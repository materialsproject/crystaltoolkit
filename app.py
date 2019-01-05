import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

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
from urllib import parse


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

struct = MPRester().get_structure_by_material_id("mp-5020")  # ("mp-123")
struct = struct.get_reduced_structure()
struct_component = mpc.StructureMoleculeComponent(struct)
search_component = mpc.SearchComponent()
editor_component = mpc.JSONComponent()


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
            f"(https://github.com/materialsproject/mash/), "
            f"powered by [The Materials Project](https://materialsproject.org) "
            f"and [pymatgen](http://pymatgen.org) v{pmg_version}."
        ),
        className="content has-text-centered",
    ),
    style={"padding": "1rem 1rem 1rem", "background-color": "inherit"},
)


favorite_button = Button(
    [Icon(kind="heart", fill="r"), html.Span("Favorite")],
    style={"margin-left": "0.2rem"},
    kind="outlined",
)
favorited_button = Button(
    [Icon(kind="heart", fill="s"), html.Span("Favorited")],
    style={"margin-left": "0.2rem"},
    kind="danger",
)
# TODO: add tooltip
favorite_button_container = html.Div(
    [
        dcc.Store(id="favorite-store"),
        html.Div([favorite_button], id="favorite-button-containier"),
    ]
)


# endregion


################################################################################
# region  DEFINE MAIN LAYOUT
################################################################################

app.layout = Container(
    [
        dcc.Location(id="url", refresh=False),
        MPComponent.all_app_stores(),
        Section(
            [
                Columns(
                    [
                        Column(
                            [struct_component.title_layout]
                            # mpc.H1("Crystal Toolkit", id="main_title")]
                        )
                    ]
                ),
                Columns(
                    [
                        Column(
                            [
                                # TODO: test responsiveness of layout on phone
                                Box(
                                    struct_component.struct_layout,
                                    style={
                                        "width": "65vmin",
                                        "height": "65vmin",
                                        "min-width": "300px",
                                        "min-height": "300px",
                                        "overflow": "hidden",
                                        "padding": "0.25rem",
                                        "margin-bottom": "0.5rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            struct_component.legend_layout,
                                            style={"float": "left"},
                                        ),
                                        html.Div(
                                            [
                                                struct_component.screenshot_layout,
                                                favorite_button_container
                                            ],
                                            style={"float": "right"},
                                        ),
                                    ],
                                    style={"width": "65vmin", "min-width": "300px"},
                                ),
                            ],
                            narrow=True,
                        ),
                        Column(
                            [
                                # search_component.standard_layout,
                                Reveal(
                                    [search_component.standard_layout],
                                    summary_title="Load Crystal or Molecule",
                                    open=True,
                                    style={"line-height": "1"},
                                ),
                                Reveal(summary_title="Display Options"),
                                Reveal(
                                    [
                                        Label("Thermodynamic Stability"),
                                        html.Div(
                                            ["1.25 eV/Atom ", html.A("above hull")]
                                        ),
                                    ],
                                    summary_title="Summary",
                                ),
                            ],
                            style={"max-width": "65vmin"},
                        ),
                    ],
                    desktop_only=True,
                    centered=True,
                ),
                Columns(
                    [
                        Column(
                            [
                                Reveal(
                                    [dt.DataTable(columns=[{"name": "Test"}])],
                                    summary_title="Literature Mentions",
                                ),
                                Reveal(summary_title="Magnetic Properties"),
                                Reveal(summary_title="Bonding and Local Environments"),
                                Reveal(summary_title="Transform Crystal"),
                                Reveal(summary_title="JSON Editor"),
                            ]
                        )
                    ]
                ),
            ]
        ),
        Section(search_component.api_hint_layout),
        Section(footer),
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


@app.callback(Output(search_component.id("input"), "value"), [Input("url", "href")])
def update_search_term_on_page_load(href):
    if href is None:
        raise PreventUpdate
    pathname = str(parse.urlparse(href).path).split("/")
    if len(pathname) == 0:
        raise PreventUpdate
    else:
        return pathname[1]


@app.callback(
    Output(search_component.id("input"), "n_submit"),
    [Input(search_component.id("input"), "value")],
    [State(search_component.id("input"), "n_submit")],
)
def perform_search_on_page_load(search_term, n_submit):
    if n_submit is None:
        return 1
    else:
        raise PreventUpdate


@app.callback(Output("url", "pathname"), [Input(search_component.id(), "data")])
def update_url_pathname_from_search_term(data):
    if data is None or "mpid" not in data:
        raise PreventUpdate
    return data["mpid"]


# endregion


################################################################################
# Run server :-)
################################################################################

if __name__ == "__main__":
    app.run_server(debug=True, port=8080)
