from __future__ import annotations

import dash
from dash import dcc
from dash.dependencies import Input, Output

# create our crystal structures using pymatgen
from pymatgen.core import Lattice, Structure

import crystal_toolkit.components as ctc
from crystal_toolkit.helpers.layouts import H1, H3, Container
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)


structures = {
    "Si": Structure(
        Lattice.cubic(5.44),
        ["Si"] * 8,
        [
            [0.25, 0.75, 0.25],
            [0.0, 0.0, 0.5],
            [0.25, 0.25, 0.75],
            [0.0, 0.5, 0.0],
            [0.75, 0.75, 0.75],
            [0.5, 0.0, 0.0],
            [0.75, 0.25, 0.25],
            [0.5, 0.5, 0.5],
        ],
    ),
    "SrTiO3": Structure(
        Lattice.cubic(3.905),
        ["Sr", "Ti", "O", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    ),
    "GaN": Structure.from_spacegroup(
        "P6_3mc",
        Lattice.hexagonal(3.189, 5.185),
        ["Ga", "N"],
        [[1 / 3, 2 / 3, 0], [1 / 3, 2 / 3, 0.377]],
    ),
}

tem_component = ctc.TEMDiffractionComponent(initial_structure=structures["Si"])

structure_choice = dcc.Dropdown(
    id="structure-choice", options=list(structures), value="Si", clearable=False
)

# example layout to demonstrate capabilities of component
layout = Container(
    [
        H1("TEMDiffractionComponent Example"),
        H3("Generated from Structure object"),
        structure_choice,
        tem_component.layout(),
    ]
)

# as explained in "preamble" section in documentation
ctc.register_crystal_toolkit(app=app, layout=layout)


@app.callback(
    Output(tem_component.id("structure"), "data"),
    Input(structure_choice, "value"),
    prevent_initial_call=True,
)
def load_structure(name: str) -> dict:
    """Show the chosen structure in the simulator."""
    return structures[name].as_dict()


# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash docs for more info
if __name__ == "__main__":
    app.run(debug=True, port=8050)
