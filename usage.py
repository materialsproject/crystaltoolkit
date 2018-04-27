import mp_viewer
import dash
import dash_core_components as dcc
import dash_html_components as html

import numpy as np
import json

from base64 import urlsafe_b64decode
from zlib import decompress
from urllib.parse import parse_qs

from dash.dependencies import Input, Output, State

from monty.serialization import loadfn

from pymatgen import MPRester, Structure
from pymatgen.vis.structure_vis_mp import MaterialsProjectStructureVis
from pymatgen.analysis.local_env import NearNeighbors

app = dash.Dash('')

app.scripts.config.serve_locally = True
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

mpr = MPRester()

DEFAULT_STRUCTURE = loadfn('default_structure.json')
DEFAULT_COLOR_SCHEME = 'VESTA'
DEFAULT_BONDING_METHOD = 'MinimumOKeeffeNN'

AVAILABLE_BONDING_METHODS = [str(c.__name__)
                             for c in NearNeighbors.__subclasses__()]

# to help with readability, each component of the app is defined
# in a modular way below; these are all then included in the app.layout

LAYOUT_FORMULA_INPUT = html.Div([
    dcc.Input(id='input-box', type='text', placeholder='Enter a formula or mp-id'),
    html.Span(' '),
    html.Button('Load', id='button')
])

LAYOUT_VISIBILITY_OPTIONS = dcc.Checklist(
    id='draw_options',
    options=[
        {'label': 'Draw Atoms', 'value': 'atoms'},
        {'label': 'Draw Bonds', 'value': 'bonds'},
        {'label': 'Draw Polyhedra', 'value': 'polyhedra'},
        {'label': 'Draw Unit Cell', 'value': 'unit_cell'}
    ],
    values=['atoms', 'bonds', 'polyhedra', 'unit_cell']
)

LAYOUT_BONDING_DROPDOWN = html.Div([html.Label("Bonding Algorithm"), dcc.Dropdown(
    id='bonding_options',
    options=[
        {'label': method, 'value': method} for method in AVAILABLE_BONDING_METHODS
    ],
    value=DEFAULT_BONDING_METHOD
)])

LAYOUT_COLOR_SCHEME_DROPDOWN = html.Div([html.Label("Color Code"), dcc.Dropdown(
    id='color_schemes',
    options=[
        {'label': option, 'value': option} for option in ['VESTA', 'Jmol']
    ],
    value=DEFAULT_COLOR_SCHEME
)])

LAYOUT_DEVELOPER_TEXTBOX = dcc.Textarea(
    id='structure',
    placeholder='Developer console',
    value='',
    style={'width': '100%', 'overflow-y': 'scroll',
           'height': '400px', 'font-family': 'monospace'}
)

# master app layout, includes layouts defined above
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Br(),
    html.H1('', style={'text-align': 'center'}),
    html.Br(),
    html.Div(
        className='row',
        children=[
            html.Div(className='one columns'),
            html.Div(
                className='seven columns',
                style={'text-align': 'right'},
                children=[
                    html.Div(id='viewer-container', children=[
                        mp_viewer.StructureViewerComponent(
                            id='viewer',
                            data=MaterialsProjectStructureVis(DEFAULT_STRUCTURE,
                                                              bonding_strategy=
                                                              DEFAULT_BONDING_METHOD,
                                                              color_scheme=
                                                              DEFAULT_COLOR_SCHEME).json
                        )
                    ])
                ]
            ),
            html.Div(
                className='three columns',
                style={'text-align': 'left'},
                children=[
                    LAYOUT_FORMULA_INPUT,
                    html.Br(),
                    LAYOUT_VISIBILITY_OPTIONS,
                    html.Br(),
                    LAYOUT_BONDING_DROPDOWN,
                    html.Br(),
                    LAYOUT_COLOR_SCHEME_DROPDOWN,
                    html.Br(),
                    html.Div(id='mp_text'),
                    html.Br(),
                    LAYOUT_DEVELOPER_TEXTBOX
                ]
            ),
            html.Div(className='one columns')
        ])
])


@app.callback(
    Output('color_schemes', 'options'),
    [Input('button', 'n_clicks')],
    [State('input-box', 'value')])
def update_color_options(n_clicks, input_formula_mpid):
    """
    Callback to update the available color scheme options
    (this is dynamic based on the structure site properties
    available).

    :param n_clicks: triggered when the load button is clicked
    :param input_formula_mpid:
    :return:
    """

    default_options = ['VESTA', 'Jmol']
    available_options = default_options.copy()

    if input_formula_mpid:
        structure = mpr.get_structures(input_formula_mpid)[0]
        for key, props in structure.site_properties.items():
            props = np.array(props)
            if len(props.shape) == 1:
                # can't color-code for vectors,
                # should draw arrows for these instead
                available_options.append(key)

    def pretty_rewrite(option):
        if option not in default_options:
            return "Site property: {}".format(option)
        else:
            return option

    return [
        {'label': pretty_rewrite(option), 'value': option}
        for option in available_options
    ]

@app.callback(
    Output('structure', 'value'),
    [Input('url', 'search')]
)
def update_structure(search_query):

    # strip leading ? from query, and parse into dict
    search_query = parse_qs(search_query[1:])

    if 'structure' in search_query:
        payload = search_query['structure'][0]
        payload = urlsafe_b64decode(payload)
        payload = decompress(payload)
        structure = Structure.from_str(payload, fmt='json')
    elif 'query' in search_query:
        structure = mpr.get_structures(search_query['query'][0])[0]
    else:
        structure = DEFAULT_STRUCTURE


    return json.dumps(json.loads(structure.to_json()), indent=4)

@app.callback(
    Output('mp_text', 'children'),
    [Input('structure', 'value')]
)
def find_structure_on_mp(structure):

    structure = Structure.from_str(structure, fmt='json')
    mpids = mpr.find_structure(structure)
    if mpids:
        links = ", ".join(["[{}](https://materialsproject.org/materials/{})".format(mpid, mpid)
                          for mpid in mpids])
        return dcc.Markdown("This structure is available on Materials Project: {}".format(links))
    else:
        return ""


@app.callback(
    Output('url', 'search'),
    [Input('button', 'n_clicks')],
    [State('input-box', 'value'),
     State('url', 'search')])
def format_query_string(n_clicks, input_formula_mpid, current_val):

    if not input_formula_mpid:
        return current_val
    else:
        return "?query={}".format(input_formula_mpid)

@app.callback(
    Output('viewer', 'data'),
    [Input('structure', 'value'),
     Input('bonding_options', 'value'),
     Input('color_schemes', 'value')])
def update_crystal_displayed(structure, bonding_option, color_scheme):

    structure = Structure.from_str(structure, fmt='json')

    crystal_json = MaterialsProjectStructureVis(structure,
                                                bonding_strategy=bonding_option,
                                                color_scheme=color_scheme).json

    return crystal_json


@app.callback(
    Output('viewer', 'visibilityOptions'),
    [Input('draw_options', 'values')])
def update_visible_elements(draw_options):
    return draw_options


if __name__ == '__main__':
    app.run_server(debug=True)
