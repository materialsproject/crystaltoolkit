import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import numpy as np
import re
from pymatgen import MPRester
from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram, ELEMENTS_HO

from crystal_toolkit.helpers.layouts import (
    MessageContainer,
    MessageBody,
)  # layout helpers like `Columns` etc. (most subclass html.Div)
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent


__author__ = "Joseph Montoya"
__email__ = "joseph.montoya@tri.global"


# TODO: fix bug for Pa, etc.

SUPPORTED_N_ELEMENTS = 4
WIDTH = 700  # in px


class PourbaixDiagramComponent(MPComponent):
    def __init__(self, pourbaix_diagram=None, **kwargs):
        super().__init__(**kwargs)

        # stores that trigger a new Pourbaix diagram
        self.create_store("mpid")  # e.g. "mp-123"
        self.create_store("chemsys")  # e.g. ["Fe", "O"], list of element strings
        self.create_store("struct")  # pymatgen.core.structure.Structure

        # filled from the input stores
        self.create_store("pourbaix_entries")

        self.create_store("figure")
        self.create_store("pourbaix_diagram_options")
        self.create_store("pourbaix_display_options")
        for index in range(SUPPORTED_N_ELEMENTS):
            self.create_store("concentration-slider-{}".format(index))
            self.create_store("concentration-slider-{}-div".format(index))

        self.create_store("conc_dict")
        self.create_store("pourbaix_diagram", initial_data=pourbaix_diagram)

    default_plot_style = dict(
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
        height=550,
        width=WIDTH,
        hovermode="closest",
        showlegend=False,
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

    empty_plot_style = {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }

    colorscale_classic = [
        [0.00, "#4728fa"],  # blue
        [0.33, "#f9f273"],  # yellow
        [0.66, "#e5211b"],  # red
        [1.00, "#ffffff"],  # white
    ]

    colorscale = "magma"

    default_table_params = [
        {"col": "Material ID", "edit": False},
        {"col": "Formula", "edit": True},
        {"col": "Formation Energy (eV/atom)", "edit": True},
        {"col": "Energy Above Hull (eV/atom)", "edit": False},
        {"col": "Predicted Stable?", "edit": False},
    ]

    empty_row = {
        "Material ID": None,
        "Formula": "INSERT",
        "Formation Energy (eV/atom)": "INSERT",
        "Energy Above Hull (eV/atom)": None,
        "Predicted Stable": None,
    }

    # TODO: why both plotter and pd
    @staticmethod
    def get_figure(
        pourbaix_diagram, heatmap_entry=None, heatmap_as_contour=True, show_labels=True
    ):
        """
        Static method for getting plotly figure from a pourbaix diagram

        Args:
            pourbaix_diagram (PourbaixDiagram): pourbaix diagram to plot
            heatmap_entry (PourbaixEntry): id for the heatmap generation
            heatmap_as_contour (bool): if True, display contours, if False heatmap as grid

        Returns:
            (dict) figure layout

        """
        # TODO: fix mpid problem.  Can't attach from mpid without it being a structure.
        data = []

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
                    "∆G<sub>pbx</sub>={:.2f}".format(de_val),
                    "ph={:.2f}".format(ph_val),
                    "V={:.2f}".format(v_val),
                ]
                hovertext = "<br>".join(hovertext)
                hovertexts.append(hovertext)
            hovertexts = np.reshape(hovertexts, list(decomposition_e.shape))

            # Enforce decomposition limit energy
            decomposition_e = np.min(
                [decomposition_e, np.ones(decomposition_e.shape)], axis=0
            )

            if not heatmap_as_contour:
                # Plotly needs a list here for validation
                hmap = go.Heatmap(
                    x=list(ph_range),
                    y=list(v_range),
                    z=decomposition_e,
                    text=hovertexts,
                    hoverinfo="text",
                    colorbar={
                        "title": "∆G<sub>pbx</sub> (eV/atom)",
                        "titleside": "right",
                    },
                    colorscale=PourbaixDiagramComponent.colorscale,
                    zmin=0,
                    zmax=1,
                )
                data.append(hmap)

            else:

                hmap = go.Contour(
                    z=decomposition_e,
                    x=list(ph_range),
                    y=list(v_range),
                    colorscale=PourbaixDiagramComponent.colorscale,  # or magma
                    zmin=0,
                    zmax=1,
                    connectgaps=True,
                    line_smoothing=0,
                    line_width=0,
                    contours_coloring="heatmap",
                    text=hovertexts,
                )
                data.insert(0, hmap)

        shapes = []
        xydata = []
        labels = []

        for entry, vertices in pourbaix_diagram._stable_domain_vertices.items():
            formula = entry.name
            clean_formula = PourbaixDiagramComponent.clean_formula(formula)

            # Generate annotation
            xydata.append(np.average(vertices, axis=0))
            labels.append(clean_formula)

            # Info on SVG paths: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths
            # Move to first point
            path = "M {},{}".format(*vertices[0])
            # Draw lines to each other point
            path += "".join(["L {},{}".format(*vertex) for vertex in vertices[1:]])
            # Close path
            path += "Z"

            # Note that the lines and fills are added separately
            # so that the lines but not the fills will show up on heatmap.
            # This may be condensable in the future if plotly adds a more
            # general z-ordering of objects

            # Fill with turquoise if solution
            if heatmap_entry is None:
                fillcolor = "White" if "Ion" in entry.phase_type else "PaleTurquoise"
                shape = go.layout.Shape(
                    type="path",
                    path=path,
                    fillcolor=fillcolor,
                    line_color=None,
                    layer="below",
                )
                shapes.append(shape)

            # Add lines separately so they show up on heatmap
            shape = go.layout.Shape(
                type="path", path=path, fillcolor=None, line_color="Black"
            )
            shapes.append(shape)

        layout = PourbaixDiagramComponent.default_plot_style
        layout.update({"shapes": shapes})

        if show_labels:
            if len(pourbaix_diagram.pbx_elts) == 1:
                # Add annotations to layout
                annotations = [
                    {
                        "align": "center",
                        "font": {"color": "#000000", "size": 15.0},
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
                    for (x, y), label in zip(xydata, labels)
                ]
                layout.update({"annotations": annotations})
            else:
                x, y = zip(*xydata)
                data.append(
                    go.Scatter(x=x, y=y, text=labels, hoverinfo="text", mode="markers")
                )

        figure = go.Figure(data=data, layout=layout)

        return figure

    # TODO: format formula
    @staticmethod
    def clean_formula(formula):
        # Superscript charges
        clean_formula = re.sub(r"\[([0-9+-]+)\]", r"<sup>\1</sup>", formula)

        # Subscript coefficients
        clean_formula = re.sub(
            r"([A-Za-z\(\)])([\d\.]+)", r"\1<sub>\2</sub>", clean_formula
        )
        return clean_formula

    @property
    def _sub_layouts(self):

        options = html.Div(
            [
                dcc.Checklist(
                    options=[{"label": "Filter solids ", "value": "filter_solids"}],
                    value=["filter_solids", "show_labels"],
                    id=self.id("pourbaix_diagram_options"),
                    style={"display": "inline-block"},
                    inputClassName="mpc-radio",
                ),
                dcc.Checklist(
                    options=[
                        {"label": "Show heatmap ", "value": "show_heatmap"},
                        {"label": "Show labels ", "value": "show_labels"},
                    ],
                    value=["show_labels"],
                    id=self.id("pourbaix_display_options"),
                    style={"display": "inline-block"},
                    inputClassName="mpc-radio",
                ),
            ],
            style={"width": WIDTH, "display": "inline-block"},
        )

        graph = html.Div(
            [
                dcc.Graph(
                    figure=go.Figure(layout=PourbaixDiagramComponent.empty_plot_style),
                    id=self.id("graph"),
                    config={"displayModeBar": False, "displaylogo": False},
                )
            ],
            id=self.id("pourbaix-div"),
        )

        sliders = html.Div(
            [
                html.Div(
                    children=[
                        html.Div(
                            "concentration-{}".format(n),
                            id=self.id("concentration-{}-text".format(n)),
                        ),
                        dcc.Slider(
                            id=self.id("concentration-slider-{}".format(n)),
                            min=-8,
                            max=1,
                            step=1,
                            value=-4,
                        ),
                    ],
                    id=self.id("concentration-slider-{}-div".format(n)),
                    style={"display": "none"},
                )
                for n in range(SUPPORTED_N_ELEMENTS)
            ],
            id=self.id("slider-div"),
            style={"width": WIDTH},
        )

        return {"graph": graph, "options": options, "sliders": sliders}

    @property
    def layout(self):
        return html.Div(
            children=[
                self._sub_layouts["options"],
                self._sub_layouts["sliders"],
                self._sub_layouts["graph"],
            ]
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("pourbaix-div"), "children"),
            [Input(self.id("figure"), "data")],
        )
        def update_graph(figure):
            if figure is None:
                raise PreventUpdate
            elif figure == "too_many_elements":
                search_error = (
                    MessageContainer(
                        [
                            MessageBody(
                                dcc.Markdown(
                                    "Pourbaix diagrams may only be calculated for materials "
                                    "with {} or fewer non-OH elements".format(
                                        SUPPORTED_N_ELEMENTS
                                    )
                                )
                            )
                        ],
                        kind="warning",
                    ),
                )
                return search_error

            else:
                plot = [
                    dcc.Graph(
                        figure=figure,
                        config={"displayModeBar": False, "displaylogo": False},
                    )
                ]
                return plot

        @app.callback(
            Output(self.id("figure"), "data"),
            [
                Input(self.id("pourbaix_diagram"), "data"),
                Input(self.id("pourbaix_display_options"), "value"),
                Input(self.id("pourbaix_entries"), "data"),
                Input(self.id("struct"), "data"),
            ],
        )
        def make_figure(
            pourbaix_diagram, pourbaix_display_options, pourbaix_entries, struct
        ):
            if pourbaix_entries == "too_many_elements":
                return "too_many_elements"

            if pourbaix_diagram is None:
                raise PreventUpdate

            pourbaix_display_options = pourbaix_display_options or []

            pourbaix_diagram = self.from_data(pourbaix_diagram)
            pourbaix_entries = self.from_data(pourbaix_entries)

            # Get heatmap id
            if "show_heatmap" in pourbaix_display_options:
                struct = self.from_data(struct)
                with MPRester() as mpr:
                    # Should probably enable fetching pourbaix entry
                    # by mpid in MPRester
                    heatmap_id = mpr.find_structure(struct)[0]

                # Find entry
                heatmap_entry = [
                    entry for entry in pourbaix_entries if heatmap_id in entry.entry_id
                ][0]
            else:
                heatmap_entry = None

            show_labels = "show_labels" in pourbaix_display_options
            fig = self.get_figure(
                pourbaix_diagram, heatmap_entry=heatmap_entry, show_labels=show_labels
            )
            return fig

        @app.callback(
            Output(self.id("pourbaix_diagram"), "data"),
            [
                Input(self.id("pourbaix_entries"), "data"),
                Input(self.id("pourbaix_diagram_options"), "value"),
                Input(self.id("conc_dict"), "data"),
                Input(self.id("struct"), "data"),
            ],
        )
        def create_pbx_object(
            pourbaix_entries, pourbaix_diagram_options, conc_dict, struct
        ):
            # Pass along element restriction
            if pourbaix_entries == "too_many_elements":
                return "too_many_elements"

            self.logger.debug("Updating entries")
            if pourbaix_entries is None or not pourbaix_entries:
                self.logger.debug("Preventing updating entries")
                raise PreventUpdate

            pourbaix_entries = self.from_data(pourbaix_entries)

            # filter_solids = True
            if pourbaix_diagram_options is not None:
                filter_solids = "filter_solids" in pourbaix_diagram_options
            else:
                filter_solids = True

            # Get composition from structure
            struct = self.from_data(struct)
            comp_dict = {
                str(elt): coeff
                for elt, coeff in struct.composition.items()
                if elt not in ELEMENTS_HO
            }
            if conc_dict is not None:
                conc_dict = self.from_data(conc_dict)

            pourbaix_diagram = PourbaixDiagram(
                pourbaix_entries,
                comp_dict=comp_dict,
                conc_dict=conc_dict,
                filter_solids=filter_solids,
            )
            self.logger.debug("Generated pourbaix diagram")
            return pourbaix_diagram

        @app.callback(
            Output(self.id("pourbaix_entries"), "data"),
            [
                Input(self.id("mpid"), "data"),
                Input(self.id("struct"), "data"),
                Input(self.id("chemsys"), "data"),
            ],
        )
        def get_chemsys_from_struct_mpid(mpid, struct, chemsys):
            ctx = dash.callback_context

            if ctx is None or not ctx.triggered:
                raise PreventUpdate

            trigger = ctx.triggered[0]

            if trigger["value"] is None:
                raise PreventUpdate

            # mpid trigger
            if trigger["prop_id"] == self.id("mpid") + ".data":
                with MPRester() as mpr:
                    entry = mpr.get_entry_by_material_id(mpid)

                chemsys = [str(elem) for elem in entry.composition.elements]

            # struct trigger
            elif trigger["prop_id"] == self.id("struct") + ".data":
                chemsys = [
                    str(elem) for elem in self.from_data(struct).composition.elements
                ]

            if len(set(chemsys) - {"O", "H"}) > SUPPORTED_N_ELEMENTS:
                return "too_many_elements"

            with MPRester() as mpr:
                pourbaix_entries = mpr.get_pourbaix_entries(chemsys)

            return pourbaix_entries

        # This is a hacked way of getting concentration, but haven't found a more sane fix
        # Basically creates 3 persistent sliders and updates the concentration according to
        # their values.  Renders only the necessary ones visible.
        @app.callback(
            [
                Output(self.id("concentration-slider-{}-div".format(index)), "style")
                for index in range(SUPPORTED_N_ELEMENTS)
            ],
            [
                Input(self.id("pourbaix_diagram"), "data"),
                Input(self.id("struct"), "data"),
            ],
        )
        def reveal_sliders(pourbaix_diagram, struct):
            if struct is None:
                raise PreventUpdate
            struct = self.from_data(struct)
            pbx_elts = [
                elt for elt in struct.composition.keys() if elt not in ELEMENTS_HO
            ]
            nelts = len(pbx_elts)
            styles = [{}] * nelts
            styles += [{"display": "none"}] * (SUPPORTED_N_ELEMENTS - nelts)
            return styles

        @app.callback(
            [Output(self.id("conc_dict"), "data")]
            + [
                Output(self.id("concentration-{}-text".format(index)), "children")
                for index in range(SUPPORTED_N_ELEMENTS)
            ],
            [Input(self.id("struct"), "data")]
            + [
                Input(self.id("concentration-slider-{}".format(index)), "value")
                for index in range(SUPPORTED_N_ELEMENTS)
            ],
        )
        def update_conc_dict(struct, *args):
            if args[0] is None:
                raise PreventUpdate

            struct = self.from_data(struct)
            pbx_elts = sorted(
                [
                    str(elt)
                    for elt in struct.composition.keys()
                    if elt not in ELEMENTS_HO
                ]
            )
            conc_dict = {
                k: 10 ** arg for k, arg in zip(pbx_elts, args[: len(pbx_elts)])
            }
            conc_text = ["{}: {} M".format(k, v) for k, v in conc_dict.items()]
            conc_text += [""] * (SUPPORTED_N_ELEMENTS - len(pbx_elts))
            return [conc_dict] + conc_text


class PourbaixDiagramPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pourbaix_component = PourbaixDiagramComponent()
        self.pourbaix_component.attach_from(self, this_store_name="struct")

    @property
    def title(self):
        return "Pourbaix Diagram"

    @property
    def description(self):
        return (
            "Display the pourbaix diagram for the"
            " chemical system containing this structure (fewer than 3 non-OH species)."
        )

    def update_contents(self, new_store_contents, *args):
        return self.pourbaix_component.layout
