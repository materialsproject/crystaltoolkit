# %%
from __future__ import annotations

import dash
from dash import html
from dash_mp_components import CrystalToolkitScene
from pymatgen.io.vasp import Chgcar

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

chgcar = Chgcar.from_file("../../../tests/test_files/chgcar.vasp")
scene = chgcar.get_scene(isolvl=0.0001)

layout = html.Div(
    [CrystalToolkitScene(data=scene.to_json())],
    style={"width": "100px", "height": "100px"},
)
# %%
# as explained in "preamble" section in documentation
ctc.register_crystal_toolkit(app=app, layout=layout)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
