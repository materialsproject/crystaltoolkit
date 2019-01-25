import dash
import dash_html_components as html
import crystal_toolkit as ct

from pymatgen import Structure, Lattice

app = dash.Dash(__name__)

app.config['suppress_callback_exceptions']=True
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
struct_component = ct.StructureMoleculeComponent(example_struct)

app.layout = html.Div(struct_component.standard_layout)


if __name__ == "__main__":
    app.run_server(debug=True)
