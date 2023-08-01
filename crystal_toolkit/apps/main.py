from __future__ import annotations

import logging
import os
import warnings
from random import choice
from time import time
from typing import TYPE_CHECKING, Any
from urllib import parse
from uuid import uuid4

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask_caching import Cache
from monty.serialization import loadfn
from pymatgen.core import Structure
from pymatgen.core import __version__ as pmg_version
from pymatgen.ext.matproj import MPRester, MPRestError

import crystal_toolkit.components as ctc
from crystal_toolkit import __file__ as module_path
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import (
    Box,
    Column,
    Columns,
    Container,
    Loading,
    MessageBody,
    MessageContainer,
    MessageHeader,
    Reveal,
)
from crystal_toolkit.settings import SETTINGS

if TYPE_CHECKING:
    from crystal_toolkit.core.panelcomponent import PanelComponent

# choose a default structure on load
path = os.path.join(os.path.dirname(module_path), "apps/assets/task_ids_on_load.json")
DEFAULT_MPIDS = loadfn(path)

################################################################################
# region SET UP APP
################################################################################

meta_tags = [  # TODO: add og-image, etc., title
    {
        "name": "description",
        "content": "Crystal Toolkit allows you to import, view, analyze and transform "
        "crystal structures and molecules using the full power of the Materials "
        "Project.",
    }
]

print("SETTINGS")
for setting, value in SETTINGS:
    print(f"{setting}: {value}")

if not SETTINGS.ASSETS_PATH:
    warnings.warn(
        "Set CRYSTAL_TOOLKIT_ASSETS environment variable or app will be unstyled."
    )

external_scripts = []
if not SETTINGS.DEBUG_MODE:
    # MathJax support
    external_scripts.append(
        "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML"
    )

app = dash.Dash(
    __name__,
    meta_tags=meta_tags,
    assets_folder=SETTINGS.ASSETS_PATH,
    external_scripts=external_scripts,
    prevent_initial_callbacks=False,
    title="Crystal Toolkit",
    update_title=None,
)
app.scripts.config.serve_locally = True

# Materials Project embed mode
if not SETTINGS.MP_EMBED_MODE:
    app.config["assets_ignore"] = r".*\.mpembed\..*"
    box_size = "65vmin"
else:
    # reduce zoom level and box size due to iframe on materialsproject.org
    ctc.StructureMoleculeComponent.default_scene_settings["defaultZoom"] = 0.5
    box_size = "50vmin"


app.server.secret_key = str(uuid4())
server = app.server

# endregion
###########


################################################################################
# region SET UP CACHE
################################################################################

if SETTINGS.DEBUG_MODE:
    # disable cache in debug
    cache = Cache(app.server, config={"CACHE_TYPE": "null"})
else:
    cache = Cache(
        app.server,
        config={
            "CACHE_TYPE": "redis",
            "CACHE_REDIS_URL": os.getenv("REDIS_URL", SETTINGS.REDIS_URL),
        },
    )

# endregion


################################################################################
# region SET UP LOGGING
################################################################################

logger = logging.getLogger(app.title)

# endregion


################################################################################
# region INSTANTIATE CORE COMPONENTS
################################################################################

search_component = ctc.SearchComponent()
upload_component = ctc.StructureMoleculeUploadComponent()


transformation_component = ctc.AllTransformationsComponent(
    transformations=[
        "SupercellTransformationComponent",
        "AutoOxiStateDecorationTransformationComponent",
        "CubicSupercellTransformationComponent",
        "GrainBoundaryTransformationComponent",
        "MonteCarloRattleTransformationComponent",
        "SlabTransformationComponent",
        "SubstitutionTransformationComponent",
    ]
)

struct_component = ctc.StructureMoleculeComponent(
    links={"default": transformation_component.id()}
)

robocrys_panel = ctc.RobocrysComponent(links={"default": transformation_component.id()})
xrd_panel = ctc.DiffractionPanelComponent(
    links={"default": transformation_component.id()}
)
# pbx_component = ctc.PourbaixDiagramPanelComponent(origin_component=struct_component)

symmetry_panel = ctc.SymmetryPanel(links={"default": struct_component.id()})
localenv_panel = ctc.LocalEnvironmentPanel(
    links={
        "default": struct_component.id(),
        "graph": struct_component.id("graph"),
        "display_options": struct_component.id("display_options"),
    }
)

if SETTINGS.MP_EMBED_MODE:
    action_div = html.Div([])
    # submit_snl_panel = ctc.SubmitSNLPanel(origin_component=struct_component)
    # action_div = html.Div(
    #     [submit_snl_panel.panel_layout, download_component.panel_layout]
    # )
else:
    action_div = html.Div([struct_component.download_layout()])

panels = [symmetry_panel, localenv_panel, xrd_panel, robocrys_panel]


if SETTINGS.MP_EMBED_MODE:
    mp_section: tuple[Any, ...] = (html.Div(),)
else:
    # bsdos_component = ctc.BandstructureAndDosPanelComponent(
    #     origin_component=search_component
    # )
    # # grain_boundary_panel = ctc.GrainBoundaryPanel(origin_component=search_component)
    # xas_component = ctc.XASPanelComponent(origin_component=search_component)
    # pd_component = ctc.PhaseDiagramPanelComponent(origin_component=struct_component)
    # literature_component = ctc.LiteratureComponent(origin_component=struct_component)
    #
    # mp_panels = [
    #     pd_component,
    #     pbx_component,
    #     magnetism_component,
    #     xas_component,
    #     bsdos_component,
    #     # grain_boundary_panel,
    #     literature_component,
    # ]

    mp_panels: list[PanelComponent] = []

    mp_section = (
        html.H3("Materials Project"),
        html.Div([panel.panel_layout() for panel in mp_panels], id="mp_panels"),
    )


body_layout = [
    html.Br(),
    html.H3("Transform"),
    html.Div([transformation_component.layout()]),
    html.Br(),
    html.H3("Analyze"),
    html.Div([panel.panel_layout() for panel in panels], id="panels"),
    # html.Br(),
    # *mp_section,
]

banner = html.Div(id="banner")
if SETTINGS.DEBUG_MODE:
    banner = html.Div(
        [
            html.Br(),
            MessageContainer(
                [
                    MessageHeader("Warning"),
                    MessageBody(
                        dcc.Markdown(
                            "The app is running in debug mode so will be slower than usual and error "
                            "messages may appear."
                        )
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


footer = html.Footer(
    html.Div(
        [
            dcc.Markdown(
                f"""
                App created by [Crystal Toolkit Development Team][contributors].\nBug reports and feature
                requests gratefully accepted, please send them to [@mkhorton](mailto:mkhorton@lbl.gov).\n
                Powered by [The Materials Project](https://materialsproject.org),
                [pymatgen v{pmg_version}](http://pymatgen.org) and
                [Dash by Plotly](https://plot.ly/products/dash/).
                Deployed on [Spin](http://www.nersc.gov/users/data-analytics/spin/).

                [contributors]: https://github.com/materialsproject/crystaltoolkit/graphs/contributors
                """
            )
        ],
        className="content has-text-centered",
    ),
    style={"padding": "1rem 1rem 1rem", "background-color": "inherit"},
)

panel_choices = dcc.Dropdown(
    options=[{"label": panel.title, "value": idx} for idx, panel in enumerate(panels)],
    multi=True,
    value=list(range(len(panels))),
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
        banner,
        html.Section(
            [
                Columns(
                    [
                        Column(
                            [
                                struct_component.title_layout(),
                                html.Div(style={"float": "right"}),
                            ]
                        )
                    ]
                ),
                Columns(
                    [
                        Column(
                            [
                                # TODO: test responsiveness of layout on phone
                                Loading(
                                    Box(
                                        struct_component.layout(size="100%"),
                                        style={
                                            "width": box_size,
                                            "height": box_size,
                                            "minWidth": "300px",
                                            "minHeight": "300px",
                                            "maxWidth": "600px",
                                            "maxHeight": "600px",
                                            "overflow": "hidden",
                                            "padding": "0.25rem",
                                            "marginBottom": "0.5rem",
                                        },
                                    )
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            struct_component._sub_layouts["legend"],
                                            style={"float": "left"},
                                        ),
                                        html.Div(
                                            [struct_component.screenshot_layout()],
                                            style={"float": "right"},
                                        ),
                                    ],
                                    style={
                                        "width": box_size,
                                        "minWidth": "300px",
                                        "marginBottom": "40px",
                                    },
                                ),
                            ],
                            narrow=True,
                        ),
                        Column(
                            [
                                Reveal(
                                    [
                                        search_component.layout(),
                                        upload_component.layout(),
                                    ],
                                    title="Load Crystal",
                                    open=True,
                                    style={"lineHeight": "1"},
                                    id="load",
                                ),
                                Reveal(
                                    [struct_component._sub_layouts["options"]],
                                    title="Display Options",
                                    id="display-options",
                                ),
                                action_div,
                            ],
                            style={"width": box_size, "maxWidth": box_size},
                        ),
                    ],
                    desktop_only=False,
                    centered=False,
                ),
                Columns([Column(body_layout)]),
            ]
        ),
        html.Section(footer),
    ]
)

ctc.register_crystal_toolkit(layout=master_layout, app=app, cache=cache)

# endregion


################################################################################
# region SET UP APP-SPECIFIC CALLBACKS
################################################################################


@app.callback(Output(search_component.id("input"), "value"), Input("url", "href"))
def update_search_term_on_page_load(href: str) -> str:
    """If an MP ID is provided in the url, load that MP ID. Otherwise load a random MP ID from the
    DEFAULT_MPIDS global variable.

    Args:
        href: e.g. "http://localhost:8050/mp-11358"

    Returns: an MP ID
    """
    if href is None:
        raise PreventUpdate
    pathname = str(parse.urlparse(href).path).split("/")
    if len(pathname) <= 1:
        raise PreventUpdate
    if not pathname[1]:
        return choice(DEFAULT_MPIDS)
    return pathname[1].replace("+", " ")


@app.callback(
    Output(search_component.id("input"), "n_submit"),
    Output(search_component.id("input"), "n_submit_timestamp"),
    Input(search_component.id("input"), "value"),
    State(search_component.id("input"), "n_submit"),
)
def perform_search_on_page_load(
    search_term: str, n_submit: int | None
) -> tuple[int, int]:
    """Loading with an MP ID in the URL requires populating the search term with the MP ID, this
    callback forces that search to then take place by force updating n_submit and n_submit_timestamp
    props.

    Args:
        search_term: e.g. mp-11358
        n_submit:

    Returns: (1, time in ms since 1970)
    """
    # TODO: could be a client side callback
    if n_submit is None:
        return 1, int(round(time() * 1000))
    raise PreventUpdate


@app.callback(Output("url", "pathname"), Input(search_component.id(), "data"))
def update_url_pathname_from_search_term(mpid: str | None) -> str:
    """Updates the URL from the search term. Technically a circular callback, this is done to
    prevent the app seeming inconsistent from the end user.

    Args:
        mpid: mpid

    Returns: mpid
    """
    # TODO: could be a client side callback
    if mpid is None:
        raise PreventUpdate
    return mpid


@app.callback(
    Output(transformation_component.id("input_structure"), "data"),
    Input(search_component.id(), "data"),
    Input(upload_component.id(), "data"),
)
def master_update_structure(
    search_mpid: str | None, upload_data: dict | None
) -> Structure:
    """A new structure is loaded either from the search component or from the upload component. This
    callback triggers the update, and uses the callback context to determine which should take
    precedence if there is both a search term and uploaded data present.

    Args:
        search_mpid: e.g. "mp-11358"
        upload_data: output of upload component, {"data": ..., "error" ...}

    Returns: an encoded Structure
    """
    if not search_mpid and not upload_data:
        raise PreventUpdate

    if not dash.callback_context.triggered:
        raise PreventUpdate

    if (
        len(dash.callback_context.triggered) > 1
        or dash.callback_context.triggered[0]["prop_id"]
        == f"{search_component.id()}.data"
    ):
        # triggered by both on initial load
        load_by = "mpid"
    else:
        load_by = "uploaded"

    upload_data = upload_data or {}

    if load_by == "mpid":
        if search_mpid is None:
            raise PreventUpdate

        with MPRester() as mpr:
            # TODO: add comprehensive fix to this in pymatgen
            try:
                struct = mpr.get_task_data(search_mpid, "structure")[0]["structure"]
                print("Struct from task.")
            except MPRestError:
                struct = mpr.get_structure_by_material_id(search_mpid)
                print("Struct from material.")
    else:
        struct = MPComponent.from_data(upload_data["data"])

    return struct


# endregion

################################################################################
# Run server :-)
################################################################################


if __name__ == "__main__":
    app.run(debug=SETTINGS.DEBUG_MODE, port=8051)
