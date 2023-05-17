from __future__ import annotations

import dash
from dash import html

# standard Dash imports for callbacks (interactivity)
from dash.dependencies import Input, Output
from pymatgen.core import Lattice, Structure

import crystal_toolkit.components as ctc

# don't run callbacks on page load
app = dash.Dash(prevent_initial_callbacks=True)

# now we give a list of structures to pick from
structures = [
    Structure(Lattice.hexagonal(5, 3), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]]),
    Structure(Lattice.cubic(5), ["K", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]]),
]

# we show the first structure by default
structure_component = ctc.StructureMoleculeComponent(
    structures[0], id="hello_structure"
)

# and we create a button for user interaction
my_button = html.Button("Swap Structure", id="change_structure_button")

# now we have two entries in our app layout,
# the structure component's layout and the button
my_layout = html.Div([structure_component.layout(), my_button])

ctc.register_crystal_toolkit(app=app, layout=my_layout)


# for the interactivity, we use a standard Dash callback
@app.callback(
    Output(structure_component.id(), "data"),
    Input("change_structure_button", "n_clicks"),
)
def update_structure(n_clicks):
    """Toggle between hexagonal and cubic structures on button click."""
    return structures[n_clicks % 2]


if __name__ == "__main__":
    app.run(debug=True, port=8050)
