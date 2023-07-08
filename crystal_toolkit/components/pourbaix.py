from __future__ import annotations

import re

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Component, Input, Output, State
from dash.exceptions import PreventUpdate
from frozendict import frozendict
from pymatgen.analysis.pourbaix_diagram import ELEMENTS_HO, PREFAC, PourbaixDiagram
from pymatgen.core import Composition
from pymatgen.util.string import unicodeify
from shapely.geometry import Polygon

import crystal_toolkit.helpers.layouts as ctl
from crystal_toolkit.core.mpcomponent import MPComponent

__author__ = "Joseph Montoya"
__email__ = "joseph.montoya@tri.global"


# TODO: fix bug for Pa, etc.
# TODO: fix bug with composition input, needs further investigation and testing
# TODO: add water stability region

HEIGHT = 550  # in px
WIDTH = 700  # in px


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
            "range": [-2, 16],
        },
        yaxis={
            "title": "Applied Potential (V vs. SHE)",
            "anchor": "x",
            "mirror": "ticks",
            "range": [-2, 4],
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

    # @staticmethod
    # def get_figure_with_shapes(
    #     pourbaix_diagram, heatmap_entry=None, heatmap_as_contour=True, show_labels=True
    # ):
    #     """
    #     Deprecated. This method returns a figure with Pourbaix domains as "shapes" and labels
    #     as "annotations." The new figure method instead returns a Pourbaix diagram with
    #     domains and labels as independent traces, so that they can be interacted with and
    #     placed ona  legend.
    #
    #     Static method for getting plotly figure from a Pourbaix diagram.
    #
    #     Args:
    #         pourbaix_diagram (PourbaixDiagram): Pourbaix diagram to plot
    #         heatmap_entry (PourbaixEntry): id for the heatmap generation
    #         heatmap_as_contour (bool): if True, display contours, if False heatmap as grid
    #
    #     Returns:
    #         (dict) figure layout
    #
    #     """
    #     # TODO: fix mpid problem.  Can't attach from mpid without it being a structure.
    #     data = []
    #
    #     # Get data for heatmap
    #     if heatmap_entry is not None:
    #         ph_range = np.arange(-2, 16.001, 0.1)
    #         v_range = np.arange(-2, 4.001, 0.1)
    #         ph_mesh, v_mesh = np.meshgrid(ph_range, v_range)
    #         decomposition_e = pourbaix_diagram.get_decomposition_energy(
    #             heatmap_entry, ph_mesh, v_mesh
    #         )
    #
    #         # Generate hoverinfo
    #         hovertexts = []
    #         for ph_val, v_val, de_val in zip(
    #             ph_mesh.ravel(), v_mesh.ravel(), decomposition_e.ravel()
    #         ):
    #             hovertext = [
    #                 f"∆G<sub>pbx</sub>={de_val:.2f}",
    #                 f"ph={ph_val:.2f}",
    #                 f"V={v_val:.2f}",
    #             ]
    #             hovertext = "<br>".join(hovertext)
    #             hovertexts.append(hovertext)
    #         hovertexts = np.reshape(hovertexts, list(decomposition_e.shape))
    #
    #         # Enforce decomposition limit energy
    #         decomposition_e = np.min(
    #             [decomposition_e, np.ones(decomposition_e.shape)], axis=0
    #         )
    #
    #         if not heatmap_as_contour:
    #             # Plotly needs a list here for validation
    #             h_map = go.Heatmap(
    #                 x=list(ph_range),
    #                 y=list(v_range),
    #                 z=decomposition_e,
    #                 text=hovertexts,
    #                 hoverinfo="text",
    #                 colorbar={
    #                     "title": "∆G<sub>pbx</sub> (eV/atom)",
    #                     "titleside": "right",
    #                 },
    #                 colorscale=PourbaixDiagramComponent.colorscale,
    #                 zmin=0,
    #                 zmax=1,
    #             )
    #             data.append(h_map)
    #
    #         else:
    #
    #             h_map = go.Contour(
    #                 z=decomposition_e,
    #                 x=list(ph_range),
    #                 y=list(v_range),
    #                 colorscale=PourbaixDiagramComponent.colorscale,  # or magma
    #                 zmin=0,
    #                 zmax=1,
    #                 connectgaps=True,
    #                 line_smoothing=0,
    #                 line_width=0,
    #                 contours_coloring="heatmap",
    #                 text=hovertexts,
    #             )
    #             data.insert(0, h_map)
    #
    #     shapes = []
    #     xy_data = []
    #     labels = []
    #
    #     for entry, vertices in pourbaix_diagram._stable_domain_vertices.items():
    #         formula = entry.name
    #         clean_formula = PourbaixDiagramComponent.clean_formula(formula)
    #
    #         # Generate annotation
    #         xy_data.append(np.average(vertices, axis=0))
    #         labels.append(clean_formula)
    #
    #         # Info on SVG paths: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths
    #         # Move to first point
    #         path = "M {},{}".format(*vertices[0])
    #         # Draw lines to each other point
    #         path += "".join("L {},{}".format(*vertex) for vertex in vertices[1:])
    #         # Close path
    #         path += "Z"
    #
    #         # Note that the lines and fills are added separately
    #         # so that the lines but not the fills will show up on heatmap.
    #         # This may be condensable in the future if plotly adds a more
    #         # general z-ordering of objects
    #
    #         # Fill with turquoise if solution
    #         if heatmap_entry is None:
    #             fillcolor = "White" if "Ion" in entry.phase_type else "PaleTurquoise"
    #             shape = go.layout.Shape(
    #                 type="path",
    #                 path=path,
    #                 fillcolor=fillcolor,
    #                 layer="below",
    #             )
    #             shapes.append(shape)
    #
    #         # Add lines separately so they show up on heatmap
    #         shape = go.layout.Shape(
    #             type="path",
    #             path=path,
    #             fillcolor="rgba(0,0,0,0)",
    #             line={"color": "Black", "width": 1},
    #         )
    #         shapes.append(shape)
    #
    #     layout = {**PourbaixDiagramComponent.default_plot_style}
    #     layout.update({"shapes": shapes})
    #
    #     if show_labels:
    #         if len(pourbaix_diagram.pbx_elts) == 1:
    #             # Add annotations to layout
    #             annotations = [
    #                 {
    #                     "align": "center",
    #                     "font": {"color": "#000000", "size": 15.0},
    #                     "opacity": 1,
    #                     "showarrow": False,
    #                     "text": label,
    #                     "x": x,
    #                     "xanchor": "center",
    #                     "yanchor": "auto",
    #                     # "xshift": -10,
    #                     # "yshift": -10,
    #                     "xref": "x",
    #                     "y": y,
    #                     "yref": "y",
    #                 }
    #                 for (x, y), label in zip(xy_data, labels)
    #             ]
    #             layout.update({"annotations": annotations})
    #         else:
    #             x, y = zip(*xy_data)
    #             data.append(
    #                 go.Scatter(x=x, y=y, text=labels, hoverinfo="text", mode="markers")
    #             )
    #
    #     figure = go.Figure(data=data, layout=layout)
    #
    #     return figure

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
                    fillcolor = "rgb(255,255,250,1)"  # same color as old website
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
            # so use white lines instead
            line = (
                {"color": "White", "width": 4}
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
        else:
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

            def get_text_size(available_vertical_space):
                """Set text size based on available vertical space."""
                return min(max(6 * available_vertical_space, 12), 20)

            annotations = [
                {
                    "align": "center",
                    "bgcolor": "white",
                    "font": {"color": "black", "size": get_text_size(height)},
                    "opacity": 1,
                    "showarrow": False,
                    "text": label,
                    "x": x,
                    "xanchor": "center",
                    "yanchor": "auto",
                    # "xshift": -10,
                    # "yshift": -10,
                    "xref": "x",
                    "y": y,
                    "yref": "y",
                }
                for (x, y), label, height in zip(xy_data, labels, domain_heights)
            ]
            layout.update({"annotations": annotations})

        # Get data for heatmap
        if heatmap_entry is not None:
            ph_range = np.arange(-2, 16.001, 0.1)
            v_range = np.arange(-2, 4.001, 0.1)
            ph_mesh, v_mesh = np.meshgrid(ph_range, v_range)
            decomposition_e = pourbaix_diagram.get_decomposition_energy(
                heatmap_entry, ph_mesh, v_mesh
            )

            # Generate hoverinfo
            hovertexts = []
            for ph_val, v_val, de_val in zip(
                ph_mesh.ravel(), v_mesh.ravel(), decomposition_e.ravel()
            ):
                hovertext = [
                    f"∆G<sub>pbx</sub>={de_val:.2f}",
                    f"ph={ph_val:.2f}",
                    f"V={v_val:.2f}",
                ]
                hovertext = "<br>".join(hovertext)
                hovertexts.append(hovertext)
            hovertexts = np.reshape(hovertexts, list(decomposition_e.shape))

            # Enforce decomposition limit energy
            decomposition_e = np.min(
                [decomposition_e, np.ones(decomposition_e.shape)], axis=0
            )

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
                colorscale=PourbaixDiagramComponent.colorscale,  # or magma
                zmin=0,
                zmax=1,
                connectgaps=True,
                line_smoothing=0,
                line_width=0,
                # contours_coloring="heatmap",
                text=hovertexts,
                name=f"{heatmap_formula} ({heatmap_entry.entry_id}) Heatmap",
                showlegend=True,
            )
            data.append(h_map)

        if show_water_lines:
            ph_range = [-2, 16]
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

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        options = html.Div(
            [
                self.get_bool_input(
                    "filter_solids",
                    state=self.default_state,
                    label="Filter Solids",
                    help_str="Whether to filter solid phases by stability on the compositional phase diagram. "
                    "The practical consequence of this is that highly oxidized or reduced phases that "
                    "might show up in experiments due to kinetic limitations on oxygen/hydrogen evolution "
                    "won't appear in the diagram, but they are not actually “stable” (and are frequently "
                    "overstabilized from DFT errors). Hence, including only the stable solid phases generally "
                    "leads to the most accurate Pourbaix diagrams.",
                ),
                self.get_bool_input(
                    "show_heatmap",  # kwarg_label
                    state=self.default_state,
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
                        )
                    ],
                    id=self.id("heatmap_choice_container"),
                ),
                html.Div(id=self.id("element_specific_controls")),
            ]
        )

        graph = html.Div(
            dcc.Graph(
                figure=go.Figure(layout={**PourbaixDiagramComponent.empty_plot_style}),
                id=self.id("graph"),
                responsive=True,
                config={"displayModeBar": False, "displaylogo": False},
            ),
            style={"min-height": "500px"},
        )

        return {"graph": graph, "options": options}

    def layout(self) -> html.Div:
        return html.Div(
            children=[self._sub_layouts["options"], self._sub_layouts["graph"]]
        )

    def generate_callbacks(self, app, cache) -> None:
        @app.callback(
            Output(self.id("heatmap_choice_container"), "children"),
            Input(self.id(), "data"),
        )
        def update_heatmap_choices(entries):
            if not entries:
                raise PreventUpdate

            options = []
            for entry in entries:
                if entry["entry_id"].startswith("mp"):
                    composition = Composition(entry["entry"]["composition"])
                    formula = unicodeify(composition.reduced_formula)
                    mpid = entry["entry_id"]
                    options.append({"label": f"{formula} ({mpid})", "value": mpid})

            return self.get_choice_input(
                "heatmap_choice",
                state={},
                label="Heatmap Entry",
                help_str="Choose the entry to use for heatmap generation.",
                options=options,
                disabled=False,
            )

        @app.callback(
            Output(self.id("element_specific_controls"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("heatmap_choice"), "value"),
            State(self.get_kwarg_id("show_heatmap"), "value"),
        )
        def update_element_specific_sliders(entries, heatmap_choice, show_heatmap):
            if not entries:
                raise PreventUpdate

            elements = set()

            kwargs = self.reconstruct_kwargs_from_state()
            heatmap_choice = kwargs.get("heatmap_choice")
            show_heatmap = kwargs.get("show_heatmap")
            heatmap_entry = None

            for entry in entries:
                if entry["entry_id"].startswith("mp"):
                    composition = Composition(entry["entry"]["composition"])
                    elements.update(composition.elements)
                if entry["entry_id"] == heatmap_choice:
                    heatmap_entry = entry

            # exclude O and H
            elements = elements - ELEMENTS_HO

            comp_defaults = {element: 1 / len(elements) for element in elements}

            comp_inputs = []
            conc_inputs = []
            for element in sorted(elements):
                if len(elements) > 1:
                    comp_input = html.Div(
                        [
                            self.get_slider_input(
                                f"comp-{element}",
                                default=comp_defaults[element],
                                label=f"Composition of {element}",
                                domain=[0, 1],
                                step=0.01,
                            )
                        ]
                    )
                    comp_inputs.append(comp_input)

                conc_input = html.Div(
                    [
                        self.get_numerical_input(
                            f"conc-{element}",
                            default=1e-6,
                            label=f"Concentration of {element} ion",
                            style={"width": "10rem"},
                        )
                    ]
                )

                conc_inputs.append(conc_input)

            comp_conc_controls = []
            if comp_inputs and (not show_heatmap) and (not heatmap_entry):
                comp_conc_controls += comp_inputs
                comp_conc_controls.append(
                    ctl.Block(html.Div(id=self.id("display-composition")))
                )
            if len(elements) > 1:
                comp_conc_controls.append(ctl.Label("Set Ion Concentrations"))
            else:
                comp_conc_controls.append(ctl.Label("Set Ion Concentration"))
            comp_conc_controls += conc_inputs

            return html.Div(comp_conc_controls)

        @app.callback(
            Output(self.id("display-composition"), "children"),
            Input(self.get_all_kwargs_id(), "value"),
        )
        def update_displayed_composition(*args):
            kwargs = self.reconstruct_kwargs_from_state()

            comp_dict = {}
            for key, val in kwargs.items():
                if "comp" in key:  # keys are encoded like "comp-Ag"
                    el = key.split("-")[1]
                    comp_dict[el] = val
            comp_dict = comp_dict or None

            if not comp_dict:
                return ""

            try:
                comp = Composition(comp_dict)
                formula = Composition(
                    comp.get_integer_formula_and_factor()[0]
                ).reduced_formula
            except Exception:
                return html.Small(
                    "Invalid composition selected.", style={"color": "red"}
                )

            return html.Small(f"Pourbaix composition set to {unicodeify(formula)}.")

        @cache.memoize(timeout=5 * 60)
        def get_pourbaix_diagram(pourbaix_entries, **kwargs):
            return PourbaixDiagram(pourbaix_entries, **kwargs)

        @app.callback(
            Output(self.id("graph"), "figure"),
            Input(self.id(), "data"),
            Input(self.get_all_kwargs_id(), "value"),
        )
        def make_figure(pourbaix_entries, *args) -> go.Figure:
            if pourbaix_entries is None:
                raise PreventUpdate

            kwargs = self.reconstruct_kwargs_from_state()

            pourbaix_entries = self.from_data(pourbaix_entries)

            # Get heatmap id
            if kwargs["show_heatmap"] and kwargs.get("heatmap_choice"):
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
            else:
                heatmap_entry = None

                # otherwise, user sets comp_dict
                comp_dict = {}
                # e.g. kwargs contains {"comp-Ag": 0.5, "comp-Fe": 0.5},
                # essentially {slider_name: slider_value}
                for key, val in kwargs.items():
                    if "comp" in key:  # keys are encoded like "comp-Ag"
                        el = key.split("-")[1]
                        comp_dict[el] = val
                comp_dict = comp_dict or None

            conc_dict = {}
            # e.g. kwargs contains {"conc-Ag": 1e-6, "conc-Fe": 1e-4},
            # essentially {slider_name: slider_value}
            for key, val in kwargs.items():
                if "conc" in key:  # keys are encoded like "conc-Ag"
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

            return self.get_figure(
                pourbaix_diagram,
                heatmap_entry=heatmap_entry,
            )

    # TODO
    # def graph_layout(self):
    #     return self._sub_layouts["graph"]
