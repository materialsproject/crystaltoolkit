import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from mp_dash_components.helpers import mp_component
from mp_dash_components.layouts.structure import *
from mp_dash_components.layouts.misc import *

from monty.serialization import loadfn

app = dash.Dash()
app.title = "Materials Project Dash Component Examples"

app.scripts.config.serve_locally = True
app.config['suppress_callback_exceptions'] = True

example_structure = loadfn('example_files/example_structure.json')

app.layout = html.Div([
    mp_component(example_structure, app=app, id='structure-viewer'),
    structure_view_options_layout(structure_viewer_id='structure-viewer', app=app),
    # structure_screenshot_button(structure_viewer_id='structure-viewer', app=app),  # beta
    structure_bonding_algorithm(structure_viewer_id='structure-viewer', app=app),
    structure_color_options(structure_viewer_id='structure-viewer', app=app),
    combine_option_dicts([
        'structure-viewer_bonding_algorithm_generation_options',
        'structure-viewer_color_scheme_choice_generation_options'
    ], 'structure-viewer', 'generationOptions', app=app)
], style={'width': '500px', 'height': '500px'})

if __name__ == '__main__':
    app.run_server(debug=True)
