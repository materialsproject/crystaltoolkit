from __future__ import annotations

import dash
from dash import html
from pymatgen.core import Lattice, Structure

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# create the Structure object
structure = Structure(
    Lattice.cubic(4.2),
    ["Na", "K"],
    [[0, 0, 0], [0.5, 0.5, 0.5]],
    site_properties={"magmom": [-2, 2]},
)

# create the Crystal Toolkit component
structure_component = ctc.StructureMoleculeComponent(structure, id="my_structure")

# example layout to demonstrate capabilities of component
my_layout = html.Div(
    [
        html.H1("StructureMoleculeComponent Example"),
        html.H2("Standard Layout"),
        structure_component.layout(),
        html.H2("Optional Title Layout"),
        structure_component.title_layout(),
    ],
    style=dict(
        margin="2em auto", display="grid", placeContent="center", placeItems="center"
    ),
)

# tell crystal toolkit about your app and layout
ctc.register_crystal_toolkit(app, layout=my_layout)

# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash docs for more info
if __name__ == "__main__":
    app.run(debug=True, port=8050)
