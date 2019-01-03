import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from uuid import uuid4

from flask import make_response, jsonify, request

import mp_dash_components

from mp_dash_components.components.structure import StructureMoleculeComponent
from mp_dash_components.helpers.layouts import *
import mp_dash_components as mpc
from pymatgen import Structure, MPRester, Molecule
from pymatgen import __version__ as pmg_version

from json import loads

struct = Structure([[1.5, 0, 0], [0, 1.5, 0], [0, 0, 1.5]], ["N"], [[0, 0, 0]])
struct = struct * (6, 6, 6)
# struct.remove_sites([2,3,4,5,6,7,8])
##struct.replace(0, "C")
# struct.replace(1, "C")
##struct.replace(2, "C")
##struct.replace(3, "C")
struct = MPRester().get_structure_by_material_id("mp-510587")
mol = Molecule(["C", "H"], [[0, 0, 0], [1.2, 0, 0]])
#struct = mol
#struct = None

app = dash.Dash()
app.config['suppress_callback_exceptions']=True
app.title = "Crystal Toolkit"

app.scripts.config.serve_locally = True

struct_component = StructureMoleculeComponent(struct, app=app)
download_component = (mpc.Section([Icon(), struct_component.layouts["screenshot"]]),)

footer = mpc.Footer(
    html.Div(
        dcc.Markdown(
            f"In beta. Bug reports and feature requests gratefully accepted, "
            f"contact [@mkhorton](mailto:mkhorton@lbl.gov).  \n"
            f"Web app created by [Crystal Toolkit Development Team]"
            f"(https://github.com/materialsproject/mash/graphs/contributors), "
            f"powered by [The Materials Project](https://materialsproject.org) "
            f"and [pymatgen](http://pymatgen.org) v{pmg_version}."
        ),
        className="content has-text-centered",
    ),
    style={"padding": "1rem 1rem 1rem", "background-color": "inherit"},
)

app.layout = Container(
    [
        dcc.Location(id="url"),
        Section([html.H1("Crystal Toolkit", className="title is-1")]),
        Section(
            [
                html.Div(
                    struct_component.layouts["struct"],
                    style={
                        "width": "500px",
                        "height": "500px",
                        "overflow": "hidden",
                        "padding": "0.25rem",
                    },
                    className="box",
                ),
            ]
        ),
        struct_component.layouts["screenshot"],
        # Section(html.Details([html.Summary(html.A("Click here", className="button")), html.Div("Test!", className="box")]))
        footer,
        struct_component._store
    ]
)



def mson_to_token(mson, cache):

    # sanity check
    allowed_classes = [Structure, Molecule, StructureGraph, MoleculeGraph]
    allowed_mson = False
    if len(mson) > 1024*1024:
        # set a sensible size limit
        return {"token": None, "error": "Request too large."}

    mson_dict = loads(mson)
    for cls in allowed_classes:
        if not allowed_mson:
            try:
                cls.from_dict(mson_dict)
                allowed_mson = True
            except:
                pass
    if not allowed_mson:
        return {"token": None, "error": "Format not recognized."}

    token = str(uuid4())[0:6]
    cache.set(token, mson, timeout=604800, key_prefix="crystal_toolkit_user_")
    return token


def token_to_mson(token, cache):
    return cache.get(token)


app.server.secret_key = str(uuid4())
server = app.server


@server.route('/version', methods=['GET'])
def get_version():
    return make_response(jsonify({'crystal_toolkit_version': 1,
                                  'crystal_toolkit_api_version': 1,
                                  'pymatgen_version': pmg_version}))

@server.route('/generate_token', methods=['POST'])
def get_token():
    print(str(request.json))
    token = mson_to_token(request.json, cache)
    if token["error"] is None:
        return make_response(jsonify(token), 200)
    else:
        return make_response(jsonify(token), 403)


if __name__ == "__main__":
    app.run_server(debug=True, port=8082)
