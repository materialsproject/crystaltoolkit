import mp_viewer
import dash
import dash_core_components as dcc
import dash_html_components as html

from dash_react_graph_vis import GraphComponent

import numpy as np
import json
import functools
import warnings
import random

from base64 import urlsafe_b64decode, b64decode
from zlib import decompress
from ast import literal_eval
from urllib.parse import parse_qsl, urlencode, urlparse
from uuid import uuid4
from tempfile import NamedTemporaryFile

from dash.dependencies import Input, Output, State

from monty.serialization import loadfn

from structure_vis_mp import MPVisualizer

from pymatgen import __version__ as pymatgen_version
from pymatgen import MPRester, Structure
from pymatgen.analysis.local_env import NearNeighbors
from pymatgen.util.string import unicodeify

from raven import Client

app = dash.Dash()
app.title = "MP Viewer"

app.scripts.config.serve_locally = True
app.css.append_css({'external_url': 'https://codepen.io/mkhorton/pen/aKmNxW.css'})
app.config['suppress_callback_exceptions'] = True

sentry = Client()

mpr = MPRester()

# TODO move this to css file
error_style = {'font-family':'monospace', 'color': 'rgb(211, 84, 0)',
               'text-align': 'left', 'font-size': '1.2em'}

DEFAULT_STRUCTURE = loadfn('default_structure.json')

DEFAULT_OPTIONS = {
    'display': 'structure',
    'range_a_min': 0,
    'range_b_min': 0,
    'range_c_min': 0,
    'range_a_max': 2,
    'range_b_max': 2,
    'range_c_max': 2,
    'atoms': True,
    'bonds': True,
    'polyhedra': True,
    'unitcell': True,
    'structure': None,
    'bonding_method': 'CrystalNN',
    'radius_method': 'average_ionic',
    'color_scheme': 'VESTA'
}

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

ALL_MPIDS = loadfn('all_mpids.json')

# to help with readability, each component of the app is defined
# in a modular way below which are then all then included in the app.layout

def layout_help(message):
    return html.Span([" \u003f\u20dd ", html.Span(message, className="tooltiptext")],
                    className="tooltip")

def layout_color(hex_code, label):
    c = tuple(int(hex_code[1:][i:i+2], 16) for i in (0, 2, 4))
    fontcolor = '#000000' if 1 - (c[0] * 0.299 + c[1] * 0.587
                                  + c[2] * 0.114) / 255 < 0.5 else '#ffffff'
    return html.Span(label, style={"width": "40px", "height": "40px", "line-height": "40px",
                                      "border-radius": "1px", "background": hex_code,
                                      "display": "inline-block",
                                   "font-weight": "bold",
                                   "color": fontcolor,
                                      "border": "1px solid black",
                                   "margin": "2px",
                                   "position": "relative",
                                   "text-align": "center",
    "top": "50%",
    "transform": "translateY(-50 %)"
    })

def layout_formula_input(value):
    return html.Div([
        html.Label('Load from Materials Project:'),
        dcc.Input(id='input-box', type='text', placeholder='Enter a formula or mp-id', value=value,
                  style={'float': 'left', 'width': 'auto'}),
        html.Span(' '),
        html.Button('Load', id='button')
    ])

@app.callback(
    Output('legend', 'children'),
    [Input('structure-viewer', 'data')]
)
def callback_color_legend(data):
    color_legend = data.get('color_legend', None)
    if color_legend:
        return html.Div([layout_color(hex_code, label) for hex_code, label in color_legend.items()])
    else:
        return []

LAYOUT_UPLOAD_INPUT = html.Div([
    html.Label('or load from a local file:'),
    dcc.Upload(id='upload-data',
        children=html.Div([
            html.Span(
            ['Drag and Drop or ',
            html.A('Select File')],
            id='upload-label'),
            layout_help("Upload any file that pymatgen supports, "
                        "including CIF and VASP file formats.")
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
        },
        multiple=True)
])

@app.callback(
    Output('upload-label', 'children'),
    [Input('upload-data', 'filename')],
    [State('upload-label', 'children')]
)
def callback_upload_label(filenames, current_upload_label):
    """
    Displays the filename of any uploaded data.
    """
    if filenames:
        return "{}".format(", ".join(filenames))
    else:
        return current_upload_label

@app.callback(
    Output('input-box', 'value'),
    [Input('upload-data', 'filename')],
    [State('input-box', 'value')]
)
def callback_query_label(filenames, current_query):
    """
    Clears the current query if data is uploaded from a file.
    """
    if filenames:
        return []
    else:
        return current_query


def layout_visibility_checklist(values):
    return html.Div([
        dcc.Checklist(
            id='visibility_options',
            options=[
                {'label': 'Show Atoms', 'value': 'atoms'},
                {'label': 'Show Bonds', 'value': 'bonds'},
                {'label': 'Show Polyhedra', 'value': 'polyhedra'},
                {'label': 'Show Unit Cell', 'value': 'unitcell'}
            ],
            values=values
        )
    ])


def layout_polyhedra_visibility_dropdown(value):
    default_options = [value] if value else []
    return html.Div([
    html.Label("Choose Polyhedra"),
    dcc.Dropdown(
        id='polyhedra_visibility_options',
        options=default_options,
        multi=True,
        value=value
    )])


def layout_bonding_method_dropdown(value):
    return html.Div([html.Span("Bonding Algorithm"),
                     layout_help("Determining whether a bond should be present between two atoms from geometry "
               "alone is not trivial. There are several algorithms available to do this in "
               "pymatgen, with CrystalNN recommended for periodic structures and JMolNN for "
               "molecules."), dcc.Dropdown(
        id='bonding_options',
        options=[
            {'label': method, 'value': method} for method in AVAILABLE_BONDING_METHODS
        ],
        value=value
)])


def layout_color_scheme_dropdown(value):
    default_color_schemes = ['VESTA', 'Jmol']
    if value not in default_color_schemes:
        default_color_schemes += value
    return html.Div([html.Span("Color Scheme"),
                     layout_help("JMol and VESTA color schemes have become de facto "
                                 "standards for visualizing atoms. It is also possible "
                                 "to color-code by any scalar site property that may be "
                                 "attached to the structure."),
                     dcc.Dropdown(
        id='color_schemes',
        options=[
            {'label': option, 'value': option} for option in default_color_schemes
        ],
        value=value
)])


def layout_structure_json_textarea(value):
    return html.Div([
        html.Div([
            html.Br(),
            html.Label("Edit crystal structure live as pymatgen structure JSON:"),
            dcc.Textarea(
                id='structure',
                placeholder='Paste JSON from a pymatgen Structure object here,'
                            'using output from Structure.to_json()',
                value='',
                style={'overflow-y': 'scroll', 'width': '100%',
                       'height': '80vh', 'font-family': 'monospace'})
        ], className="six columns"),
        html.Div([
            html.Br(),
            html.Label("", id='structure-highlighted-error', style=error_style),
            dcc.SyntaxHighlighter(
                id='structure-highlighted',
                children="",
                language='javascript',
                showLineNumbers=True,
                customStyle={'overflow-y': 'scroll', 'height': '80vh'})
        ], className="six columns")
    ], className="row")

@app.callback(
    Output('structure-highlighted', 'children'),
    [Input('structure', 'value')]
)
def callback_highlighted_json(structure_json):
    return str(structure_json)

@app.callback(
    Output('structure-highlighted-error', 'children'),
    [Input('structure', 'value')]
)
def callback_highlighted_json_error(structure_json):
    try:
        structure_dict = json.loads(structure_json)
        Structure.from_dict(structure_dict)
        return ""
    except Exception as e:
        return "Invalid JSON: {}".format(e)


def layout_structure_viewer(data, visibilityOptions):
    return html.Div(id='viewer-container', children=[
        mp_viewer.StructureViewerComponent(
            id='structure-viewer',
            data=data,
            visibilityOptions=visibilityOptions
        )], style={'height': '80vh', 'width': '100%', 'overflow': 'hidden'})


def layout_graph_viewer(graph):
    return html.Div(id='graph-container', children=[
        GraphComponent(
            id='graph',
            graph=graph,
            options=DEFAULT_GRAPH_OPTIONS
        )], style={'height': '80vh', 'width': '100%', 'overflow': 'hidden'})


def layout_view_range(value):
    return html.Div([html.Label("View Range"),
                     dcc.Slider(
                         id='view-range', min=0, max=3, step=1,
                         value=value,
                         marks={i: str(i) for i in range(4)}
                     )])


@app.callback(
    Output('color_schemes', 'options'),
    [Input('structure', 'value')])
def callback_structure_viewer_to_color_options(structure_json):
    """
    Callback to update the available color scheme options
    (this is dynamic based on the structure site properties
    available).
    """
    # TODO: rewrite from MPStructureVisualizer output

    default_options = ('VESTA', 'Jmol')
    available_options = list(default_options)

    structure = Structure.from_dict(json.loads(structure_json))
    for key, props in structure.site_properties.items():
        props = np.array(props)
        # "coordination_no" from MPRester should be deprecated ...
        if len(props.shape) == 1 and key != "coordination_no":
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
    Output('url', 'search'),
    [Input('button', 'n_clicks')],
    [State('input-box', 'value')]
)
def callback_update_query_string(input_formula_mpid_nclicks, input_formula_mpid):

    query = {}

    if input_formula_mpid:
        query['query'] = input_formula_mpid

    formatted_query = "?{}".format(urlencode(query))

    if formatted_query != "?":
        return formatted_query
    else:
        return ""


@app.callback(
    Output('structure', 'value'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('upload-data', 'last_modified'),
     Input('url', 'search')]
)
def callback_update_structure(list_of_contents, list_of_filenames, list_of_modified_dates,
                              search_query):

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
        search_query = dict(parse_qsl(search_query[1:]))
        if 'structure' in search_query:
            payload = search_query['structure'][0]
            payload = urlsafe_b64decode(payload)
            payload = decompress(payload)
            structure = Structure.from_str(payload, fmt='json')
        else:
            structure = mpr.get_structures(search_query['query'])[0]
    else:
        random_mpid = random.choice(ALL_MPIDS)
        try:
            structure = mpr.get_structure_by_material_id(random_mpid)
        except:
            structure = DEFAULT_STRUCTURE

    return json.dumps(structure.as_dict(verbosity=0), indent=4)


@app.callback(
    Output('mp_text', 'children'),
    [Input('structure', 'value')]
)
def callback_structure_to_mp_link(structure):
    structure = Structure.from_dict(json.loads(structure))
    mpids = mpr.find_structure(structure)
    formula = unicodeify(structure.composition.reduced_formula)
    if mpids:
        links = ", ".join(["[{}](https://materialsproject.org/materials/{})".format(mpid, mpid)
                           for mpid in mpids])
        return dcc.Markdown("{} is available on the Materials Project: {}".format(formula, links))
    else:
        return ""


@app.callback(
    Output('polyhedra_visibility_options', 'options'),
    [Input('structure-viewer', 'data')]
)
def callback_structure_viewer_to_polyhedra_options(viewer_data):
    available_polyhedra = viewer_data['polyhedra']['polyhedra_types']
    return [{'label': polyhedron, 'value': polyhedron} for polyhedron in available_polyhedra]

@app.callback(
    Output('polyhedra_visibility_options', 'value'),
    [Input('structure-viewer', 'data')]
)
def callback_structure_viewer_to_default_polyhedra(viewer_data):
    return viewer_data['polyhedra']['polyhedra_types']

@app.callback(
    Output('structure-viewer', 'visibilityOptions'),
    [Input('visibility_options', 'values'),
     Input('polyhedra_visibility_options', 'value')])
def callback_update_visible_elements(visibility_options, polyhedra_visibility_options):
    polyhedra_visibility_options = polyhedra_visibility_options or []
    return visibility_options + polyhedra_visibility_options


@functools.lru_cache(1024)
def get_structure_viewer_json(structure, bonding_option=None,
                              color_scheme=None,
                              display_repeats=((0, 2), (0, 2), (0, 2))):

    # TODO: change to MontyDecoder ? so that we can load sg too
    structure = Structure.from_str(structure, fmt='json')


    mp_vis = MPVisualizer(structure,
                          bonding_strategy=bonding_option,
                          color_scheme=color_scheme,
                          display_repeats=display_repeats)

    json = mp_vis.json
    try:
        json = mp_vis.json
    except Exception as e:
        sentry.captureException()
        warnings.warn(e)
        json = {'error': str(e)}

    try:
        graph_json = mp_vis.graph_json
    except Exception as e:
        sentry.captureException()
        warnings.warn(e)
        graph_json = {'error': str(e)}

    return (json, graph_json)

@app.callback(
    Output('tab-output-graph', 'style'),
    [Input('tabs', 'value')]
)
def callback_tab_output_graph(tab):
    if tab == 'graph':
        return {}
    else:
        return {'display': 'none'}

@app.callback(
    Output('tab-output-json', 'style'),
    [Input('tabs', 'value')]
)
def callback_tab_output_json(tab):
    if tab == 'json':
        return {}
    else:
        return {'display': 'none'}

@app.callback(
    Output('tab-output-structure', 'style'),
    [Input('tabs', 'value')]
)
def callback_tab_output_structure(tab):
    if tab == 'structure':
        return {}
    else:
        return {'display': 'none'}


@app.callback(
     Output('structure-viewer', 'data'),
     [Input('structure', 'value'),
      Input('bonding_options', 'value'),
      Input('color_schemes', 'value'),
      Input('view-range', 'value')]
)
def callback_structure_viewer_data(structure, bonding_option, color_scheme, range):

    range = (0, range)
    display_repeats = (range, range, range)

    json, graph_json = \
        get_structure_viewer_json(structure, bonding_option=bonding_option,
                                  color_scheme=color_scheme, display_repeats=display_repeats)

    # TODO parse error

    return json

@app.callback(
    Output('graph', 'graph'),
    [Input('structure', 'value'),
     Input('bonding_options', 'value'),
     Input('color_schemes', 'value'),
     Input('view-range', 'value')]
)
def callback_structure_viewer_data(structure, bonding_option, color_scheme, range):

    range = (0, range)
    display_repeats = (range, range, range)

    json, graph_json = \
        get_structure_viewer_json(structure, bonding_option=bonding_option,
                                  color_scheme=color_scheme, display_repeats=display_repeats)

    # TODO parse error

    return graph_json



def master_layout(options):

    options = dict(options)

    mpid_formula = options.get('query', random.choice(ALL_MPIDS))

    visibility_values = [val for val
                         in ['atoms', 'bonds',
                             'unitcell', 'polyhedra']
                         if options[val]]


    view_range_value = options['range_a_max']
    bonding_method_value = options['bonding_method']
    color_scheme_value = options['color_scheme']

    try:
        structure = mpr.get_structure_by_material_id(mpid_formula)
    except:
        structure = DEFAULT_STRUCTURE # TODO replace, no default

    display_repeats = ((options['range_a_min'], options['range_a_max']),
                       (options['range_b_min'], options['range_b_max']),
                       (options['range_c_min'], options['range_c_max']))

    vis = MPVisualizer(structure,
                       bonding_strategy=options['bonding_method'],
                       color_scheme=options['color_scheme'],
                       display_repeats=display_repeats)

    data = vis.json
    graph = vis.graph_json
    json_value = vis.structure.to_json()

    structure_tab = layout_structure_viewer(data, visibility_values)
    graph_tab = layout_graph_viewer(graph)
    json_tab = layout_structure_json_textarea(json_value)

    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Br(),
        html.Div(
            className='row',
            children=[
                html.Div(className='one columns'),
                html.Div(
                    className='seven columns',
                    children=[
                        html.Div([
                            dcc.Tabs(
                                tabs=[
                                    {'label': 'Structure', 'value': 'structure'},
                                    {'label': 'Bonding Graph', 'value': 'graph'},
                                    {'label': 'JSON', 'value': 'json'}
                                ],
                                value=options['display'],
                                id='tabs'),
                            html.Div([structure_tab],
                                     id='tab-output-structure'),
                            html.Div([graph_tab],
                                     id='tab-output-graph'),
                            html.Div([json_tab],
                                     id='tab-output-json'),
                            html.Hr(),
                            html.Div('Powered by pymatgen v{}. '
                                     'Contact mkhorton@lbl with bug reports. '
                                     'Currently only periodic structures supported, molecules '
                                     'coming soon. Known bugs: initial loading slow, some minor '
                                     'visual artifacts including lighting.'.format(
                                pymatgen_version),
                                     style={'text-align': 'left'})
                        ])
                    ]
                ),
                html.Div(
                    className='three columns',
                    style={'text-align': 'left'},
                    children=[
                        html.H5('Input'),
                        layout_formula_input(mpid_formula),
                        html.Br(),
                        LAYOUT_UPLOAD_INPUT,
                        html.Br(),
                        html.Div(id='mp_text'),
                        html.Hr(),
                        html.H5('Options'),
                        html.Br(),
                        layout_visibility_checklist(visibility_values),
                        html.Br(),
                        layout_polyhedra_visibility_dropdown(None),
                        html.Br(),
                        layout_view_range(view_range_value),
                        html.Br(),
                        layout_bonding_method_dropdown(bonding_method_value),
                        html.Br(),
                        layout_color_scheme_dropdown(color_scheme_value),
                        html.Br(),
                        html.Div(children=html.Div([layout_color(hex_code, label)
                                                    for hex_code, label in data['color_legend'].items()]),
                                 id="legend")
                    ]
                ),
                html.Div(className='one columns')
            ])
    ])


app.server.secret_key = str(uuid4())
server = app.server

app.layout = master_layout(DEFAULT_OPTIONS)

if __name__ == '__main__':
    app.run_server(debug=True)
