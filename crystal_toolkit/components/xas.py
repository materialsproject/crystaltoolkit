from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Component, Input, Output, State
from dash.exceptions import PreventUpdate
from frozendict import frozendict

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import MessageBody, MessageContainer

# Author: Matthew McDermott
# Contact: mcdermott@lbl.gov


class XASComponent(MPComponent):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.create_store("mpid")
        self.create_store("elements")

    default_xas_layout = frozendict(
        xaxis={
            "title": "Energy (eV)",
            "anchor": "y",
            "mirror": "ticks",
            "nticks": 8,
            "showgrid": True,
            "showline": True,
            "side": "bottom",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"size": 16.0},
            "type": "linear",
            "zeroline": False,
        },
        yaxis={
            "title": "Absorption Coeff, μ (a.u.)",
            "anchor": "x",
            "mirror": "ticks",
            "nticks": 7,
            "showgrid": True,
            "showline": True,
            "side": "left",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"size": 16.0},
            "type": "linear",
            "zeroline": False,
        },
        autosize=True,
        height=300,
        hovermode="x",
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, b=50, t=50, pad=0, r=30),
    )

    line_colors = (
        "rgb(128, 0, 0)",
        "rgb(0, 0, 128)",
        "rgb(60, 180, 75)",
        "rgb(145,30,180)",
        "rgb(230,25,75)",
        "rgb(240,50,230)",
    )

    empty_plot_style = frozendict(
        xaxis={"visible": False},
        yaxis={"visible": False},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        graph = html.Div(
            [
                dcc.Graph(
                    figure=go.Figure(layout=XASComponent.empty_plot_style),
                    config={"displayModeBar": False},
                )
            ],
            id=self.id("xas-div"),
        )

        element_selector = html.Div(
            [
                html.P("Select an Element:"),
                dcc.RadioItems(
                    id=self.id("element-selector"),
                    options=[],
                    inputClassName="mpc-radio",
                    labelClassName="mpc-radio",
                ),
            ]
        )

        return {"graph": graph, "element_selector": element_selector}

    @property
    def layout(self) -> html.Div:
        """Main layout for XAS component."""
        return html.Div(
            [self._sub_layouts["graph"], self._sub_layouts["element_selector"]]
        )

    def generate_callbacks(self, app, cache) -> None:
        """Generate callbacks for XAS component.

        Args:
            app (dash.Dash): Dash app to generate callbacks for.
            cache (_type_): _description_

        Raises:
            PreventUpdate: If no data is available.

        Returns:
            dcc.Graph | MessageContainer: XAS plot or error message.
        """

        @app.callback(Output(self.id("xas-div"), "children"), Input(self.id(), "data"))
        def update_graph(plotdata):
            if not plotdata:
                raise PreventUpdate
            if plotdata == "error":
                return MessageContainer(
                    [
                        MessageBody(
                            dcc.Markdown(
                                "XANES pattern not available for this selection."
                            )
                        )
                    ],
                    kind="warning",
                )
            return dcc.Graph(
                figure=go.Figure(data=plotdata, layout=self.default_xas_layout),
                config={"displayModeBar": False},
            )

        @app.callback(
            Output(self.id(), "data"),
            Output(self.id("elements"), "data"),
            Input(self.id("element-selector"), "value"),
            State(self.id("mpid"), "data"),
            State(self.id("elements"), "data"),
        )
        def pattern_from_mpid(element, mpid, elements):
            if not element or not elements:
                raise PreventUpdate

            url_path = f"/materials/{mpid['mpid']}/xas/{element}"

            from mp_api.client import MPRester

            with MPRester() as mpr:
                data = mpr._make_request(url_path)  # querying MP database via MAPI

            if len(data) == 0:
                plot_data = "error"
            else:
                x = data[0]["spectrum"].x
                y = data[0]["spectrum"].y
                line = dict(color=self.line_colors[elements.index(element)])
                plot_data = [go.Scatter(x=x, y=y, line=line)]

            with MPRester() as mpr:
                entry = mpr.get_entry_by_material_id(mpid["mpid"])
            comp = entry.composition
            elem_options = [str(comp.elements[i]) for i in range(len(comp))]

            return plot_data, elem_options

        @app.callback(
            Output(self.id("element-selector"), "options"),
            Input(self.id("elements"), "data"),
        )
        def generate_element_options(elements):
            return [{"label": i, "value": i} for i in elements]

        @app.callback(
            Output(self.id("element-selector"), "value"),
            Input(self.id("element-selector"), "options"),
        )
        def set_xas_value(options):
            if not options or not options[0]:
                raise PreventUpdate
            return options[0]["value"]


class XASPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.xas = XASComponent()
        self.xas.attach_from(self, this_store_name="mpid")

    @property
    def title(self) -> str:
        return "X-Ray Absorption Spectra"

    @property
    def description(self) -> str:
        return (
            "Display the K-edge X-Ray Absorption Near Edge Structure (XANES) for this structure, "
            "if it has been calculated by the Materials Project."
        )

    @property
    def loading_text(self) -> str:
        return "Searching for calculated XANES pattern on Materials Project..."

    @property
    def initial_contents(self) -> html.Div:
        return html.Div([super().initial_contents, html.Div([self.xas.layout])])

    def update_contents(self, new_store_contents, *args):
        return self.xas.layout

    # def generate_callbacks(self, app, cache) -> None:
    #
    #     super().generate_callbacks(app, cache)
    #
    #     @app.callback(
    #         Output(self.id("inner_contents"), "children"), Input(self.id(), "data")
    #     )
    #     def add_xas(mpid):
    #         if not mpid:
    #             raise PreventUpdate
    #         return self.xas.layout
