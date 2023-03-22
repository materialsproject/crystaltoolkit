from __future__ import annotations

import os

import dash
from monty.serialization import loadfn

import crystal_toolkit.components as ctc
from crystal_toolkit.helpers.layouts import H1, Container
from crystal_toolkit.settings import SETTINGS

# assets folder set for visual styles only
app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# If callbacks created dynamically they cannot be statically checked at app startup.
# For this simple example this IS a problem and,
# nested layout this will need to be enabled -- consult Dash documentation
# for more information.
# app.config["suppress_callback_exceptions"] = True

path = os.path.dirname(os.path.realpath(__file__))
fermi_surface = loadfn(f"{path}/BaFe2As2_fs.json.gz")

# create the Crystal Toolkit component
fs_component = ctc.FermiSurfaceComponent(fermi_surface, id="fermi_surface")

# example layout to demonstrate capabilities of component
my_layout = Container([H1("Fermi Surface Example"), fs_component.layout()])

# wrap your app.layout with crystal_toolkit_layout()
# to ensure all necessary components are loaded into layout
ctc.register_crystal_toolkit(app, layout=my_layout)

# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash docs for more info
if __name__ == "__main__":
    app.run(debug=True, port=8050)
