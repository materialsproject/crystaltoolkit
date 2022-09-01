import dash

# create our crystal structure using pymatgen
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure

import crystal_toolkit.components as ctc
from crystal_toolkit.helpers.layouts import H1, Container
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

structure = Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])

xrd_component = ctc.XRayDiffractionComponent()

# example layout to demonstrate capabilities of component
my_layout = Container(
    [H1("XRDComponent Example (Empty, No Structure Defined)"), xrd_component.layout()]
)

# as explained in "preamble" section in documentation
ctc.register_crystal_toolkit(app=app, layout=my_layout)

# allow app to be run using "python structure.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
