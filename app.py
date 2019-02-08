import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import os
import logging

from flask import make_response, jsonify, request
from flask_caching import Cache

from crystal_toolkit.components.core import MPComponent
from crystal_toolkit.helpers.layouts import *
import crystal_toolkit as ct

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

app = dash.Dash(__name__, meta_tags=meta_tags)
app.config["suppress_callback_exceptions"] = True
app.title = "Crystal Toolkit"
app.scripts.config.serve_locally = True

app.server.secret_key = str(uuid4())  # TODO: will need to change this one day
server = app.server

DEBUG_MODE = os.environ.get("CRYSTAL_TOOLKIT_DEBUG_MODE", False)

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
if DEBUG_MODE:
    from crystal_toolkit.components.core import DummyCache
    cache = DummyCache()

# endregion


################################################################################
# region SET UP LOGGING
################################################################################

logger = logging.getLogger(app.title)

# endregion


################################################################################
# region INSTANTIATE CORE COMPONENTS
################################################################################

ct.register_app(app)
ct.register_cache(cache)

json_editor_component = ct.JSONEditor()

struct_component = ct.StructureMoleculeComponent(origin_component=json_editor_component)

search_component = ct.SearchComponent()
upload_component = ct.StructureMoleculeUploadComponent()

favorites_component = ct.FavoritesComponent()
favorites_component.attach_from(search_component, this_store_name="current-mpid")

literature_component = ct.LiteratureComponent(origin_component=struct_component)
robocrys_component = ct.RobocrysComponent(origin_component=struct_component)
magnetism_component = ct.MagnetismComponent(origin_component=struct_component)
xrd_component = ct.XRayDiffractionPanelComponent(origin_component=struct_component)

bonding_graph_component = ct.BondingGraphComponent()
bonding_graph_component.attach_from(struct_component, origin_store_name="graph")
bonding_graph_component.attach_from(struct_component, this_store_name="display_options", origin_store_name="display_options")


supercell = ct.SupercellTransformationComponent()
grain_boundary = ct.GrainBoundaryTransformationComponent()
oxi_state = ct.AutoOxiStateDecorationTransformationComponent()

transformation_component = ct.AllTransformationsComponent(transformations=[supercell, grain_boundary, oxi_state],
                                                          origin_component=struct_component)

panels = [
    bonding_graph_component,
    literature_component,
    magnetism_component,
    transformation_component,
    json_editor_component,
]

# panels not ready for production yet (e.g. pending papers, further testing, etc.)
if DEBUG_MODE:
    panels.insert(-1, robocrys_component)
    panels.insert(-1, xrd_component)


banner = html.Div(id="banner")
if DEBUG_MODE:
    banner = html.Div(
        [
            html.Br(),
            MessageContainer(
                [
                    MessageHeader("Warning"),
                    MessageBody(
                        dcc.Markdown(
                            "This is a pre-release version of Crystal Toolkit and "
                            "may not behave reliably. Please visit "
                            "[https://viewer.materialsproject.org](https://viewer.materialsproject.org) "
                            "for a stable version.")
                    ),
                ],
                kind="warning",
            ),
        ],
        id="banner",
    )

api_offline, api_error = True, "Unknown error connecting to Materials Project API."
try:
    with MPRester() as mpr:
        api_check = mpr._make_request("/api_check")
    if not api_check.get("api_key_valid", False):
        api_error = (
            "Materials Project API key not supplied or not valid, "
            "please set PMG_MAPI_KEY in your environment."
        )
    else:
        api_offline = False
except Exception as exception:
    api_error = str(exception)
if api_offline:
    banner = html.Div(
        [
            html.Br(),
            MessageContainer(
                [
                    MessageHeader("Error: Cannot connect to Materials Project"),
                    MessageBody(api_error),
                ],
                kind="danger",
            ),
        ],
        id="banner",
    )


# endregion


################################################################################
# region CREATE OTHER LAYOUT ELEMENTS
################################################################################


footer = ct.Footer(
    html.Div(
        [
            # html.Iframe(
            #    src="https://ghbtns.com/github-btn.html?user=materialsproject&repo=crystaltoolkit&type=star&count=true",
            #    style={
            #        "frameborder": False,
            #        "scrolling": False,
            #        "width": "72px",
            #        "height": "20px",
            #    },
            # ),
            # html.Br(), Button([Icon(kind="cog", fill="r"), html.Span("Customize")], kind="light", size='small'),
            dcc.Markdown(
                f"App created by [@mkhorton](mailto:mkhorton@lbl.gov) and [@mattmcdermott](https://github.com/mattmcdermott), "
                f"bug reports and feature requests gratefully accepted.  \n"
                f"Powered by [The Materials Project](https://materialsproject.org), "
                f"[pymatgen v{pmg_version}](http://pymatgen.org) and "
                f"[Dash by Plotly](https://plot.ly/products/dash/). "
                f"Deployed on [Spin](http://www.nersc.gov/users/data-analytics/spin/)."
            )
        ],
        className="content has-text-centered",
    ),
    style={"padding": "1rem 1rem 1rem", "background-color": "inherit"},
)

panel_choices = dcc.Dropdown(
    options=[{"label": panel.title, "value": idx} for idx, panel in enumerate(panels)],
    multi=True,
    value=[idx for idx in range(len(panels))],
    id="panel-choices",
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

master_layout = Container(
    [
        dcc.Location(id="url", refresh=False),
        MPComponent.all_app_stores(),
        # dcc.Store(storage_type="session", id="session_store"),
        banner,
        Section(
            [
                Columns(
                    [
                        Column(
                            [
                                struct_component.title_layout,
                                html.Div(
                                    # [favorites_component.button_layout],
                                    style={"float": "right"}
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
                                        upload_component.standard_layout,
                                        # favorites_component.favorite_materials_layout,
                                    ],
                                    title="Load Crystal or Molecule",
                                    open=True,
                                    style={"line-height": "1"},
                                    id="load",
                                ),
                                Reveal(
                                    [struct_component.options_layout],
                                    title="Display Options",
                                    id="display-options",
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

app.layout = master_layout


# endregion


################################################################################
# region SET UP API ROUTES (to support creating viewer links in future)
################################################################################


@server.route("/version", methods=["GET"])
def get_version():
    return make_response(
        jsonify(
            {
                "crystal_toolkit_version": ct.__version__,
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
    Output(json_editor_component.id(), "data"), [Input(search_component.id(), "data"),
                                                 Input(upload_component.id(), "data")]
)
def master_update_structure(search_mpid, upload_data):

    if not search_mpid and not upload_data:
        raise PreventUpdate

    search_mpid = search_mpid or {}
    upload_data = upload_data or {}

    time_searched = search_mpid.get('time_requested', -1)
    time_uploaded = upload_data.get('time_requested', -1)

    if time_searched > time_uploaded:

        if search_mpid is None or "mpid" not in search_mpid:
            raise PreventUpdate

        with MPRester() as mpr:
            struct = mpr.get_structure_by_material_id(search_mpid["mpid"])

    else:

        struct = MPComponent.from_data(upload_data['data'])

    return MPComponent.to_data(struct.as_dict(verboisty=0))


# endregion


################################################################################
# region HANDLE PERSISTENT SETTINGS
################################################################################

# to_save_and_restore = [
#    # (struct_component.id("hide-show"), "values"),
#    (struct_component.id("color-scheme"), "value"),
#    # (struct_component.id("radius_strategy"), "value"),
#    # (struct_component.id("draw_options"), "values"),
#    # (struct_component.id("unit-cell-choice"), "value"),
#    # (struct_component.id("repeats"), "value"),
# ]
#
## ("display-options", "open")]
#
# for (component_id, component_property) in to_save_and_restore:
#
#    @app.callback(
#        Output(component_id, component_property),
#        [Input("session_store", "modified_timestamp")],
#        [State("session_store", "data")],
#    )
#    def load_data(modified_timestamp, saved_data):
#        key = f"{component_id}_{component_property}"
#        print("Saving: ", key)
#        print("Saved session data: ", saved_data)
#        if not saved_data or key not in saved_data:
#            raise PreventUpdate
#        return saved_data[key]
#
#
# all_inputs = [
#    Input(component_id, component_property)
#    for component_id, component_property in to_save_and_restore
# ]
# all_keys = [
#    f"{component_id}_{component_property}"
#    for component_id, component_property in to_save_and_restore
# ]
#
#
# @app.callback(
#    Output("session_store", "data"), all_inputs, [State("session_store", "data")]
# )
# def load_data(property, saved_data):
#    key = f"{component_id}_{component_property}"
#    print("Saving: ", key)
#    saved_data = saved_data or {}
#    saved_data[key] = property
#    print("Saved session data: ", saved_data)
#    return saved_data

# for idx, panel in enumerate(panels):
#    @app.callback(
#        Output(panel.id("panel"), "style"),
#        [Input("panel-choices", "value")]
#    )
#    def hide_show_panel(value):
#        if idx in value:
#            return {}
#        else:
#            return {"display": "none"}

# endregion

################################################################################
# Run server :-)
################################################################################


if __name__ == "__main__":
    app.run_server(debug=DEBUG_MODE, port=8050)
