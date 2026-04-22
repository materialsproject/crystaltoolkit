from __future__ import annotations

import dash
from dash import html
from mp_api.client import MPRester
import os

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# If callbacks created dynamically they cannot be statically checked at app startup.
# For this simple example this is not a problem, but if creating a complicated,
# nested layout this will need to be enabled -- consult Dash documentation
# for more information.
app.config["suppress_callback_exceptions"] = True

print("API_Key found:", os.environ.get("MP_API_KEY"))

# first, retrieve entries from Materials Project
with MPRester() as mpr: #os.environ.get("MP_API_KEY")
    pourbaix_entries = mpr.get_pourbaix_entries("Fe-Co")

pourbaix_component = ctc.PourbaixDiagramComponent(default_data=pourbaix_entries)

# example layout to demonstrate capabilities of component
layout = html.Div(
    [
        html.H1("PourbaixDiagramComponent Example"),
        html.Button("Get Pourbaix Diagram", id="get-pourbaix"),
        pourbaix_component.layout(),
        html.Div(id="pourbaix-output"),
    ],
    style=dict(maxWidth="90vw", margin="2em auto"),
)

ctc.register_crystal_toolkit(app=app, layout=layout)

# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash docs for more info
if __name__ == "__main__":
    app.run(debug=True, port=8050)
