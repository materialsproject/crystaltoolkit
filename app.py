import mp_viewer
import dash
import dash_core_components as dcc
import dash_html_components as html

from dash_react_graph_vis import GraphComponent

import numpy as np
import json
import functools

from base64 import urlsafe_b64decode, b64decode
from zlib import decompress
from urllib.parse import parse_qs
from uuid import uuid4
from tempfile import NamedTemporaryFile

from dash.dependencies import Input, Output, State

from monty.serialization import loadfn

from structure_vis_mp import MPVisualizer

from pymatgen import __version__ as pymatgen_version
from pymatgen import MPRester, Structure
from pymatgen.analysis.local_env import NearNeighbors

app = dash.Dash()
app.title = "MP Viewer"

app.scripts.config.serve_locally = True
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

mpr = MPRester()

DEFAULT_STRUCTURE = loadfn('default_structure.json')
DEFAULT_COLOR_SCHEME = 'VESTA'
DEFAULT_BONDING_METHOD = 'CrystalNN'
DEFAULT_GRAPH_OPTIONS = {
    'edges': {
        'smooth': {
            'type': 'dynamic'
        },
        'length': 250,
        'color': {
            'inherit': 'both'
        }
    },
    'physics': {
        'solver': 'forceAtlas2Based',
        'forceAtlas2Based': {
            'avoidOverlap': 1.0
        }
    }
}

AVAILABLE_BONDING_METHODS = [str(c.__name__)
                             for c in NearNeighbors.__subclasses__()]

# to help with readability, each component of the app is defined
# in a modular way below; these are all then included in the app.layout

LAYOUT_FORMULA_INPUT = html.Div([
    dcc.Input(id='input-box', type='text', placeholder='Enter a formula or mp-id'),
    html.Span(' '),
    html.Button('Load', id='button')
])

LAYOUT_UPLOAD_INPUT = html.Div([
    dcc.Upload(id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select File')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True)
])

LAYOUT_VISIBILITY_OPTIONS = html.Div([
    dcc.Checklist(
        id='visibility_options',
        options=[
            {'label': 'Auto Rotate', 'value': 'rotate'},
            {'label': 'Draw Atoms', 'value': 'atoms'},
            {'label': 'Draw Bonds', 'value': 'bonds'},
            {'label': 'Draw Polyhedra', 'value': 'polyhedra'},
            {'label': 'Draw Unit Cell', 'value': 'unitcell'}
        ],
        values=['atoms', 'bonds', 'unitcell']
    )])

LAYOUT_POLYHEDRA_VISIBILITY_OPTIONS = html.Div([
    html.Label("Choose Polyhedra"),
    dcc.Dropdown(
        id='polyhedra_visibility_options',
        options=[],
        multi=True
    )])

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

LAYOUT_DEVELOPER_TEXTBOX = html.Div([html.Label("Enter Structure JSON:"), dcc.Textarea(
    id='structure',
    placeholder='Developer console',
    value='',
    style={'width': '100%', 'overflow-y': 'scroll',
           'height': '400px', 'font-family': 'monospace'}
)])

LAYOUT_STRUCTURE_VIEWER = html.Div(id='viewer-container', children=[
    mp_viewer.StructureViewerComponent(
        id='viewer',
        data=MPVisualizer(DEFAULT_STRUCTURE,
                          bonding_strategy=DEFAULT_BONDING_METHOD,
                          color_scheme=DEFAULT_COLOR_SCHEME).json
    )], style={'height': '80vh', 'width': '100%', 'overflow': 'hidden'})

LAYOUT_GRAPH_VIEWER = html.Div(id='graph-container', children=[
    GraphComponent(
        id='graph',
        graph=MPVisualizer(DEFAULT_STRUCTURE,
                           bonding_strategy=DEFAULT_BONDING_METHOD,
                           color_scheme=DEFAULT_COLOR_SCHEME).graph_json,
        options=DEFAULT_GRAPH_OPTIONS
    )], style={'height': '80vh', 'width': '100%', 'overflow': 'hidden'})

# master app layout, includes layouts defined above
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(children=[LAYOUT_STRUCTURE_VIEWER, LAYOUT_GRAPH_VIEWER],
             id='preload', style={'display': 'none'}),
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
                    html.Div([
                        dcc.Tabs(
                            tabs=[
                                {'label': 'Structure', 'value': 'structure'},
                                {'label': 'Bonding Graph', 'value': 'graph'}
                            ],
                            value='structure',
                            id='tabs'),
                        html.Div(id='tab-output',
                                 style={'border-style': 'solid'})
                    ])
                ]
            ),
            html.Div(
                className='three columns',
                style={'text-align': 'left'},
                children=[
                    html.H2('MP Viewer'),
                    html.Div('Powered by pymatgen v{} and the Materials Project. '
                             'Contact mkhorton@lbl with bug reports.'.format(pymatgen_version)),
                    html.Hr(),
                    html.H5('Input'),
                    LAYOUT_FORMULA_INPUT,
                    html.Br(),
                    LAYOUT_UPLOAD_INPUT,
                    html.Br(),
                    html.Div(id='mp_text'),
                    html.Hr(),
                    html.H5('Options'),
                    LAYOUT_VISIBILITY_OPTIONS,
                    html.Br(),
                    LAYOUT_POLYHEDRA_VISIBILITY_OPTIONS,
                    html.Br(),
                    LAYOUT_BONDING_DROPDOWN,
                    html.Br(),
                    LAYOUT_COLOR_SCHEME_DROPDOWN,
                    html.Hr(),
                    html.H5('Developer'),
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
    [Input('url', 'search'),
     Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('upload-data', 'last_modified')]
)
def update_structure(search_query, list_of_contents, list_of_filenames, list_of_modified_dates):

    if list_of_contents is not None:

        # assume we only want the first input for now
        content_type, content_string = list_of_contents[0].split(',')
        decoded_contents = b64decode(content_string)
        name = list_of_filenames[0]

        # necessary to write to file so pymatgen's filetype detection can work
        with NamedTemporaryFile(suffix=name) as tmp:
            tmp.write(decoded_contents)
            tmp.flush()
            structure = Structure.from_file(tmp.name)

    elif search_query:
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

    return json.dumps(structure.as_dict(verbosity=0), indent=4)


@app.callback(
    Output('mp_text', 'children'),
    [Input('structure', 'value')]
)
def find_structure_on_mp(structure):
    structure = Structure.from_dict(json.loads(structure))
    mpids = mpr.find_structure(structure)
    if mpids:
        links = ", ".join(["[{}](https://materialsproject.org/materials/{})".format(mpid, mpid)
                           for mpid in mpids])
        return dcc.Markdown("This material is available on the Materials Project: {}".format(links))
    else:
        return ""


@app.callback(
    Output('polyhedra_visibility_options', 'options'),
    [Input('viewer', 'data')]
)
def update_available_polyhedra(viewer_data):
    available_polyhedra = viewer_data['polyhedra']['polyhedra_types']
    return [{'label': polyhedron, 'value': polyhedron} for polyhedron in available_polyhedra]

@app.callback(
    Output('polyhedra_visibility_options', 'value'),
    [Input('viewer', 'data')]
)
def update_default_polyhedra(viewer_data):
    return viewer_data['polyhedra']['polyhedra_types']

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
    Output('viewer', 'visibilityOptions'),
    [Input('visibility_options', 'values'),
     Input('polyhedra_visibility_options', 'value')])
def update_visible_elements(visibility_options, polyhedra_visibility_options):
    return visibility_options + polyhedra_visibility_options


@functools.lru_cache(1024)
def get_structure_viewer_json(structure, bonding_option=None,
                              color_scheme=None):

    # TODO: change to MontyDecoder ? so that we can load sg too
    structure = Structure.from_str(structure, fmt='json')

    mp_vis = MPVisualizer(structure, bonding_strategy=bonding_option, color_scheme=color_scheme)

    try:
        json = mp_vis.json
        json_error = False
    except Exception as e:
        json = str(e)
        json_error = True

    try:
        graph_json = mp_vis.graph_json
        graph_json_error = False
    except Exception as e:
        graph_json = str(e)
        graph_json_error = True

    return (json, json_error, graph_json, graph_json_error)

@app.callback(
    Output('tab-output', 'children'),
    [Input('tabs', 'value'),
     Input('structure', 'value'),
     Input('bonding_options', 'value'),
     Input('color_schemes', 'value')])
def display_content(value, structure, bonding_option, color_scheme):

    json, json_error, graph_json, graph_json_error = \
        get_structure_viewer_json(structure, bonding_option=bonding_option,
                                  color_scheme=color_scheme)

    if value == 'structure':
        if json_error:
            return html.Div(json, id='error',
                            style={'font-family':'monospace', 'color': 'red'})
        else:
            return html.Div(id='viewer-container', children=[
                mp_viewer.StructureViewerComponent(id='viewer', data=json)],
                            style={'height': '80vh', 'width': '100%', 'overflow': 'hidden'})
    elif value == 'graph':
        if graph_json_error:
            return html.Div(graph_json, id='error',
                            style={'font-family': 'monospace', 'color': 'red'})
        else:
            return html.Div(id='graph-container', children=[
                GraphComponent(id='graph', graph=graph_json, options=DEFAULT_GRAPH_OPTIONS)],
                            style={'height': '80vh', 'width': '100%', 'overflow': 'hidden'})



app.server.secret_key = str(uuid4())
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
