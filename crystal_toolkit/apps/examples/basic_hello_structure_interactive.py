# as above
import dash
import dash_html_components as html
import dash_core_components as dcc
import crystal_toolkit.components as ctc

# standard Dash imports for callbacks (interactivity)
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from pymatgen import Structure, Lattice

app = dash.Dash()

# now we give a list of structures to pick from
structures = [
    Structure(Lattice.cubic(4), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]]),
    Structure(Lattice.cubic(5), ["K", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]]),
]

# we show the first structure by default
structure_component = ctc.StructureMoleculeComponent(structures[0])

# and we create a button for user interaction
my_button = html.Button("Swap Structure", id="change_structure_button")

# now we have two entries in our app layout,
# the structure component's layout and the button
my_layout = html.Div([structure_component.layout(), my_button])

ctc.register_crystal_toolkit(app=app, layout=my_layout, cache=None)

# for the interactivity, we use a standard Dash callback
@app.callback(
    Output(structure_component.id(), "data"),
    [Input("change_structure_button", "n_clicks")],
)
def update_structure(n_clicks):
    # on load, n_clicks will be None, and no update is required
    # after clicking on the button, n_clicks will be an int and incremented
    if not n_clicks:
        raise PreventUpdate
    return structures[n_clicks % 2]


# as above
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
