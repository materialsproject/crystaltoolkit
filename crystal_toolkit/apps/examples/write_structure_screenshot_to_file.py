# This example is used to write structures to images in an automated manner.
# It is a very specific script! Not intended for general use.
from __future__ import annotations

import urllib
from pathlib import Path
from time import sleep

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from pymatgen.ext.matproj import MPRester
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

SCREENSHOT_PATH = Path.home() / "screenshots"

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)
server = app.server

structure_component = ctc.StructureMoleculeComponent(
    show_compass=False,
    bonded_sites_outside_unit_cell=True,
    scene_settings={"zoomToFit2D": True},
)

my_layout = html.Div(
    [structure_component.layout(), dcc.Location(id="url"), html.Div(id="dummy-output")]
)


def get_structure_for_mpid(mpid):
    from pymatgen.ext.matproj import MPRester

    with MPRester() as mpr:
        structure = mpr.get_structure_by_material_id(mpid)

    return SpacegroupAnalyzer(structure).get_conventional_standard_structure()


@app.callback(
    Output(structure_component.id("scene"), "imageRequest"),
    Input(structure_component.id("graph"), "data"),
)
def trigger_image_request(data):
    sleep(1)
    return {"filetype": "png"}


@app.callback(Output(structure_component.id(), "data"), Input("url", "pathname"))
def trigger_new_data(url):
    mp_id = url[1:]
    with MPRester() as mpr:
        structure = mpr.get_structure_by_material_id(mp_id)

    return SpacegroupAnalyzer(structure).get_conventional_standard_structure()


@app.callback(
    Output("dummy-output", "children"),
    Input(structure_component.id("scene"), "imageDataTimestamp"),
    State("url", "pathname"),
    State(structure_component.id("scene"), "imageData"),
)
def save_image(image_data_timestamp, url, image_data):
    if image_data:
        # print(image_data.strip("data:image/png;base64,")[-1:-100])
        # image_bytes = b64decode(image_data.strip("data:image/png;base64,").encode('ascii'))
        response = urllib.request.urlopen(image_data)
        with open(SCREENSHOT_PATH / f"{url[1:]}.png", "wb") as file:
            file.write(response.file.read())


ctc.register_crystal_toolkit(app=app, layout=my_layout)
if __name__ == "__main__":
    app.run(debug=True, port=8050)
