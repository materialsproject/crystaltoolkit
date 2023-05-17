from __future__ import annotations

import dash
from dash.dependencies import Input, Output
from pymatgen.core import Lattice, Structure

import crystal_toolkit.components as ctc
from crystal_toolkit.helpers.layouts import H1, Button, Container
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

xrd_component = ctc.XRayDiffractionComponent(id="xrd-diffraction")

# example layout to demonstrate capabilities of component
page_title = H1("XRDComponent Example (Structure Added After Loading)")
load_btn = Button("Load XRD", id="load-xrd-button")
my_layout = Container([page_title, xrd_component.layout(), load_btn])

# as explained in "preamble" section in documentation
ctc.register_crystal_toolkit(app=app, layout=my_layout)


@app.callback(Output(xrd_component.id(), "data"), Input(load_btn, "n_clicks"))
def load_structure(n_clicks: int) -> Structure:
    """Load a cubic structure on button click."""
    return Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])


# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash docs for more info
if __name__ == "__main__":
    app.run(debug=True, port=8050)
