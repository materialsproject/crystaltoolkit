from __future__ import annotations

import dash
from dash import html
from pymatgen.ext.matproj import MPRester

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# If callbacks created dynamically they cannot be statically checked at app startup.
# For this simple example this is not a problem, but if creating a complicated,
# nested layout this will need to be enabled -- consult Dash documentation
# for more information.
app.config["suppress_callback_exceptions"] = True

# first, retrieve entries from Materials Project
with MPRester() as mpr:
    pourbaix_entries = mpr.get_pourbaix_entries("Fe-Co")

pourbaix_component = ctc.PourbaixDiagramComponent(default_data=pourbaix_entries)

# example layout to demonstrate capabilities of component
my_layout = html.Div(
    [
        html.H1("PourbaixDiagramComponent Example"),
        html.Button("Get Pourbaix Diagram", id="get-pourbaix"),
        pourbaix_component.layout(),
        html.Div(id="pourbaix-output"),
    ],
    style=dict(maxWidth="90vw", margin="2em auto"),
)

ctc.register_crystal_toolkit(app=app, layout=my_layout)

# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash docs for more info
if __name__ == "__main__":
    app.run(debug=True, port=8050)
