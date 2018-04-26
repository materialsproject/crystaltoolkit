import mp_viewer
import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash('')

app.scripts.config.serve_locally = True
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

from monty.serialization import loadfn
from pymatgen import MPRester
from pymatgen.vis.structure_vis_mp import MaterialsProjectStructureVis
from pymatgen.analysis.local_env import NearNeighbors

mpr = MPRester()

crystal = loadfn('crystal.json')

formula_input_button = html.Div([
                                dcc.Input(id='input-box', type='text', placeholder='Enter a formula...'),
                                html.Button('Submit', id='button')
                            ])

draw_options = dcc.Checklist(
    id='draw_options',
    options=[
        {'label': 'Draw Atoms', 'value': 'atoms'},
        {'label': 'Draw Bonds', 'value': 'bonds'},
        {'label': 'Draw Polyhedra', 'value': 'polyhedra'},
        {'label': 'Draw Unit Cell', 'value': 'unit_cell'},
        {'label': 'Animate', 'value': 'animate'}
    ],
    values=['atoms', 'bonds', 'polyhedra', 'unit_cell', 'animate']
)

bonding_methods = [str(c.__name__) for c in NearNeighbors.__subclasses__()]
bonding_options = dcc.Dropdown(
    options=[
        {'label': method, 'value': method} for method in bonding_methods
    ],
    value='MinimumDistanceNN'
)

app.layout = html.Div([
    html.Br(),
    html.H1('MP Viewer', style={'text-align': 'center'}),
    html.Br(),
    html.Div(
                className='row',
                children=[
                    html.Div(className='one columns'),
                    html.Div(
                        className='seven columns',
                        style={'text-align': 'right'},
                        children=[
                            html.Div(id='viewer-container',children=[
                                #mp_viewer.StructureViewerComponent(
                                #    value='my-value',
                                #    label='my-label',
                                #    data=crystal
                                #)
                            ])
                        ]
                    ),
                    html.Div(
                        className='three columns',
                        style={'text-align': 'left'},
                        children=[
                            formula_input_button,
                            html.Br(),
                            draw_options,
                            html.Br(),
                            bonding_options
                        ]
                    )]),
                    html.Div(className='one columns'),
mp_viewer.StructureViewerComponent()

])



@app.callback(
    dash.dependencies.Output('viewer-container', 'children'),
    [dash.dependencies.Input('button', 'n_clicks'),
     dash.dependencies.Input('draw_options', 'values')],
    [dash.dependencies.State('input-box', 'value')])
def update_output(n_clicks, draw_options, value):
    
    value = value or "NaCl"
    
    structure = mpr.get_structures(value)[0]

    crystal_json =  MaterialsProjectStructureVis(structure).json
    
    # TODO: should edit the React component to be able to just update its contents
    viewer = mp_viewer.StructureViewerComponent(
                                    data=crystal_json,
                                    showAtoms='atoms' in draw_options
                                )
                                
    return viewer


if __name__ == '__main__':
    app.run_server(debug=True)
