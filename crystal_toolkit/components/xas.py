import os

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from pymatgen import MPRester

from crystal_toolkit.components.core import MPComponent, PanelComponent
from crystal_toolkit.helpers.layouts import *
from crystal_toolkit import __file__ as module_path


# Author: Matthew McDermott
# Contact: mcdermott@lbl.gov

class XASComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("mpid")

    # X-ray Absoprtion Spectrum - default layout
    default_xas_layout = dict(
        xaxis={'title': 'Energy (eV)',
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

        yaxis={'title': 'Absorption Coeff, μ (a.u.)',
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
        hovermode='x',
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, b=50, t=50, pad=0, r=30)
    )

    line_colors = ['rgb(22, 96, 167)', 'rgb(54, 34, 156)', 'rgb(23, 45, 23)', 'rgb(150,100,1)']

    empty_plot_style = {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }

    @property
    def all_layouts(self):

        # Main plot
        graph = html.Div(
            [
                dcc.Graph(
                    figure=go.Figure(layout=XASComponent.empty_plot_style),
                    config={"displayModeBar": False},
                )
            ], id=self.id("xas-div")
        )

        element_selector = html.Div(
            [
                html.P('Select an Element:'),
                dcc.RadioItems(
                    options =[],
                    id=self.id("element-selector"),
                    labelStyle={'display': 'inline-block', 'margin':'4px'}
                )
            ]
        )

        return {"graph": graph,
                "element_selector": element_selector,
                }

    @property
    def standard_layout(self):
        return html.Div([self.all_layouts["element_selector"],
                         self.all_layouts["graph"],
                         ])

    def _generate_callbacks(self, app, cache):

        @app.callback(Output(self.id("xas-div"), "children"),
                      [Input(self.id(), "data")])
        def update_graph(plotdata):
            if plotdata == []:
                return html.P("XANES pattern not found for this structure.")
            else:
                return [dcc.Graph(figure=go.Figure(data=plotdata,
                                                   layout=self.default_xas_layout))]

        @app.callback(
            Output(self.id(), "data"),
            [
                Input(self.id("mpid"), "modified_timestamp"),
                Input(self.id("element-selector"), "value"),
            ],
            [State(self.id("mpid"), "data"), State(self.id("element-selector"), "options")]
        )
        def pattern_from_mpid(mpid_time, element, mpid, elem_options):
            if mpid is None or element is None or elem_options is None:
                raise PreventUpdate
            elems = [val["value"] for val in elem_options]

            url_path = '/materials/' + mpid["mpid"] + '/xas/' + element
            with MPRester() as mpr:
                data = mpr._make_request(url_path)

            if len(data) == 0:
                plotdata = []
            else:
                x = data[0]['spectrum'].x
                y = data[0]['spectrum'].y
                plotdata = [go.Scatter(x=x,
                                       y=y,
                                       line=dict(color=self.line_colors[elems.index(element)]))]

            return plotdata

        @app.callback(
            Output(self.id("element-selector"), "options"),
            [Input(self.id("mpid"), "modified_timestamp")],
            [State(self.id("mpid"), "data")],
        )
        def generate_element_options(mpid_time, mpid):
            if mpid is None:
                raise PreventUpdate
            print(mpid_time, mpid)
            with MPRester() as mpr:
                entry = mpr.get_entry_by_material_id(mpid["mpid"])
            comp = entry.composition
            elem_options = [str(comp.elements[i]) for i in range(0, len(comp))]
            return [{'label': i, 'value': i} for i in elem_options]

        @app.callback(
            Output(self.id("element-selector"), "value"),
            [Input(self.id("element-selector"), 'options')])
        def set_xas_value(options):
            print(options)
            return options[0]['value']


class XASPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xas = XASComponent()
        self.xas.attach_from(self, this_store_name="mpid")

    @property
    def title(self):
        return "X-Ray Absorption Spectra"

    @property
    def description(self):
        return "Display the K-edge X-Ray Absorption Near Edge Structure (XANES) for this structure, if it has been caclulated."

    @property
    def initial_contents(self):
        return html.Div(
            [
                super().initial_contents,
                # necessary to include for the callbacks from XRayDiffractionComponent to work
                html.Div([self.xas.standard_layout], style={"display": "none"}),
            ]
        )

    def update_contents(self, new_store_contents, *args):
        return self.xas.standard_layout
