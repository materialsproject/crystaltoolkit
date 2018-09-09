import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import dash_table_experiments as dt

from mp_dash_components.converters.structure import StructureIntermediateFormat
from mp_dash_components import StructureViewerComponent
from mp_dash_components.layouts.misc import help_layout

from pymatgen.core import Structure

from itertools import combinations_with_replacement

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
            [Input(structure_viewer_id, 'generationOptions')],
            [State(structure_viewer_id, 'value')]
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
            "Jmol": "JMolNN",
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
            dt.DataTable(
                rows=[{'A': None, 'B': None, 'A-B /Å': None}],
                row_selectable=True,
                filterable=False,
                sortable=True,
                editable=True,
                selected_row_indices=[],
                max_rows_in_viewport=4,
                id=f'{structure_viewer_id}_bonding_algorithm_custom_cutoffs'
            )],
            id=f'{structure_viewer_id}_bonding_algorithm_custom_cutoffs_container',
            style={'display': 'none'})

        generation_options_hidden_div = html.Div(id=f'{structure_viewer_id}_bonding_algorithm_generation_options',
                                                 style={'display': 'none'})

        return html.Div([options, custom_cutoffs, generation_options_hidden_div])

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


def structure_color_options(structure_viewer_id, app, **kwargs):

    default_color_schemes = ['VESTA', 'Jmol']

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
                value='Jmol'
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
    pass




def structure_graph(structure_viewer_id, app, **kwargs):
    pass


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