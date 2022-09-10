
import dash
from dash import html
from dash_mp_components import CrystalToolkitScene
from monty.serialization import loadfn

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# create the MigrationGraph object
mg = loadfn("LiMnP2O7_mg.json")

# create the Crystal Toolkit component
# no MigrationGraph component yet
component = ctc.StructureMoleculeComponent(mg.structure, id="my_structure")
test_scene = mg.get_scene()

# example layout
my_layout = html.Div(
    [html.Div([CrystalToolkitScene(data=test_scene.to_json())])],
    style=dict(
        margin="2em auto", display="grid", placeContent="center", placeItems="center"
    ),
)

# tell crystal toolkit about your app and layout
ctc.register_crystal_toolkit(app, layout=my_layout)

# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
