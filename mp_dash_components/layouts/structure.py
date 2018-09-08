import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from mp_dash_components.converters.structure import StructureIntermediateFormat
from mp_dash_components import StructureViewerComponent

from pymatgen.core import Structure


def structure_layout(structure, app,
                     structure_viewer_id="structure-viewer", **kwargs):

    def generate_layout(structure, structure_viewer_id):

        if isinstance(structure, Structure):
            structure_dict = structure.as_dict(verbosity=0)
            intermediate_json = StructureIntermediateFormat(structure).json
            return StructureViewerComponent(id=structure_viewer_id,
                                            structure=structure_dict,
                                            data=intermediate_json,
                                            **kwargs)
        else:
            raise ValueError

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(structure_viewer_id, 'data'),
            [Input(structure_viewer_id, 'generationOptions')],
            [State(structure_viewer_id, 'structure')]
        )
        def generate_visualization_data(generationOptions, structure):
            generationOptions = generationOptions or {}
            print(generationOptions)
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
            "Custom": "CutOffDictNN",
            "Jmol": "JMolNN",
        }

        options = dcc.Dropdown(
            options=[
                {'label': k, 'value': v} for k, v in nn_mapping.items()
            ],
            value='CrystalNN',
            id=f'{structure_viewer_id}_bonding_algorithm'
        )

        return options

    def generate_callbacks(structure_viewer_id, app):

        @app.callback(
            Output(structure_viewer_id, 'generationOptions'),
            [Input(f'{structure_viewer_id}_bonding_algorithm', 'value')],
            [State(structure_viewer_id, 'generationOptions')]
        )
        def update_structure_viewer_data(bonding_algorithm, currentGenerationOptions):
            generationOptions = currentGenerationOptions or {}
            generationOptions['bonding_strategy'] = bonding_algorithm
            return generationOptions

    layout = generate_layout(structure_viewer_id)
    generate_callbacks(structure_viewer_id, app)

    return layout


def structure_graph(structure_viewer_id, app, **kwargs):
    pass


def structure_json_editor(structure_viewer_id, app, **kwargs):
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