# standard Dash imports
import dash
from dash import dcc
from dash import html

# import for this example
from pymatgen.core.structure import Structure
from pymatgen.core.lattice import Lattice

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc

# create Dash app as normal
app = dash.Dash()

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
        structure_component.layout(size="400px"),
        html.H2("Optional Title Layout"),
        structure_component.title_layout(),
    ]
)

# tell crystal toolkit about your app and layout
ctc.register_crystal_toolkit(app, layout=my_layout)

# allow app to be run using "python structure.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
