# standard Dash imports
import dash
import dash_html_components as html
import dash_core_components as dcc

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS
from crystal_toolkit.helpers.layouts import H1, H2, Container

# dos and bs data from local jsons
from monty.serialization import loadfn
import os


# create Dash app as normal, assets folder set for visual styles only
app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# If callbacks created dynamically they cannot be statically checked at app startup.
# For this simple example this IS a problem and,
# nested layout this will need to be enabled -- consult Dash documentation
# for more information.
# app.config["suppress_callback_exceptions"] = True

path = os.path.dirname(os.path.realpath(__file__))
bandstructure_symm_line = loadfn(path + "/GaN_bs.json")
density_of_states = loadfn(path + "/GaN_dos.json")

# # create the Crystal Toolkit component
bsdos_component = ctc.BandstructureAndDosComponent(
    bandstructure_symm_line=bandstructure_symm_line,
    density_of_states=density_of_states,
    id="bs_dos",
)

# example layout to demonstrate capabilities of component
my_layout = Container(
    [H1("Band Structure and Density of States Example"), bsdos_component.layout(),]
)

# wrap your app.layout with crystal_toolkit_layout()
# to ensure all necessary components are loaded into layout
ctc.register_crystal_toolkit(app, layout=my_layout)


# allow app to be run using "python structure.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
