import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objs as go
import numpy as np
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from pymatgen import MPRester
from pymatgen.core.composition import Composition
from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram, PourbaixPlotter, \
    PourbaixEntry, MultiEntry

from crystal_toolkit.helpers.layouts import Columns, Column, MessageContainer, \
    MessageBody # layout helpers like `Columns` etc. (most subclass html.Div)
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent


__author__ = "Joseph Montoya"
__email__ = "joseph.montoya@tri.global"


class PourbaixDiagramComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("mpid")
        self.create_store("struct")
        self.create_store("figure")
        self.create_store("pourbaix_entries")

    # Default plot layouts for Binary (2), Ternary (3), Quaternary (4) phase diagrams
    default_plot_style = dict(
        xaxis={
            "title": "pH",
            "anchor": "y",
            "mirror": "ticks",
            "nticks": 8,
            "showgrid": False,
            "showline": True,
            "side": "bottom",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"color": "#000000", "size": 24.0},
            "type": "linear",
            "zeroline": False,
        },
        yaxis={
            "title": "Applied Potential (V vs. SHE)",
            "anchor": "x",
            "mirror": "ticks",
            "nticks": 7,
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
        width=500,
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

    empty_plot_style = {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }

    colorscale = [
        [0.0, "#008d00"],
        [0.1111111111111111, "#4b9f3f"],
        [0.2222222222222222, "#73b255"],
        [0.3333333333333333, "#97c65b"],
        [0.4444444444444444, "#b9db53"],
        [0.5555555555555556, "#ffdcdf"],
        [0.6666666666666666, "#ffb8bf"],
        [0.7777777777777778, "#fd92a0"],
        [0.8888888888888888, "#f46b86"],
        [1.0, "#e24377"],
    ]

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
    def figure_layout(self, pourbaix_diagram):
        """

        Args:
            pourbaix_diagram (PourbaixDiagram): pourbaix diagram to plot

        Returns:
            (dict) figure layout

        """
        dim = len(pourbaix_diagram.pourbaix_elements)

        shapes = []
        annotations = []

        for entry, vertices in pourbaix_diagram._stable_domain_vertices.items():
            formula = list(entry.name)

            clean_formula = self.clean_formula(formula)

            # Info on SVG paths: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths
            # Move to first point
            path = "M {},{}".format(*vertices[0])
            # Draw lines to each other point
            path += "".join(["L {},{}".format(*vertex) for vertex in vertices[1:]])
            # Close path
            path += "Z"
            shape = go.layout.Shape(
                type="path",
                path=path,
                fillcolor="Gray",
                linecolor="Black"
            )
            shapes.append(shape)

            # Generate annotation
            x, y = np.average(vertices, axis=0)
            annotation = {
                "align": "center",
                "font": {"color": "#000000", "size": 20.0},
                "opacity": 1,
                "showarrow": False,
                "text": clean_formula,
                "x": x,
                "xanchor": "right",
                "yanchor": "auto",
                "xshift": -10,
                "yshift": -10,
                "xref": "x",
                "y": y,
                "yref": "y",
            }

            annotations.append(annotation)
        layout = self.default_plot_style
        layout.update({"shapes": shapes,
                       "annotations": annotations})
        return layout

    @staticmethod
    def clean_formula(formula):
        s = []
        for char in formula:
            if char.isdigit():
                s.append(f"<sub>{char}</sub>")
            else:
                s.append(char)

        clean_formula = "".join(s)

        return clean_formula

    @property
    def all_layouts(self):

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

        return {"graph": graph}

    @property
    def standard_layout(self):
        return html.Div(
            [
                Columns(
                    [
                        Column(self.all_layouts["graph"]),
                        # Column(self.all_layouts["table"]),
                    ],
                    centered=True,
                )
            ]
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("pourbaix-div"), "children"), [Input(self.id("figure"), "data")]
        )
        def update_graph(figure):
            if figure is None:
                raise PreventUpdate
            elif figure == "error":
                search_error = (
                    MessageContainer(
                        [
                            MessageBody(
                                dcc.Markdown(
                                    "Plotting is only available for phase diagrams containing 2-4 components."
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

        @app.callback(Output(self.id("figure"), "data"), [Input(self.id(), "pourbaix_data")])
        def make_figure(pourbaix_diagram):
            if pourbaix_diagram is None:
                raise PreventUpdate

            pourbaix_diagram = self.from_data(pourbaix_diagram)

            fig = go.Figure()
            fig.layout = self.figure_layout(pourbaix_diagram)

            return fig

        @app.callback(Output(self.id(), "pourbaix_data"), [Input(self.id("pourbaix_entries"), "data")])
        def create_pbx_object(pourbaix_entries):
            if pourbaix_entries is None or not pourbaix_entries:
                raise PreventUpdate

            pourbaix_entries = self.from_data(pourbaix_entries)

            return self.to_data(PourbaixDiagram(pourbaix_entries))


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
            " chemical system containing this structure (between 2–4 species)."
        )

    def update_contents(self, new_store_contents, *args):
        return self.pourbaix_component.standard_layout
