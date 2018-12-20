import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from uuid import uuid4

import mp_dash_components

app = dash.Dash()

app.scripts.config.serve_locally = True

#data = [
#        {
#            'type': 'sphere',
#            'defaults': {'radii': 'standard', 'colors': 'standard'},
#            'idx': [0, 0, 0, 1, 1, 1],
#            'positions': [[0, 0, 0], [5, 0, 0], [0, 5, 0], [0, 0, 5], [5, 5, 0], [0, 5, 5]],
#            'idx_phi_start': [0, 0],
#            'idx_phi_end': [1, 1],
#            'idx_radii': {'standard': [0.5, 0.75]},
#            'idx_colors': {'standard': ['#ff0000', '#0000ff']},
#        }
#]

data = {
    'name': 'crystal',
    'contents': [
        {
            'name': 'atoms_example',
            'contents': [
                {'type': 'sphere', 'radius': 5, 'color': '#0000ff', 'positions': [[0, 0, 0],
                                                                                  [0, 0, 20],
                                                                                  [0, 20, 0],
                                                                                  [20, 0, 0],
                                                                                  [20, 20, 0]]}
            ]
        },
        {
            'name': 'bonds_example',
            'contents': [
                {'type': 'cylinder', 'radius': 3, 'color': '#ff0000',
                 'positions': [[[0, 0, 0], [0, 0, 20]],
                               [[0, 0, 20], [0, 20, 20]]]}
            ]
        }
    ]
}

app.layout = html.Div([
    mp_dash_components.MP3DComponent(data=data)
], style={'width': '500px', 'height': '500px'})

app.server.secret_key = str(uuid4())
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=8082)
