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

meta_tags = [
    {
        "name": "description",
        "content": "Crystal Toolkit allows you to import, view, analyze and transform "
        "crystal structures and molecules using the full power of the Materials "
        "Project.",
    }
]

app = dash.Dash(meta_tags=meta_tags)
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

# Enable for debug purposes:
# from mp_dash_components.components.core import DummyCache
# cache = DummyCache()

# endregion


################################################################################
# region INSTANTIATE CORE COMPONENTS
################################################################################

MPComponent.register_app(app)
MPComponent.register_cache(cache)

struct = MPRester().get_structure_by_material_id(
    "mp-1078929"  # "mp-804"
)  # 19306 #"mp-5020") # ("mp-804")  # ("mp-123")


json_editor_component = mpc.JSONEditor(struct)

struct_component = mpc.StructureMoleculeComponent(struct)

search_component = mpc.SearchComponent()

favorites_component = mpc.FavoritesComponent()
favorites_component.attach_from(search_component, this_store_name="current-mpid")

literature_component = mpc.LiteratureComponent(origin_component=struct_component)
robocrys_component = mpc.RobocrysComponent(origin_component=struct_component)
magnetism_component = mpc.MagnetismComponent(origin_component=struct_component)

panels = [
    literature_component,
    robocrys_component,
    magnetism_component,
    json_editor_component,
]

api_offline = True
try:
    with MPRester() as mpr:
        api_check = mpr._make_request("/api_check")
    if not api_check.get("api_key_valid", False):
        api_error = "Materials Project API key not supplied or not valid, " \
                    "please set PMG_MAPI_KEY in your environment."
    else:
        api_offline = False
except Exception as exception:
    api_error = str(exception)
if api_offline:
    api_banner = MessageContainer(MessageHeader("Error: Cannot connect to Materials Project"), MessageBody(api_error), kind="danger")
else:
    api_banner = html.Div(id="api-banner")

# endregion


################################################################################
# region CREATE OTHER LAYOUT ELEMENTS
################################################################################


footer = mpc.Footer(
    html.Div(
        [
            html.Iframe(
                src="https://ghbtns.com/github-btn.html?user=materialsproject&repo=mash&type=star&count=true",
                style={
                    "frameborder": False,
                    "scrolling": False,
                    "width": "72px",
                    "height": "20px",
                },
            ),
            dcc.Markdown(
                f"App created by [@mkhorton](mailto:mkhorton@lbl.gov), "
                f"bug reports and feature requests gratefully accepted.  \n"
                f"Powered by [The Materials Project](https://materialsproject.org), "
                f"[pymatgen v{pmg_version}](http://pymatgen.org) and "
                f"[Dash by Plotly](https://plot.ly/products/dash/). "
                f"Deployed on [Spin](http://www.nersc.gov/users/data-analytics/spin/)."
            ),
        ],
        className="content has-text-centered",
    ),
    style={"padding": "1rem 1rem 1rem", "background-color": "inherit"},
)

panel_choices = dcc.Dropdown(
    options=[{"label": panel.title, "value": idx} for idx, panel in enumerate(panels)],
    multi=True,
    value=0,
)

panel_description = dcc.Markdown(
    [
        "Crystal Toolkit offers various *panels* which each provide different ways "
        "of analyzing, transforming or retrieving information about a material using "
        "resources and tools available to The Materials Project. Some panels "
        "retrieve data or run algorithms on demand, so please allow some time "
        "for them to run. Explore these panels below."
    ],
    className="mpc-panel-description",
)



# endregion


################################################################################
# region  DEFINE MAIN LAYOUT
################################################################################

app.layout = Container(
    [
        dcc.Location(id="url", refresh=False),
        MPComponent.all_app_stores(),
        api_banner,
        Section(
            [
                Columns(
                    [
                        Column(
                            [
                                H1(
                                    "Crystal Toolkit",
                                    id="main_title",
                                    style={"display": "inline-block"},
                                ),
                                html.Div(
                                    [favorites_component.button_layout],
                                    style={"float": "right"},
                                ),
                            ]
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
                                            [struct_component.screenshot_layout],
                                            style={"float": "right"},
                                        ),
                                    ],
                                    style={
                                        "width": "65vmin",
                                        "min-width": "300px",
                                        "margin-bottom": "40px",
                                    },
                                ),
                            ],
                            narrow=True,
                        ),
                        Column(
                            [
                                Reveal(
                                    [
                                        search_component.standard_layout,
                                        favorites_component.favorite_materials_layout,
                                    ],
                                    title="Load Crystal or Molecule",
                                    open=True,
                                    style={"line-height": "1"},
                                    id="load",
                                ),
                                Reveal(
                                    [struct_component.options_layout],
                                    title="Display Options",
                                ),
                                Reveal(
                                    [
                                        Label("Thermodynamic Stability"),
                                        html.Div(
                                            ["1.25 eV/Atom ", html.A("above hull")]
                                        ),
                                    ],
                                    title="Summary",
                                ),
                                # favorites_component.notes_layout,
                            ],
                            style={"max-width": "65vmin"},
                        ),
                    ],
                    desktop_only=False,
                    centered=False,
                ),
                Columns(
                    [
                        Column(
                            [
                                # panel_description,
                                # panel_choices,
                                html.Div(
                                    [panel.panel_layout for panel in panels],
                                    id="panels",
                                )
                            ]
                        )
                    ]
                ),
            ]
        ),
        # Section(search_component.api_hint_layout),
        Section(footer),
    ]
)

# endregion


################################################################################
# region SET UP API ROUTES (to support creating viewer links in future)
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


if os.environ.get("CRYSTAL_TOOLKIT_ENABLE_API", False):

    @server.route("/generate_token", methods=["POST"])
    def get_token():
        token = mson_to_token(request.json, cache)
        if token["error"] is None:
            return make_response(jsonify(token), 200)
        else:
            return make_response(jsonify(token), 403)


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


# @app.callback(Output("load", "open"), [Input("url", "href")])
# def open_load_box_if_no_search_from_url(href):
#    # only if open=False by default
#    if href is None:
#        raise PreventUpdate
#    if str(parse.urlparse(href).path) == '/':
#        return True
#    else:
#        raise PreventUpdate
#


@app.callback(
    Output(search_component.id("input"), "n_submit"),
    [Input(search_component.id("input"), "value")],
    [State(search_component.id("input"), "n_submit")],
)
def perform_search_on_page_load(search_term, n_submit):
    # TODO: when multiple output callbacks are supported, should also update n_submit_timestamp
    if n_submit is None:
        return 1
    else:
        raise PreventUpdate


@app.callback(Output("url", "pathname"), [Input(search_component.id(), "data")])
def update_url_pathname_from_search_term(data):
    if data is None or "mpid" not in data:
        raise PreventUpdate
    return data["mpid"]


@app.callback(
    Output(struct_component.id(), "data"), [Input(search_component.id(), "data")]
)
def update_structure(search_mpid):

    if search_mpid is None or "mpid" not in search_mpid:
        raise PreventUpdate

    with MPRester() as mpr:
        struct = mpr.get_structure_by_material_id(search_mpid["mpid"])

    return MPComponent.to_data(struct)


@app.callback(
    Output("main_title", "children"), [Input(struct_component.id("title"), "children")]
)
def update_title(title):
    print("title", title)
    if not title:
        raise PreventUpdate
    return title


# endregion


################################################################################
# Run server :-)
################################################################################

DEBUG_MODE = os.environ.get("CRYSTAL_TOOLKIT_DEBUG_MODE", False)

if __name__ == "__main__":
    app.run_server(debug=DEBUG_MODE, port=8080)
