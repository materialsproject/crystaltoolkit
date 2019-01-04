import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import os

from flask import make_response, jsonify, request
from flask_caching import Cache

from mp_dash_components.components.core import MPComponent
from mp_dash_components.helpers.layouts import *
import mp_dash_components as mpc

from pymatgen import MPRester, Structure, Molecule
from pymatgen.analysis.graphs import StructureGraph, MoleculeGraph
from pymatgen import __version__ as pmg_version

from json import loads
from uuid import uuid4


################################################################################
# region SET UP APP
################################################################################

app = dash.Dash()
app.config["suppress_callback_exceptions"] = True
app.title = "Crystal Toolkit"
app.scripts.config.serve_locally = True
app.server.secret_key = str(uuid4())  # TODO: will need to change this one day
server = app.server

# endregion
##########


################################################################################
# region SET UP CACHE
################################################################################

try:
    cache = Cache(
        app.server,
        config={
            "CACHE_TYPE": "redis",
            "CACHE_REDIS_URL": os.environ.get("REDIS_URL", ""),
        },
    )
except Exception as exception:
    app.logger.error(
        f"Failed to connect to Redis cache, falling back to "
        f"file system cache: {exception}"
    )
    cache = Cache(app.server, config={"CACHE_TYPE": "filesystem"})

# endregion


################################################################################
# region INSTANTIATE CORE COMPONENTS
################################################################################

MPComponent.register_app(app)
MPComponent.register_cache(cache)

struct_component = mpc.StructureMoleculeComponent()
search = mpc.SearchComponent()
editor = mpc.JSONComponent()


# endregion


################################################################################
# region CREATE OTHER LAYOUT ELEMENTS
################################################################################

footer = mpc.Footer(
    html.Div(
        dcc.Markdown(
            f"In beta. Bug reports and feature requests gratefully accepted, "
            f"contact [@mkhorton](mailto:mkhorton@lbl.gov).  \n"
            f"Created by [Crystal Toolkit Development Team]"
            f"(https://github.com/materialsproject/mash/graphs/contributors), "
            f"powered by [The Materials Project](https://materialsproject.org) "
            f"and [pymatgen](http://pymatgen.org) v{pmg_version}."
        ),
        className="content has-text-centered",
    ),
    style={"padding": "1rem 1rem 1rem", "background-color": "inherit"},
)

# endregion


################################################################################
# region  DEFINE MAIN LAYOUT
################################################################################

app.layout = Container(
    [
        dcc.Location(id="url"),
        MPComponent.all_app_stores(),
        Section([html.H1("Crystal Toolkit", className="title is-1")]),
        Section(
            [
                html.Div(
                    struct_component.all_layouts["struct"],
                    style={
                        "width": "65vmin",
                        "height": "65vmin",
                        "min-width": "200px",
                        "min-height": "200px",
                        "overflow": "hidden",
                        "padding": "0.25rem",
                    },
                    className="box",
                ),
                html.Div(struct_component.all_layouts["screenshot"]),
                search.standard_layout,
            ]
        ),
        # Section(html.Details([html.Summary(html.A("Click here", className="button")), html.Div("Test!", className="box")]))
        footer,
    ]
)

# endregion


################################################################################
# region SET UP API ROUTES (to support creating viewer links)
################################################################################

@server.route("/version", methods=["GET"])
def get_version():
    return make_response(
        jsonify(
            {
                "crystal_toolkit_version": mpc.__version__,
                "crystal_toolkit_api_version": 1,
                "pymatgen_version": pmg_version,
            }
        )
    )


@server.route("/generate_token", methods=["POST"])
def get_token():
    print(str(request.json))
    token = mson_to_token(request.json, cache)
    if token["error"] is None:
        return make_response(jsonify(token), 200)
    else:
        return make_response(jsonify(token), 403)


def mson_to_token(mson, cache):

    # sanity check
    allowed_classes = [Structure, Molecule, StructureGraph, MoleculeGraph]
    allowed_mson = False
    if len(mson) > 1024 * 1024:
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
    # set to 1 week expiration by default
    cache.set(token, mson, timeout=604_800, key_prefix="crystal_toolkit_user_")
    return token


def token_to_mson(token, cache):
    return cache.get(token)

# endregion


################################################################################
# region SET UP CALLBACKS
################################################################################


# endregion


################################################################################
# Run server :-)
################################################################################

if __name__ == "__main__":
    app.run_server(debug=True, port=8080)
