import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import dash_table_experiments as dt

from mp_dash_components.converters.structure import StructureIntermediateFormat
from mp_dash_components import StructureViewerComponent, GraphComponent
from mp_dash_components.layouts.misc import help_layout

from pymatgen.core import Structure
from pymatgen.ext.matproj import MPRester

from itertools import combinations_with_replacement, chain

from tempfile import NamedTemporaryFile
from base64 import urlsafe_b64decode, b64decode
from json import dumps, loads
from zlib import decompress
from urllib.parse import parse_qsl
from random import choice

import numpy as np


import datetime, time
def _get_time():
    # TODO: this seems bad, used to display 'latest' structure
    return time.mktime(datetime.datetime.now().timetuple())

def dump_structure(structure):
    d = structure.as_dict(verbosity=0)
    d['_created_at'] = _get_time()
    return dumps(d, indent=4)


def structure_layout(structure, app,
                     structure_viewer_id="structure-viewer", **kwargs):

    def generate_layout(structure, structure_viewer_id):

        if isinstance(structure, Structure):
            structure_dict = structure.as_dict(verbosity=0)
            intermediate_json = StructureIntermediateFormat(structure).json
            return StructureViewerComponent(id=structure_viewer_id,
                                            value=structure_dict,
                                            data=intermediate_json,
                                            **kwargs)
        else:
            raise ValueError

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(structure_viewer_id, 'data'),
            [Input(structure_viewer_id, 'generationOptions'),
             Input(structure_viewer_id, 'value')]
        )
        def generate_visualization_data(generationOptions, structure):
            generationOptions = generationOptions or {}
            structure = Structure.from_dict(structure)
            intermediate_json = StructureIntermediateFormat(structure, **generationOptions).json
            return intermediate_json

    layout = generate_layout(structure, structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout


def structure_view_options_layout(structure_viewer_id, app,
                                  polyhedra_options=False,
                                  bond_options=False, **kwargs):
    """
    :param structure_id: id of component that contains viewer data
    :param app: app to set up callbacks
    :param kwargs: kwargs to pass to dcc.Checklist
    :return: a Dash layout
    """

    def generate_layout(structure_viewer_id):

        view_options = dcc.Checklist(
            id=f'{structure_viewer_id}_visibility_options',
            options=[
                {'label': 'Show Atoms', 'value': 'atoms'},
                {'label': 'Show Bonds', 'value': 'bonds'},
                {'label': 'Show Polyhedra', 'value': 'polyhedra'},
                {'label': 'Show Unit Cell', 'value': 'unitcell'}
            ],
            values=['atoms', 'bonds', 'unitcell'],
            **kwargs
        )

        return view_options

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(structure_viewer_id, 'visibilityOptions'),
            [Input(f'{structure_viewer_id}_visibility_options', 'values')],
            [State(f'{structure_viewer_id}_visibility_options', 'options')]
        )
        def update_view_options(view_options, all_options):
            return {opt['value']: (opt['value'] in view_options) for opt in all_options}

    layout = generate_layout(structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout


def structure_bonding_algorithm(structure_viewer_id, app, **kwargs):

    def generate_layout(structure_viewer_id):

        nn_mapping = {
            "CrystalNN": "CrystalNN",
            "Custom Bonds": "CutOffDictNN",
            "Jmol Bonding": "JMolNN",
            "Minimum Distance (10% tolerance)": "MinimumDistanceNN",
            "O'Keeffe's Algorithm": "MinimumOKeeffeNN",
            "Hoppe's ECoN Algorithm": "EconNN",
            "Brunner's Reciprocal Algorithm": "BrunnerNN_reciprocal"
        }

        options = dcc.Dropdown(
            options=[
                {'label': k, 'value': v} for k, v in nn_mapping.items()
            ],
            value='BrunnerNN_reciprocal',
            id=f'{structure_viewer_id}_bonding_algorithm'
        )

        custom_cutoffs = html.Div([
            html.Br(),
            dt.DataTable(
                rows=[{'A': None, 'B': None, 'A-B /Å': None}],
                row_selectable=False,
                filterable=False,
                sortable=True,
                editable=True,
                selected_row_indices=[],
                id=f'{structure_viewer_id}_bonding_algorithm_custom_cutoffs'
            ),
            html.Br()
        ],
            id=f'{structure_viewer_id}_bonding_algorithm_custom_cutoffs_container',
            style={'display': 'none'})

        generation_options_hidden_div = html.Div(id=f'{structure_viewer_id}_bonding_algorithm_generation_options',
                                                 style={'display': 'none'})

        return html.Div([html.Label('Bonding Algorithm'), options, custom_cutoffs, generation_options_hidden_div])

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(f'{structure_viewer_id}_bonding_algorithm_generation_options', 'value'),
            [Input(f'{structure_viewer_id}_bonding_algorithm', 'value'),
             Input(f'{structure_viewer_id}_bonding_algorithm_custom_cutoffs', 'rows')]
        )
        def update_structure_viewer_data(bonding_algorithm, custom_cutoffs_rows):
            options = {'bonding_strategy': bonding_algorithm,
                       'bonding_strategy_kwargs': None}
            if bonding_algorithm == 'CutOffDictNN':
                # this is not the format CutOffDictNN expects (since that is not JSON
                # serializable), so we store as a list of tuples instead
                # TODO: make CutOffDictNN args JSON serializable
                custom_cutoffs = [(row['A'], row['B'], float(row['A-B /Å']))
                                  for row in custom_cutoffs_rows]
                options['bonding_strategy_kwargs'] = {'cut_off_dict': custom_cutoffs}
            return options

        @app.callback(
            Output(f'{structure_viewer_id}_bonding_algorithm_custom_cutoffs', 'rows'),
            [Input(structure_viewer_id, 'value')]
        )
        def update_custom_bond_options(structure):
            structure = Structure.from_dict(structure)
            # can't use type_of_specie because it doesn't work with disordered structures
            species = set(map(str, chain.from_iterable([list(c.keys())
                                                        for c in structure.species_and_occu])))
            rows = [{'A': combination[0], 'B': combination[1], 'A-B /Å': 0}
                    for combination in combinations_with_replacement(species, 2)]
            return rows

        @app.callback(
            Output(f'{structure_viewer_id}_bonding_algorithm_custom_cutoffs_container', 'style'),
            [Input(f'{structure_viewer_id}_bonding_algorithm', 'value')]
        )
        def show_hide_custom_bond_options(bonding_algorithm):
            if bonding_algorithm == 'CutOffDictNN':
                return {}
            else:
                return {'display': 'none'}

    layout = generate_layout(structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout


def structure_color_scheme_choice(structure_viewer_id, app, **kwargs):

    default_color_schemes = ['Jmol', 'VESTA']

    def generate_layout(structure_viewer_id):

        color_schemes = html.Div([
            html.Span("Color Scheme"),
            help_layout("JMol and VESTA color schemes have become de facto "
                        "standards for visualizing atoms. It is also possible "
                        "to color-code by any scalar site property that may be "
                        "attached to the structure with pymatgen."),
            dcc.Dropdown(
                id=f'{structure_viewer_id}_color_scheme_choice',
                options=[
                    {'label': option, 'value': option}
                    for option in default_color_schemes
                ],
                value=default_color_schemes[0]
            )
        ])

        generation_options_hidden_div = html.Div(id=f'{structure_viewer_id}_color_scheme_choice_generation_options',
                                                 style={'display': 'none'})

        return html.Div([color_schemes, generation_options_hidden_div])

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(f'{structure_viewer_id}_color_scheme_choice', 'options'),
            [Input(structure_viewer_id, 'value')]
        )
        def update_color_options(structure):
            # TODO: this will be a little inefficient, should find a smarter way to pass options

            structure = Structure.from_dict(structure)
            available_options = default_color_schemes.copy()

            for key, props in structure.site_properties.items():
                props = np.array(props)
                # "coordination_no" from MPRester should be deprecated ...
                if len(props.shape) == 1 and key != "coordination_no":
                    # can't color-code for vectors,
                    # should draw arrows for these instead
                    available_options.append(key)

            def pretty_rewrite(option):
                if option not in default_color_schemes:
                    return "Site property: {}".format(option)
                else:
                    return option

            return [
                {'label': pretty_rewrite(option), 'value': option}
                for option in available_options
            ]

        @app.callback(
            Output(f'{structure_viewer_id}_color_scheme_choice_generation_options', 'value'),
            [Input(f'{structure_viewer_id}_color_scheme_choice', 'value')]
        )
        def update_color_choice(value):
            return {'color_scheme': value}

    layout = generate_layout(structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout


def structure_view_range(structure_viewer_id, app, **kwargs):

    def generate_layout(structure_viewer_id):

        view_range = html.Div([
            html.Label("View Range"),
            dcc.RadioItems(options=[
                {'label': 'Display Single Unit Cell', 'value': 'single'},
                {'label': 'Display Expanded Unit Cell', 'value': 'expanded'}
            ], value='expanded', id=f'{structure_viewer_id}_view_range')
        ])

        generation_options_hidden_div = html.Div(id=f'{structure_viewer_id}_view_range_generation_options',
                                                 style={'display': 'none'})

        return html.Div([view_range, generation_options_hidden_div])

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(f'{structure_viewer_id}_view_range_generation_options', 'value'),
            [Input(f'{structure_viewer_id}_view_range', 'value')],
            [State(structure_viewer_id, 'value')]
        )
        def update_color_choice(view_range, structure):

            if view_range == 'expanded':
                if len(Structure.from_dict(structure)) <= 12:
                    range = (0, 2.99)
                else:
                    range = (0, 1.99)
            else:
                range = (0, 0.99)

            display_repeats = (range, range, range)

            return {'display_repeats': display_repeats}

    layout = generate_layout(structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout


def structure_import_from_file(structure_id, app, **kwargs):

    def generate_layout(structure_id):

        upload = html.Div([
            html.Label('Load from a local file:'),
            dcc.Upload(id=f'{structure_id}_upload_data',
                       children=html.Div([
                           html.Span(
                               ['Drag and Drop or ',
                                html.A('Select File')],
                               id=f'{structure_id}_upload_label'),
                           help_layout("Upload any file that pymatgen supports, "
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

        hidden_structure_div = html.Div(id=structure_id, style={'display': 'none'})

        return html.Div([upload, hidden_structure_div])

    def generate_callbacks(structure_id, app):

        @app.callback(
          Output(f'{structure_id}_upload_label', 'children'),
           [Input(f'{structure_id}_upload_data', 'filename')],
           [State(f'{structure_id}_upload_label', 'children')]
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
             Output(structure_id, 'children'),
             [Input(f'{structure_id}_upload_data', 'contents'),
              Input(f'{structure_id}_upload_data', 'filename'),
              Input(f'{structure_id}_upload_data', 'last_modified')]
        )
        def callback_update_structure(list_of_contents, list_of_filenames,
                                        list_of_modified_dates):

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

                return dump_structure(structure)

            else:

                return None

    layout = generate_layout(structure_id)
    generate_callbacks(structure_id, app)

    return layout


def structure_import_from_url(url_id, app, **kwargs):

    def generate_layout(url_id):
        hidden_structure_div = html.Div(id=f'{url_id}_structure', style={'display': 'none'})
        hidden_mpid_div = html.Div(id=f'{url_id}_mpid', style={'display': 'none'})
        return html.Div([hidden_structure_div, hidden_mpid_div], style={'display': 'none'})

    def generate_callbacks(url_id, app):

        @app.callback(
            Output(f'{url_id}_structure', 'children'),
            [Input(url_id, 'search')]
        )
        def load_structure_from_url(search_query):
            if (search_query is None) or (search_query is ""):
                raise PreventUpdate
            # strip leading ? from query, and parse into dict
            search_query = dict(parse_qsl(search_query[1:]))
            if 'structure' in search_query:
                payload = search_query['structure']
                payload = urlsafe_b64decode(payload)
                payload = decompress(payload).decode('ascii')
                structure = Structure.from_dict(loads(payload))
                return dump_structure(structure)
            elif 'query' in search_query:
                with MPRester() as mpr:
                    structure = mpr.get_structures(search_query['query'])[0]
                    return dump_structure(structure)
            else:
                raise PreventUpdate

        @app.callback(
            Output(f'{url_id}_mpid', 'children'),
            [Input(url_id, 'search')]
        )
        def update_mpid(search_query):
            if (search_query is None) or (search_query is ""):
                raise PreventUpdate
            # strip leading ? from query, and parse into dict
            search_query = dict(parse_qsl(search_query[1:]))
            if 'query' in search_query:
                return search_query['query']
            else:
                raise PreventUpdate

    layout = generate_layout(url_id)
    generate_callbacks(url_id, app)

    return layout


def structure_import_from_mpid(structure_id, app, **kwargs):

    def generate_layout(structure_id):
        hidden_structure_div = html.Div(id=structure_id, style={'display': 'none'})

        mpid_input = html.Div([
            html.Label('Load from Materials Project:'),
            dcc.Input(id=f'{structure_id}_mpid_input', type='text', placeholder='Enter a formula or mp-id',
                      value='',
                      style={'float': 'left', 'width': 'auto'}),
            html.Span(' '),
            html.Button('Load', id=f'{structure_id}_mpid_input_button'),
            html.Br(),
            html.Div(dcc.Dropdown(id=f'{structure_id}_choose'), id=f'{structure_id}_choose_container',
                     style={'display': 'none'})
        ])

        return html.Div([hidden_structure_div, mpid_input])

    def generate_callbacks(structure_id, app):

        @app.callback(
            Output(structure_id, 'children'),
            [Input(f'{structure_id}_mpid_input_button', 'n_clicks'),
             Input(f'{structure_id}_choose', 'value')],
            [State(f'{structure_id}_mpid_input', 'value')]
        )
        def load_structure_from_query(n_clicks, choice, query):
            if (query is None) or (query is ""):
                raise PreventUpdate
            with MPRester() as mpr:
                structures = mpr.get_structures(query)
            if structures:
                if choice:
                    structure = structures[choice]
                else:
                    structure = structures[0]
                return dump_structure(structure)
            else:
                raise PreventUpdate

        @app.callback(
            Output(f'{structure_id}_choose', 'options'),
            [Input(f'{structure_id}_mpid_input_button', 'n_clicks')],
            [State(f'{structure_id}_mpid_input', 'value')]
        )
        def load_structure_choices(n_clicks, query):
            if (query is None) or (query is ""):
                raise PreventUpdate
            with MPRester() as mpr:
                structures = mpr.get_structures(query)
            if structures:
                return [{
                    'label': f'{structure.composition.reduced_formula} {structure.get_space_group_info()[0]}',
                    'value': idx
                } for idx, structure in enumerate(structures)]

        @app.callback(
            Output(f'{structure_id}_choose', 'value'),
            [Input(f'{structure_id}_mpid_input_button', 'n_clicks')],
            [State(f'{structure_id}_mpid_input', 'value')]
        )
        def load_structure_choices(n_clicks, query):
            if (query is None) or (query is ""):
                raise PreventUpdate
            with MPRester() as mpr:
                structures = mpr.get_structures(query)
            if structures:
                return 0
            else:
                return None

        @app.callback(
            Output(f'{structure_id}_choose_container', 'style'),
            [Input(f'{structure_id}_choose', 'value')],
        )
        def load_structure_choices(value):
            if type(value) == int:
                return {}
            else:
                return {'display': 'none'}

    layout = generate_layout(structure_id)
    generate_callbacks(structure_id, app)

    return layout


def structure_random_input(structure_id, app, mpid_list, **kwargs):

    def generate_layout(structure_id):

        hidden_structure_div = html.Div(id=structure_id, style={'display': 'none'})
        random_button = html.Button('🎲', id=f'{structure_id}_random_button')

        return html.Div([html.Label('Load random structure:'), random_button, hidden_structure_div])

    def generate_callbacks(structure_id, app):

        @app.callback(
            Output(structure_id, 'children'),
            [Input(f'{structure_id}_random_button', 'n_clicks')]
        )
        def get_random_structure(n_clicks):
            if n_clicks:
                mpid = choice(mpid_list)
                with MPRester() as mpr:
                    structure = mpr.get_structure_by_material_id(mpid)
                return dump_structure(structure)
            else:
                raise PreventUpdate

    layout = generate_layout(structure_id)
    generate_callbacks(structure_id, app)

    return layout

def structure_graph(structure_viewer_id, app, **kwargs):

    default_graph_options = {
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

    def generate_layout(structure_viewer_id):

        graph = GraphComponent(id=f'{structure_viewer_id}_bonding_graph',
                               graph={},
                               options=default_graph_options)

        return graph

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(f'{structure_viewer_id}_bonding_graph', 'graph'),
            [Input(structure_viewer_id, 'value'),
             Input(structure_viewer_id, 'generationOptions')]
        )
        def update_graph(structure, generationOptions):
            generationOptions = generationOptions or {}
            structure = Structure.from_dict(structure)
            graph_json = StructureIntermediateFormat(structure, **generationOptions).graph_json
            return graph_json

    layout = generate_layout(structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout


def json_editor(structure_id, app, initial_structure=None, structure_viewer_id=None, **kwargs):

    if isinstance(initial_structure, Structure):
        initial_value = dumps(initial_structure.as_dict(verbosity=0), indent=4)
    else:
        initial_value = ""

    def generate_layout(structure_id):

        # TODO move this to css file
        error_style = {'font-family': 'monospace', 'color': 'rgb(211, 84, 0)',
                       'text-align': 'left', 'font-size': '1.2em'}

        editor = html.Div([
            html.Div([
                html.Br(),
                html.Label("Edit crystal structure live as pymatgen structure JSON "
                           "(in Python, use Structure.to_json() to generate):"),
                dcc.Textarea(
                    id=structure_id,
                    placeholder='Paste JSON from a pymatgen Structure object here, '
                                'using output from Structure.to_json()',
                    value=initial_value,
                    style={'overflow-y': 'scroll', 'width': '100%',
                           'height': '70vh',
                           'max-height': '80vh', 'font-family': 'monospace',
                           'min-height': '100px'})
           ], className="six columns"),
           html.Div([
               html.Br(),
               html.Label("", id=f'{structure_id}-highlighted-error', style=error_style),
               dcc.SyntaxHighlighter(
                   id=f'{structure_id}-highlighted',
                   children="",
                   language='javascript',
                   showLineNumbers=True,
                   customStyle={'overflow-y': 'scroll', 'height': '70vh', 'min-height': '100px',
                                'max-height': '80vh'})
           ], className="six columns")
        ], className="row")

        return html.Div([editor], style={'padding': '10px'})

    def generate_callbacks(structure_id, all):

        @app.callback(
            Output(f'{structure_id}-highlighted', 'children'),
            [Input(structure_id, 'value')]
        )
        def callback_highlighted_json(structure):
            try:
                structure = loads(structure)
                return dumps(Structure.from_dict(structure).as_dict(verbosity=0), indent=4)
            except:
                raise PreventUpdate

        @app.callback(
            Output(f'{structure_id}-highlighted-error', 'children'),
            [Input(structure_id, 'value')]
        )
        def callback_highlighted_json_error(structure):
            try:
                structure = loads(structure)
                Structure.from_dict(structure)
                return ""
            except Exception as e:
                try:
                    if "None" in structure:
                        error_msg = "Use Structure.to_json() to generate JSON, not Structure.as_dict(" \
                                    "). "
                    elif len(structure) > 0 and structure[0] == "'":
                        error_msg = "Do not include initial or final quotes when pasting JSON. "
                    else:
                        error_msg = str(e)
                except:
                    error_msg = str(e)
            return error_msg

        if structure_viewer_id:
            @app.callback(
                Output(structure_viewer_id, 'value'),
                [Input(structure_id, 'value')]
            )
            def update_displayed_structure(structure):
                try:
                    structure = Structure.from_dict(loads(structure))
                    return structure.as_dict(verbosity=0)
                except:
                    raise PreventUpdate

    layout = generate_layout(structure_id)
    generate_callbacks(structure_id, app)

    return layout


def structure_inspector(structure_id, app, **kwargs):

    def generate_layout(structure_id):
        return dcc.Markdown(id=f'{structure_id}_inspector')

    def generate_callbacks(structure_id, app):

        @app.callback(
            Output(f'{structure_id}_inspector', 'children'),
            [Input(structure_id, 'value')]
        )
        def analyze_structure(structure):
            # TODO: in some places, structure stored as text, in other places as dict
            structure = Structure.from_dict(structure)
            text = []

            spacegroup = structure.get_space_group_info()
            text.append("Space group: {} ({})".format(spacegroup[0], spacegroup[1]))

            with MPRester() as mpr:
                mpids = mpr.find_structure(structure)
            if mpids:
                links = ", ".join(
                    ["[{}](https://materialsproject.org/materials/{})".format(mpid, mpid)
                     for mpid in mpids])
                text.append("This material is available on the Materials Project: {}".format(links))

            text = "\n\n".join(text)

            return text


    layout = generate_layout(structure_id)
    generate_callbacks(structure_id, app)

    return layout


def structure_screenshot_button(structure_viewer_id, app, **kwargs):
    """
    BETA!
    :param structure_id: id of component that contains viewer data
    :param app: app to set up callbacks
    :return: a Dash layout
    """

    def generate_layout(structure_viewer_id):

        button = html.Button('Take Screenshot',
                            id=f'{structure_viewer_id}_screenshot_button')
        download_link = html.A('Download Screenshot (currently non-functional, see console)',
                               id=f'{structure_viewer_id}_screenshot_download_link')

        return html.Div([button, download_link])

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(structure_viewer_id, 'n_screenshot_requests'),
            [Input(f'{structure_viewer_id}_screenshot_button', 'n_clicks')],
            [State(structure_viewer_id, 'n_screenshot_requests')]
        )
        def generate_screenshot(n_clicks, current_n_screenshot_requests):
            if current_n_screenshot_requests:
                return current_n_screenshot_requests+1
            else:
                return 1

        @app.callback(
            Output(f'{structure_viewer_id}_screenshot_download_link', 'href'),
            [Input(structure_viewer_id, 'screenshot')]
        )
        def return_screenshot(screenshot):
            return screenshot

    layout = generate_layout(structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout


def structure_viewer_header(structure_viewer_id, app, **kwargs):

    def generate_layout(structure_viewer_id):

        title = html.H1(id=f'{structure_viewer_id}_title', style={'display': 'inline-block'})

        return title

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(f'{structure_viewer_id}_title', 'children'),
            [Input(structure_viewer_id, 'value')]
        )
        def update_title(structure):
            structure = Structure.from_dict(structure)
            return structure.composition.reduced_formula

    layout = generate_layout(structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout


def structure_viewer_legend(structure_viewer_id, app, **kwargs):

    def layout_color(hex_code, label):
        c = tuple(int(hex_code[1:][i:i + 2], 16) for i in (0, 2, 4))
        fontcolor = '#000000' if 1 - (c[0] * 0.299 + c[1] * 0.587
                                      + c[2] * 0.114) / 255 < 0.5 else '#ffffff'
        return html.Span(label, style={"min-width": "40px", "width": "auto", "height": "40px",
                                       "line-height": "40px",
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

    def generate_layout(structure_viewer_id):

        legend = html.Div(id=f'{structure_viewer_id}_legend')

        return legend # html.Div([html.Label('Legend'), legend])

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(f'{structure_viewer_id}_legend', 'children'),
            [Input(structure_viewer_id, 'data')]
        )
        def update_legend(data):
            # TODO: this is pretty inefficient! update ...
            return [layout_color(hex_code, label)
                    for hex_code, label in data.get('color_legend', {}).items()]

    layout = generate_layout(structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout