import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from pymatgen import MPRester
from pymatgen.core.structure import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from pymatgen.analysis.diffraction.xrd import XRDCalculator, DiffractionPattern

from crystal_toolkit.helpers.layouts import *  # layout helpers like `Columns` etc. (most subclass html.Div)
from crystal_toolkit.components.core import MPComponent

class XRayDiffractionComponent(MPComponent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("mpid")
        self.create_store("struct")

    # Default XRD plot style settings
    default_xrd_plot_style = dict(
        title = "Calculated X-Ray Diffraction Pattern",
        xaxis={'title': "2" + u"\u03B8" + " (deg)",
               'anchor': 'y',
               'mirror': 'ticks',
               'nticks': 8,
               'showgrid': True,
               'showline': True,
               'side': 'bottom',
               'tickfont': {'size': 16.0},
               'ticks': 'inside',
               'titlefont': {'size': 16.0},
               'type': 'linear',
               'zeroline': False},

        yaxis={'title': 'Intensity (a.u.)',
               'anchor': 'x',
               'mirror': 'ticks',
               'nticks': 7,
               'showgrid': True,
               'showline': True,
               'side': 'left',
               'tickfont': {'size': 16.0},
               'ticks': 'inside',
               'titlefont': {'size': 16.0},
               'type': 'linear',
               'zeroline': False},

        autosize=True,
        hovermode='x',
        height = 225,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, b=50, t=50, pad=0, r=30))

    @property
    def all_layouts(self):
        # Main plot
        graph = html.Div([
            dcc.Graph(id=self.id("xrd-plot"),config={'displayModeBar':False})
        ])

        # Radiation source selector
        rad_source = html.Div([
            html.P('Radiation Source (K' + u"\u03B1)" + ":"),
            dcc.RadioItems(
                id=self.id('rad-source'),
                options=[
                    {'label': ' Cu ' , 'value': 'CuKa'},
                    {'label': ' Mo ', 'value': 'MoKa'},
                    {'label': ' Ag ', 'value': 'AgKa'},
                    {'label': ' Fe ', 'value': 'FeKa'},
                ],
                value='CuKa',
                )
            ])

        return {'graph': graph, 'rad_source':rad_source}

    @property
    def standard_layout(self):
        return html.Div([self.all_layouts['graph'], self.all_layouts['rad_source']])

    def _generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("xrd-plot"),"figure"),
            [Input(self.id(), "data")]
        )
        def update_graph(data):
            domain = max(data['x']) - min(data['x']) # find total domain of angles in pattern
            bar_width = 0.01*domain # set width of bars to 1% of the domain
            length = len(data['x'])

            hkl_list = [hkl[0]['hkl'] for hkl in data['hkls']]
            hkls = ["hkl: (" + ' '.join([str(i) for i in hkl]) + ")" for hkl in hkl_list] # convert to (h k l) format

            annotations = [hkl + '<br>' + 'd: ' + str(round(d,3)) for hkl,d in zip(hkls,data['d_hkls'])] # text boxes

            plot_data = [go.Bar(x=data['x'], y=data['y'], width=[bar_width]*length, text=annotations)]
            graph = go.Figure(data=plot_data, layout=XRayDiffractionComponent.default_xrd_plot_style)

            return graph

        @app.callback(
            Output(self.id(), "data"),
             [Input(self.id("rad-source"),"value"),
             Input(self.id("mpid"),"modified_timestamp"),
             Input(self.id("struct"),"modified_timestamp")],
            [State(self.id("mpid"), "data"),
             State(self.id("struct"), "data")]
        )
        def pattern_from_mpid_or_struct(rad_source,mp_time,struct_time,mpid,struct):

            if (struct_time is None) or (mp_time is None):
                raise PreventUpdate

            if struct_time > mp_time:
                if struct is None:
                    raise PreventUpdate
                sga = SpacegroupAnalyzer(self.from_data(struct))
                struct = sga.get_conventional_standard_structure() # always get conventional structure
            elif mp_time >= struct_time:
                if mpid is None:
                    raise PreventUpdate
                mpid = mpid['mpid']

                with MPRester() as mpr:
                    struct = mpr.get_structure_by_material_id(mpid, conventional_unit_cell=True)

            xrdc = XRDCalculator(wavelength=rad_source)
            data = xrdc.get_pattern(struct,two_theta_range=None)

            return data.as_dict()