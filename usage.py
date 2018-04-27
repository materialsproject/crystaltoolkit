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
                                dcc.Input(id='input-box', type='text', placeholder='Enter a formula or mp-id'),
                                html.Span(' '),
                                html.Button('Load', id='button')
                            ])

draw_options = dcc.Checklist(
    id='draw_options',
    options=[
        {'label': 'Draw Atoms', 'value': 'atoms'},
        {'label': 'Draw Bonds', 'value': 'bonds'},
        {'label': 'Draw Polyhedra', 'value': 'polyhedra'},
        {'label': 'Draw Unit Cell', 'value': 'unit_cell'}
    ],
    values=['atoms', 'bonds', 'polyhedra', 'unit_cell']
)

bonding_methods = [str(c.__name__) for c in NearNeighbors.__subclasses__()]
bonding_options = html.Div([html.Label("Bonding Algorithm"),dcc.Dropdown(
    id='bonding_options',
    options=[
        {'label': method, 'value': method} for method in bonding_methods
    ],
    value='MinimumOKeeffeNN'
)])

color_options = html.Div([html.Label("Color Code"),dcc.Dropdown(
    id='color_options',
    options=[
        {'label': option, 'value': option} for option in ['VESTA', 'Jmol']
    ],
    value='VESTA'
)])

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
                                mp_viewer.StructureViewerComponent(
                                id='viewer',
                                                                    data=crystal
                                                                )
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
                            bonding_options,
                            html.Br(),
                            color_options
                        ]
                    )]),
                    html.Div(className='one columns')
])

@app.callback(
    dash.dependencies.Output('color_options', 'options'),
    [dash.dependencies.Input('button', 'n_clicks')],
    [dash.dependencies.State('input-box', 'value')])
def update_color_options(n_clicks, input_formula_mpid):
    
    options = ['VESTA', 'Jmol'] 

    if  input_formula_mpid:
        
        structure = mpr.get_structures(input_formula_mpid)[0]
        options += structure.site_properties.keys()
    
    def pretty_rewrite(option):
        
        pretty_mapping = {
            'magmom': 'Magnetic moment',
            'coordination_no': 'Coordination number (from database)',
            'forces': 'Forces'
        }
        
        if option in pretty_mapping.keys():
            return pretty_mapping[option]
        else:
            return option
    
    return [
        {'label': pretty_rewrite(option), 'value': option} for option in options
    ]

@app.callback(
    dash.dependencies.Output('viewer', 'data'),
    [dash.dependencies.Input('button', 'n_clicks'),
     dash.dependencies.Input('bonding_options', 'value'),
     dash.dependencies.Input('color_options', 'value')],
    [dash.dependencies.State('input-box', 'value')])
def update_crystal_displayed(n_clicks, bonding_option, color_option, input_formula_mpid):

    if not input_formula_mpid:
        return crystal
    
    structure = mpr.get_structures(input_formula_mpid)[0]

    crystal_json =  MaterialsProjectStructureVis(structure,
    bonding_strategy=bonding_option,
    color_scheme=color_option).json
    
    return crystal_json
    
@app.callback(
    dash.dependencies.Output('viewer', 'visibilityOptions'),
    [dash.dependencies.Input('draw_options', 'values')])
def update_visible_elements(draw_options):
    return draw_options


if __name__ == '__main__':
    app.run_server(debug=True)
