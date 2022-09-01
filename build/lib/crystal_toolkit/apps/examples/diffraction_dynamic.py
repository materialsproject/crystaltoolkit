# standard Dash imports
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS
from crystal_toolkit.helpers.layouts import H1, H2, Container, Button

# create Dash app as normal
app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# create our crystal structure using pymatgen
from pymatgen.core.structure import Structure
from pymatgen.core.lattice import Lattice

xrd_component = ctc.XRayDiffractionComponent()

# example layout to demonstrate capabilities of component
my_layout = Container(
    [
        H1("XRDComponent Example (Structure Added After Loading)"),
        xrd_component.layout(),
        Button("Load XRD", id="load-xrd-button"),
    ]
)

# as explained in "preamble" section in documentation
ctc.register_crystal_toolkit(app=app, layout=my_layout)


@app.callback(
    Output(xrd_component.id(), "data"), [Input("load-xrd-button", "n_clicks")]
)
def load_structure(n_clicks):
    structure = Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    return structure


# allow app to be run using "python structure.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
