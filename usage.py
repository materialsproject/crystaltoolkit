import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from mp_dash_components.helpers import mp_component

from monty.serialization import loadfn

app = dash.Dash()
app.title = "Materials Project Dash Component Examples"

app.scripts.config.serve_locally = True

example_structure = loadfn('example_files/example_structure.json')

app.layout = html.Div([
    mp_component(example_structure, id='structure')
], style={'width': '500px', 'height': '500px'})

if __name__ == '__main__':
    app.run_server(debug=True)
