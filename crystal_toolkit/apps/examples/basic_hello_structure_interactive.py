# as above
import dash
import dash_html_components as html
import dash_core_components as dcc
import crystal_toolkit.components as ctc

# standard Dash imports for callbacks (interactivity)
from dash.dependencies import Input, Output, State

# so we can pick a structure at random
from random import choice
from pymatgen import Structure, Lattice

app = dash.Dash()
ctc.register_app(app)

# prevent static checking of your layout ahead-of-time
# otherwise errors can be raised in certain instances
# see discussion below
app.config["suppress_callback_exceptions"] = True

# now we give a list of structures to pick from
structures = [
    Structure(Lattice.cubic(4), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]]),
    Structure(Lattice.cubic(5), ["K", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]]),
    Structure(Lattice.cubic(6), ["Li", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]]),
]

# we show the first structure by default
structure_component = ctc.StructureMoleculeComponent(structures[0])

# and we create a button for user interaction
my_button = html.Button("Randomize!", id="random_button")

# now we have two entries in our app layout,
# the structure component's layout and the button
my_layout = html.Div([structure_component.layout(), my_button])
app.layout = ctc.crystal_toolkit_layout(my_layout)


# for the interactivity, we use a standard Dash callback
@app.callback(
    Output(structure_component.id(), "data"), [Input("random_button", "n_clicks")]
)
def update_structure(n_clicks):
    return choice(structures)


# as above
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
