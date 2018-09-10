import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import dash_table_experiments as dt

from mp_dash_components.converters.structure import StructureIntermediateFormat
from mp_dash_components import StructureViewerComponent, GraphComponent
from mp_dash_components.layouts.misc import help_layout

from pymatgen.core import Structure

from itertools import combinations_with_replacement

from tempfile import NamedTemporaryFile
from base64 import b64decode
from json import dumps, loads

import numpy as np


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
            "CrystalNN (default)": "CrystalNN",
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
            value='CrystalNN',
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
            species = map(str, structure.types_of_specie)
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
                    structure.append(key)

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

        hidden_structure_div = html.Div(style={'display': 'none'})

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
             Output(structure_id, 'value'),
             [Input('upload-data', 'contents'),
              Input('upload-data', 'filename'),
              Input('upload-data', 'last_modified')]
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

                return structure.as_dict(verbosity=0)

            else:

                return None

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


def json_editor(structure_id, app, **kwargs):

    def generate_layout(structure_id):

        # TODO move this to css file
        error_style = {'font-family': 'monospace', 'color': 'rgb(211, 84, 0)',
                       'text-align': 'left', 'font-size': '1.2em'}

        layout = html.Div([
            html.Div([
                html.Br(),
                html.Label("Edit crystal structure live as pymatgen structure JSON "
                           "(in Python, use Structure.to_json() to generate):"),
                dcc.Textarea(
                    id=structure_id,
                    placeholder='Paste JSON from a pymatgen Structure object here, '
                                'using output from Structure.to_json()',
                    value="",
                    style={'overflow-y': 'scroll', 'width': '100%',
                           'height': '100%', 'font-family': 'monospace',
                           'min-height': '200px'})
           ], className="six columns"),
           html.Div([
               html.Br(),
               html.Label("", id=f'{structure_id}-highlighted-error', style=error_style),
               dcc.SyntaxHighlighter(
                   id=f'{structure_id}-highlighted',
                   children="",
                   language='javascript',
                   showLineNumbers=True,
                   customStyle={'overflow-y': 'scroll', 'height': '100%', 'min-height': '200px'})
           ], className="six columns")
        ], className="row")

        return html.Div([layout], style={'padding': '10px'})

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