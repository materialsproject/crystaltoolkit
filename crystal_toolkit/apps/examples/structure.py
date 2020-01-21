# standard Dash imports
import dash
import dash_html_components as html
import dash_core_components as dcc

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc

# import for this example
from pymatgen import Structure, Lattice

# create Dash app as normal
app = dash.Dash()

# create the Structure object
structure = Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])

# create the Crystal Toolkit component
structure_component = ctc.StructureMoleculeComponent(structure, id="my_structure")

# example layout to demonstrate capabilities of component
my_layout = html.Div(
    [
        html.H1("StructureMoleculeComponent Example"),
        html.H2("Standard Layout"),
        structure_component.layout(size="400px"),
        html.H2("Optional Additional Layouts"),
        html.H3("Screenshot Layout"),
        structure_component.screenshot_layout(),
        html.H3("Options Layout"),
        structure_component.options_layout(),
        html.H3("Title Layout"),
        structure_component.title_layout(),
        html.H3("Legend Layout"),
        structure_component.legend_layout(),
        html.H2("Technical Details"),
        dcc.Markdown(str(structure_component)),
    ]
)

# tell crystal toolkit about your app and layout
ctc.register_crystal_toolkit(app, layout=my_layout)

# allow app to be run using "python structure.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
