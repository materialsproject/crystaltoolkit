from __future__ import annotations

import logging
import re

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Component, Input, Output, State
from dash.exceptions import PreventUpdate
from frozendict import frozendict
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.pourbaix_diagram import PREFAC, PourbaixDiagram
from pymatgen.core import Composition, Element
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.util.string import unicodeify
from shapely.geometry import Polygon

import crystal_toolkit.helpers.layouts as ctl
from crystal_toolkit.core.mpcomponent import MPComponent

try:
    from pymatgen.analysis.pourbaix_diagram import ELEMENTS_HO
except ImportError:
    ELEMENTS_HO = {Element("H"), Element("O")}


logger = logging.getLogger(__name__)
__author__ = "Joseph Montoya"
__email__ = "joseph.montoya@tri.global"


# TODO: fix bug for Pa, etc.
# TODO: fix bug with composition input, needs further investigation and testing
# TODO: add water stability region

HEIGHT = 550  # in px
WIDTH = 700  # in px
MIN_CONCENTRATION = 1e-6
MAX_CONCENTRATION = 5
MIN_PH = -2
MAX_PH = 16
MIN_V = -4
MAX_V = 4


class PourbaixDiagramComponent(MPComponent):
    default_state = frozendict(filter_solids=True, show_heatmap=False)

    default_plot_style = frozendict(
        xaxis={
            "title": "pH",
            "anchor": "y",
            "mirror": "ticks",
            "showgrid": False,
            "showline": True,
            "side": "bottom",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"color": "#000000", "size": 24.0},
            "type": "linear",
            "zeroline": False,
            "range": [MIN_PH, MAX_PH],
        },
        yaxis={
            "title": "Applied Potential (V vs. SHE)",
            "anchor": "x",
            "mirror": "ticks",
            "range": [MIN_V, MAX_V],
            "showgrid": False,
            "showline": True,
            "side": "left",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"color": "#000000", "size": 24.0},
            "type": "linear",
            "zeroline": False,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=HEIGHT,
        width=WIDTH,
        hovermode="closest",
        showlegend=True,
        legend=dict(
            orientation="h",
            traceorder="reversed",
            x=1.0,
            y=1.08,
            xanchor="right",
            tracegroupgap=5,
        ),
        margin=dict(l=80, b=70, t=10, r=20),
    )

    empty_plot_style = frozendict(
        xaxis={"visible": False},
        yaxis={"visible": False},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    colorscale_classic = (
        [0.00, "#4728fa"],  # blue
        [0.33, "#f9f273"],  # yellow
        [0.66, "#e5211b"],  # red
        [1.00, "#ffffff"],  # white
    )

    colorscale = "magma"

    default_table_params = (
        {"col": "Material ID", "edit": False},
        {"col": "Formula", "edit": True},
        {"col": "Formation Energy (eV/atom)", "edit": True},
        {"col": "Energy Above Hull (eV/atom)", "edit": False},
        {"col": "Predicted Stable?", "edit": False},
    )

    empty_row = frozendict(
        {
            "Material ID": None,
            "Formula": "INSERT",
            "Formation Energy (eV/atom)": "INSERT",
            "Energy Above Hull (eV/atom)": None,
            "Predicted Stable": None,
        }
    )

    @staticmethod
    def get_figure(
        pourbaix_diagram: PourbaixDiagram, heatmap_entry=None, show_water_lines=True
    ) -> go.Figure:
        """Static method for getting plotly figure from a Pourbaix diagram.

        Args:
            pourbaix_diagram (PourbaixDiagram): Pourbaix diagram to plot
            heatmap_entry (PourbaixEntry): id for the heatmap generation
            show_water_lines (bool): if True, show region of water stability

        Returns:
            (dict) figure layout
        """
        data = []

        shapes = []
        xy_data = []
        labels = []
        domain_heights = []

        include_legend = set()

        for entry, vertices in pourbaix_diagram._stable_domain_vertices.items():
            formula = entry.name
            clean_formula = PourbaixDiagramComponent.clean_formula(formula)

            # Generate information for textual labels
            domain = Polygon(vertices)
            centroid = domain.centroid
            height = domain.bounds[3] - domain.bounds[1]

            # Ensure label is within plot area
            # TODO: remove hard-coded value here and make sure it's set dynamically
            xy_data.append([centroid.x, centroid.y])
            labels.append(clean_formula)
            domain_heights.append(height)

            # Assumes that entry.phase_type is either "Solid" or "Ion" or
            # a list of "Solid" and "Ion"
            if isinstance(entry.phase_type, str):
                legend_entry = entry.phase_type
            elif isinstance(entry.phase_type, list):
                if len(set(entry.phase_type)) == 1:
                    legend_entry = (
                        "Mixed Ion" if entry.phase_type[0] == "Ion" else "Mixed Solid"
                    )
                else:
                    legend_entry = "Mixed Ion/Solid"
            else:
                # Should never get here
                print(f"Debug required in Pourbaix for {entry.phase_type}")
                legend_entry = "Unknown"

            if not heatmap_entry:
                if legend_entry == "Ion" or legend_entry == "Unknown":
                    fillcolor = "rgb(255,245,255,1)"  # New purple white color
                elif legend_entry == "Mixed Ion":
                    fillcolor = "rgb(255,255,240,1)"
                elif legend_entry == "Solid":
                    fillcolor = "rgba(188,236,237,1)"  # same color as old website
                elif legend_entry == "Mixed Solid":
                    fillcolor = "rgba(155,229,232,1)"
                elif legend_entry == "Mixed Ion/Solid":
                    fillcolor = "rgb(95,238,222,1)"
            else:
                fillcolor = "rgba(0,0,0,0)"

            data.append(
                go.Scatter(
                    x=[v[0] for v in vertices],
                    y=[v[1] for v in vertices],
                    fill="toself",
                    fillcolor=fillcolor,
                    legendgroup=legend_entry,
                    # legendgrouptitle={"text": legend_entry},
                    name=legend_entry,
                    text=f"{clean_formula} ({entry.entry_id})",
                    hoverinfo="text",
                    marker={"color": "Black"},
                    line={"color": "Black", "width": 0},
                    mode="lines",
                    showlegend=legend_entry not in include_legend,
                )
            )

            include_legend.add(legend_entry)

            # Add lines separately so they show up on heatmap

            # Info on SVG paths: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths
            # Move to first point
            path = "M {},{}".format(*vertices[0])
            # Draw lines to each other point
            path += "".join("L {},{}".format(*vertex) for vertex in vertices[1:])
            # Close path
            path += "Z"

            # stable entries are black with default color scheme,
            # so use off-white lines instead
            line = (
                {"color": "rgba(255,235,255,1)", "width": 4}
                if heatmap_entry
                else {"color": "Black", "width": 1}
            )

            shape = go.layout.Shape(
                type="path", path=path, fillcolor="rgba(0,0,0,0)", opacity=1, line=line
            )
            shapes.append(shape)

        layout = {**PourbaixDiagramComponent.default_plot_style}
        layout.update({"shapes": shapes})

        if heatmap_entry is None:
            x, y = zip(*xy_data)
            data.append(
                go.Scatter(
                    x=x, y=y, text=labels, hoverinfo="text", mode="text", name="Labels"
                )
            )
            layout.update({"annotations": []})
        # else:
        # Add annotations to layout to make text more readable when displaying heatmaps

        # TODO: this doesn't work yet; resolve or scrap
        # cmap = get_cmap(PourbaixDiagramComponent.colorscale)
        # def get_text_color(x, y):
        #     """
        #     Set text color based on whether background at that point is dark or light.
        #     """
        #     energy = pourbaix_diagram.get_decomposition_energy(entry, pH=x, V=y)
        #     c = [int(c * 255) for c in cmap(energy)[0:3]]
        #     # borrowed from crystal_toolkit.components.structure
        #     # TODO: move to utility function and ensure correct attribution for magic numbers
        #     if 1 - (c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114) / 255 < 0.5:
        #         font_color = "#000000"
        #     else:
        #         font_color = "#ffffff"
        #     #print(energy, c, font_color)
        #     return font_color

        # def get_text_size(available_vertical_space):
        #     """Set text size based on available vertical space."""
        #     return min(max(6 * available_vertical_space, 12), 20)

        # annotations = [
        #     {
        #         "align": "center",
        #         "bgcolor": "white",
        #         "font": {"color": "black", "size": get_text_size(height)},
        #         "opacity": 1,
        #         "showarrow": False,
        #         "text": label,
        #         "x": x,
        #         "xanchor": "center",
        #         "yanchor": "auto",
        #         # "xshift": -10,
        #         # "yshift": -10,
        #         "xref": "x",
        #         "y": y,
        #         "yref": "y",
        #     }
        #     for (x, y), label, height in zip(xy_data, labels, domain_heights)
        # ]
        # layout.update({"annotations": annotations}) # shouldn't have annotation when heatmap_entry presents

        # Get data for heatmap
        if heatmap_entry is not None:
            ph_range = np.arange(MIN_PH, MAX_PH + 0.001, 0.1)
            v_range = np.arange(MIN_V, MAX_V + 0.001, 0.1)
            ph_mesh, v_mesh = np.meshgrid(ph_range, v_range)
            decomposition_e = pourbaix_diagram.get_decomposition_energy(
                heatmap_entry, ph_mesh, v_mesh
            )

            # Generate hoverinfo
            hoverlabel = []
            for ph_val, v_val, de_val in zip(
                ph_mesh.ravel(), v_mesh.ravel(), decomposition_e.ravel()
            ):
                hovertext = [
                    f"∆G<sub>pbx</sub>={de_val:.2f}",
                    f"ph={ph_val:.2f}",
                    f"V={v_val:.2f}",
                ]
                hovertext = "<br>".join(hovertext)
                hoverlabel.append(hovertext)
            hoverlabel = np.reshape(hoverlabel, list(decomposition_e.shape))

            # Enforce decomposition limit energy
            # decomposition_e = np.min(
            #     [decomposition_e, np.ones(decomposition_e.shape)], axis=0
            # )

            heatmap_formula = unicodeify(
                Composition(heatmap_entry.composition).reduced_formula
            )

            h_map = go.Contour(
                z=decomposition_e,
                x=list(ph_range),
                y=list(v_range),
                colorbar={
                    "title": "∆G<sub>pbx</sub> (eV/atom)",
                    "titleside": "right",
                },
                colorscale=[
                    [0, "#000004"],
                    [0.031, "#180f3d"],
                    [0.044, "#440f76"],
                    [0.063, "#721f81"],
                    [0.088, "#9e2f7f"],
                    [0.125, "#cd4071"],
                    [0.177, "#f1605d"],
                    [0.25, "#fd9668"],
                    [0.354, "#feca8d"],
                    [0.5, "#fcfdbf"],
                    [1, "#fcfdbf"],
                ],  # Custom Magma built exponentially rather than linearly
                ncontours=50,
                connectgaps=True,
                line_smoothing=0,
                line_width=0,
                # contours_coloring="heatmap",
                text=hoverlabel,
                hoverinfo="text",
                name=f"{heatmap_formula} ({heatmap_entry.entry_id}) Heatmap",
                showlegend=True,
                contours=dict(
                    start=0,
                    end=1,
                ),
            )
            data.append(h_map)

        if show_water_lines:
            ph_range = [MIN_PH, MAX_PH]
            # hydrogen line
            data.append(
                go.Scatter(
                    x=[ph_range[0], ph_range[1]],
                    y=[-ph_range[0] * PREFAC, -ph_range[1] * PREFAC],
                    mode="lines",
                    line={"color": "orange", "dash": "dash"},
                    name="Hydrogen Stability Line",
                )
            )
            # oxygen line
            data.append(
                go.Scatter(
                    x=[ph_range[0], ph_range[1]],
                    y=[-ph_range[0] * PREFAC + 1.23, -ph_range[1] * PREFAC + 1.23],
                    mode="lines",
                    line={"color": "orange", "dash": "dash"},
                    name="Oxygen Stability Line",
                )
            )

            #     h_line = np.transpose([[xlim[0], -xlim[0] * PREFAC], [xlim[1], -xlim[1] * PREFAC]])
            #     o_line = np.transpose([[xlim[0], -xlim[0] * PREFAC + 1.23], [xlim[1], -xlim[1] * PREFAC + 1.23]])
            # #   SHE line
            # #   data.append(go.Scatter(
            # #
            # #   ))

        return go.Figure(data=data, layout=layout)

    # TODO: format formula
    @staticmethod
    def clean_formula(formula):
        # Superscript charges
        clean_formula = re.sub(r"\[([0-9+-]+)\]", r"<sup>\1</sup>", formula)

        # Subscript coefficients
        return re.sub(r"([A-Za-z\(\)])([\d\.]+)", r"\1<sub>\2</sub>", clean_formula)

    def get_figure_div(self, figure=None):
        """
        Intentionally update the graph by wrapping it in an `html.Div` instead of directly modifying `go.Figure` or `dcc.Graph`.
        This is because, after resetting the axes (e.g., zooming in/out), the updated axes may not match the original ones.
        This behavior appears to be a long-standing issue in Dash.

        Reference:
        https://community.plotly.com/t/dash-reset-axes-range-not-updating-if-ranges-specified-in-layout/25839/3
        """
        if figure is None:
            figure = go.Figure(layout={**PourbaixDiagramComponent.empty_plot_style})

        return html.Div(
            [
                html.H5(
                    "💡 Zoom in by selecting an area of interest, and double-click to return to the original view.",
                    style={"textAlign": "right"},
                ),
                dcc.Graph(
                    figure=figure,
                    responsive=True,
                    config={"displayModeBar": False, "displaylogo": False},
                ),
            ]
        )

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        options = html.Div(
            [
                self.get_bool_input(
                    "filter_solids",
                    # state=self.default_state,
                    default=self.default_state["filter_solids"],
                    label="Filter Solids",
                    help_str="Whether to filter solid phases by stability on the compositional phase diagram. "
                    "The practical consequence of this is that highly oxidized or reduced phases that "
                    "might show up in experiments due to kinetic limitations on oxygen/hydrogen evolution "
                    "won't appear in the diagram, but they are not actually “stable” (and are frequently "
                    "overstabilized from DFT errors). Hence, including only the stable solid phases generally "
                    "leads to the most accurate Pourbaix diagrams.",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.ConfirmDialog(
                                    id=self.id("invalid-comp-alarm"),
                                    message="Illegal composition entry!",
                                ),
                                html.H5(
                                    "Composition",
                                    id=self.id("composition-title"),
                                    style={"fontWeight": "bold"},
                                ),
                                dcc.Input(
                                    id=self.id("comp-text"),
                                    type="text",
                                    # placeholder="composition e.g. 1:1:1",
                                ),
                                html.Button(
                                    "Update",
                                    id=self.id("comp-btn"),
                                ),
                                ctl.Block(html.Div(id=self.id("display-composition"))),
                                html.Br(),
                                html.Br(),
                                dcc.Store(id=self.id("elements-store")),
                            ],
                            id=self.id("comp-panel"),
                            style={"display": "none"},
                        ),
                        html.Div(
                            [
                                dcc.ConfirmDialog(
                                    id=self.id("invalid-conc-alarm"),
                                    message=f"Illegal concentration entry! Must be between {MIN_CONCENTRATION} and {MAX_CONCENTRATION} M",
                                ),
                            ],
                            id=self.id("conc-panel"),
                            style={"display": "none"},
                        ),
                        html.Div(id=self.id("element_specific_controls")),
                    ]
                ),
                self.get_bool_input(
                    "show_heatmap",  # kwarg_label
                    # state=self.default_state,
                    default=self.default_state["show_heatmap"],
                    label="Show Heatmap",
                    help_str="Hide or show a heatmap showing the decomposition energy for a specific "
                    "entry in this system.",
                ),
                html.Div(
                    [
                        self.get_choice_input(
                            "heatmap_choice",
                            state={},
                            label="Heatmap entry",
                            help_str="Choose the entry to use for heatmap generation.",
                            disabled=True,
                        ),
                        html.A(
                            "\U0001f517 to detail page",
                            id=self.id("ext-link"),
                            href="",
                            hidden=True,
                            target="_blank",
                        ),
                    ],
                    id=self.id("heatmap_choice_container"),
                    style={"width": "250px"},  # better to assign a class for selection
                ),
            ]
        )

        graph = (
            html.Div(
                dcc.Graph(
                    figure=go.Figure(
                        layout={**PourbaixDiagramComponent.empty_plot_style}
                    ),
                    responsive=True,
                    config={"displayModeBar": False, "displaylogo": False},
                ),
                style={"minHeight": "500px"},
                id=self.id("graph-panel"),
            ),
        )

        return {"graph": graph, "options": options}

    def layout(self) -> html.Div:
        return html.Div(
            children=[
                self._sub_layouts["options"],
                self._sub_layouts["graph"],
            ]
        )

    def generate_callbacks(self, app, cache) -> None:
        @app.callback(
            Output(self.id("heatmap_choice_container"), "children"),
            Input(self.id(), "data"),
            Input(self.id("mat-details"), "data"),
            Input(self.get_kwarg_id("filter_solids"), "value"),
        )
        def update_heatmap_choices(entries, mat_detials, filter_solids):
            if not entries:
                raise PreventUpdate

            kwargs = self.reconstruct_kwargs_from_state()
            filter_solids = kwargs["filter_solids"]

            entries_obj = self.from_data(entries)
            solid_entries = [
                entry for entry in entries_obj if entry.phase_type == "Solid"
            ]

            if filter_solids:
                # O is 2.46 b/c pbx entry finds energies referenced to H2O
                entries_HO = [ComputedEntry("H", 0), ComputedEntry("O", 2.46)]
                solid_pd = PhaseDiagram(solid_entries + entries_HO)
                entries_obj = list(set(solid_pd.stable_entries) - set(entries_HO))
                entries = [en.as_dict() for en in entries_obj]

            options = []
            for entry in entries:
                if entry["entry_id"].startswith("mp"):
                    composition = Composition(entry["entry"]["composition"])
                    formula = unicodeify(composition.reduced_formula)
                    mpid = entry["entry_id"]

                    # get material details
                    functional = mpid.split("-")[2]
                    mpid_wo_function = "mp-" + mpid.split("-")[1]
                    if mpid_wo_function in mat_detials:
                        structure_text = mat_detials[mpid_wo_function]["structure_text"]
                        crystal_system = mat_detials[mpid_wo_function]["crystal_system"]

                        label_text_list = [
                            f"{formula} ({mpid_wo_function}, {functional}) \n"
                        ]
                        if structure_text:
                            label_text_list.append(
                                " - Prototype: " + structure_text + "\n"
                            )
                        if crystal_system:
                            label_text_list.append(
                                " - Crystal system: " + crystal_system + "\n"
                            )
                        label = "".join(label_text_list)

                        option = {"label": label, "value": mpid}
                    else:
                        option = {"label": f"{formula} ({mpid})", "value": mpid}

                    # options.append({"label": f"{formula} ({mpid})", "value": mpid})
                    options.append(option)
                    options.sort(key=lambda x: x["label"])
            return [
                self.get_choice_input(
                    "heatmap_choice",
                    state={},
                    label="Heatmap Entry",
                    help_str="Choose the entry to use for heatmap generation.",
                    options=options,
                    disabled=False,
                    style={"width": "100%", "whiteSpace": "nowrap"},
                ),
                html.A(
                    "\U0001f517 to detail page",
                    id=self.id("ext-link"),
                    href="",
                    hidden=True,
                    target="_blank",
                ),
            ]

        @app.callback(
            Output(self.id("element_specific_controls"), "children"),
            Output(self.id("comp-panel"), "style"),
            Output(self.id("elements-store"), "data"),
            Output(self.id("comp-text"), "value"),
            Output(self.id("composition-title"), "children"),
            Input(self.id(), "data"),
            prevent_initial_call=True,
        )
        def update_element_specific_sliders(
            entries,
        ):
            """
            When pourbaix entries input, add concentration and composition options
            """
            if not entries:
                raise PreventUpdate

            elements = set()

            for entry in entries:
                if entry["entry_id"].startswith("mp"):
                    composition = Composition(entry["entry"]["composition"])
                    elements.update(composition.elements)

            # exclude O and H
            elements = elements - ELEMENTS_HO

            comp_inputs = []
            conc_inputs = []

            for element in sorted(elements):
                conc_input = html.Div(
                    [
                        self.get_numerical_input(
                            f"conc-{element}",
                            default=1e-6,
                            min=MIN_CONCENTRATION,
                            max=MAX_CONCENTRATION,
                            label=f"Concentration of {element} ion",
                            style={"width": "10rem", "fontSize": "14px"},
                        )
                    ]
                )

                conc_inputs.append(conc_input)

            comp_conc_controls = []
            comp_conc_controls += comp_inputs

            ion_label = (
                "Set Ion Concentrations (M)"
                if len(elements) > 1
                else "Set Ion Concentration"
            )
            comp_conc_controls.append(ctl.Label(ion_label))

            comp_conc_controls += conc_inputs

            #
            comp_panel_style = {"display": "none"}
            if len(elements) > 1:
                comp_panel_style = {"display": "block"}

            #
            elements = [element.symbol for element in elements]

            #
            default_comp = ":".join(["1" for _ in elements])

            #
            title = "Composition of " + ":".join(elements)

            return (
                html.Div(comp_conc_controls),
                comp_panel_style,
                elements,
                default_comp,
                title,
            )

        @cache.memoize(timeout=5 * 60)
        def get_pourbaix_diagram(pourbaix_entries, **kwargs):
            return PourbaixDiagram(pourbaix_entries, **kwargs)

        @app.callback(
            Output(self.id("graph-panel"), "children"),
            Output(self.id("invalid-comp-alarm"), "displayed"),
            Output(self.id("invalid-conc-alarm"), "displayed"),
            Output(self.id("display-composition"), "children"),
            Input(self.id(), "data"),
            Input(self.id("display-composition"), "children"),
            Input(self.get_all_kwargs_id(), "value"),
            Input(self.id("comp-btn"), "n_clicks"),
            State(self.id("elements-store"), "data"),
            State(self.id("comp-text"), "value"),
            Input(self.id("element_specific_controls"), "children"),
            prevent_initial_call=True,
        )
        def make_figure(
            pourbaix_entries,
            dependency,
            kwargs,
            n_clicks,
            elements,
            comp_text,
            dependency2,
        ) -> go.Figure:
            if pourbaix_entries is None:
                raise PreventUpdate

            # check if composition input
            if n_clicks:
                raw_comp_list = comp_text.split(":")
            else:
                raw_comp_list = [1 / len(elements) for _ in elements]

            if len(raw_comp_list) != len(elements):
                logger.error("Invalid composition input!")
                return (self.get_figure_div(), True, False, "")
            try:
                # avoid direct type casting because string inputs may raise errors
                comp_list = [float(t) for t in raw_comp_list]
                comp_dict = {el: comp for comp, el in zip(comp_list, elements)}
                comp = Composition(comp_dict)
                formula = Composition(
                    comp.get_integer_formula_and_factor()[0]
                ).reduced_formula

            except Exception:
                logger.error("Invalid composition input!")
                return (self.get_figure_div(), True, False, "")

            kwargs = self.reconstruct_kwargs_from_state()

            pourbaix_entries = self.from_data(pourbaix_entries)

            # Get heatmap id
            heatmap_entry = None
            if kwargs.get("show_heatmap") and kwargs.get("heatmap_choice"):
                # get Entry object based on the heatmap_choice, which is entry_id string
                heatmap_entry = next(
                    entry
                    for entry in pourbaix_entries
                    if entry.entry_id == kwargs["heatmap_choice"]
                )

                # if using heatmap, comp_dict is constrained and is set automatically
                comp_dict = {
                    element: coeff
                    for element, coeff in heatmap_entry.composition.items()
                    if element not in ELEMENTS_HO
                }

            conc_dict = {}
            # e.g. kwargs contains {"conc-Ag": 1e-6, "conc-Fe": 1e-4},
            # essentially {slider_name: slider_value}
            for key, val in kwargs.items():
                if "conc" in key:  # keys are encoded like "conc-Ag"
                    if val is None:
                        # if the input is out of pre-defined range, Input will get None
                        return (self.get_figure_div(), False, True, "")

                    el = key.split("-")[1]
                    conc_dict[el] = val
            conc_dict = conc_dict or None
            pourbaix_diagram = get_pourbaix_diagram(
                pourbaix_entries,
                comp_dict=comp_dict,
                conc_dict=conc_dict,
                filter_solids=kwargs["filter_solids"],
            )

            self.logger.debug(  # noqa: PLE1205
                "Generated pourbaix diagram",
                len(pourbaix_entries),
                heatmap_entry,
                conc_dict,
                comp_dict,
            )

            figure = self.get_figure(
                pourbaix_diagram,
                heatmap_entry=heatmap_entry,
            )
            return (
                self.get_figure_div(figure=figure),
                False,
                False,
                html.Small(f"Pourbaix composition set to {unicodeify(formula)}."),
            )
