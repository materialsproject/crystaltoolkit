import dash
import dash_html_components as html
import crystal_toolkit as ct

from dash.dependencies import Input, Output, State


app = dash.Dash(__name__)

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

my_struct = ...

my_component = ct.StructureMoleculeComponent(my_struct)

app.layout = html.Div([
    ct.struct_layout
])


if __name__ == '__main__':
    app.run_server(debug=True)
