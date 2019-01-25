import dash
import dash_html_components as html
import crystal_toolkit as ct

from crystal_toolkit.helpers.scene import *

from pymatgen import Structure, Lattice

app = dash.Dash(__name__)

app.config["suppress_callback_exceptions"] = True
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True
app.title = "Crystal Toolkit Example Components"

ct.register_app(app)

# StructureMoleculeComponent

example_struct = Structure.from_spacegroup(
    "P6_3mc",
    Lattice.hexagonal(3.22, 5.24),
    ["Ga", "N"],
    [[1 / 3, 2 / 3, 0], [1 / 3, 2 / 3, 3 / 8]],
)

test_scene = [Scene("test", contents=[
    Spheres(positions=[[0, 0, 0]]),
    Surface(positions=[[0, 10, 0], [10, 0, 0], [0, 0, 10]])
])]

struct_component = ct.StructureMoleculeComponent(
    example_struct, scene_additions=test_scene
)

app.layout = html.Div(struct_component.standard_layout)


if __name__ == "__main__":
    app.run_server(debug=True)
