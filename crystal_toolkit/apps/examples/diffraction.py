from __future__ import annotations

import dash
from pymatgen.core import Lattice, Structure

import crystal_toolkit.components as ctc
from crystal_toolkit.helpers.layouts import H1, H3, Container
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)


structure = Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])

xrd_component = ctc.XRayDiffractionComponent(initial_structure=structure)

# example layout to demonstrate capabilities of component
my_layout = Container(
    [
        H1("XRDComponent Example"),
        H3("Generated from Structure object"),
        xrd_component.layout(),
    ]
)

# as explained in "preamble" section in documentation
ctc.register_crystal_toolkit(app=app, layout=my_layout)

# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash docs for more info
if __name__ == "__main__":
    app.run(debug=True, port=8050)
