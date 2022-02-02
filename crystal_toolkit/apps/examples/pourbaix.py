# standard Dash imports
import dash
from dash import dcc
from dash import html

# import for this example
from pymatgen.ext.matproj import MPRester

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc

# create Dash app as normal
app = dash.Dash()

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
        html.Div(id="pourbaix-output")
    ]
)

ctc.register_crystal_toolkit(app=app, layout=my_layout)

# allow app to be run using "python structure.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
