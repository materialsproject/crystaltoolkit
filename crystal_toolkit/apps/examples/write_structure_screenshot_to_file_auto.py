# This example is used to write structures to images in an automated manner.
# It is a very specific script! Not intended for general use.
import urllib
from time import sleep
from pathlib import Path

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State

import crystal_toolkit.components as ctc


SCREENSHOT_PATH = Path.home() / "screenshots"

TIME_BETWEEN_STRUCTURES = 4  # seconds
TIME_FOR_STRUCTURE_TO_LOAD = 0.5

app = dash.Dash()

structure_component = ctc.StructureMoleculeComponent(
    show_compass=False, scene_settings={"zoomToFit2D": True}
)

my_layout = html.Div(
    [
        structure_component.layout(),
        dcc.Interval(id="interval", interval=TIME_BETWEEN_STRUCTURES * 1000),
        html.Div(id="dummy-output"),
    ]
)


def get_structure_for_mpid(mpid):
    from pymatgen.ext.matproj import MPRester

    with MPRester() as mpr:
        structure = mpr.get_structure_by_material_id(mpid)
    return structure


def get_all_mpids():
    from pymatgen.ext.matproj import MPRester

    with MPRester() as mpr:
        mpids = [
            d["task_id"]
            for d in mpr.query({"pretty_formula": "GaN"}, ["task_id"], chunk_size=10000)
        ]

    return sorted(mpids)


ALL_MPIDS = get_all_mpids()


@app.callback(
    Output(structure_component.id("scene"), "imageRequest"),
    [Input(structure_component.id("graph"), "data")],
)
def trigger_image_request(data):
    print("request!")
    sleep(TIME_FOR_STRUCTURE_TO_LOAD)
    return {"filetype": "png"}


@app.callback(
    Output(structure_component.id(), "data"), [Input("interval", "n_intervals")]
)
def trigger_new_data(n_intervals):
    if n_intervals:
        print(n_intervals, ALL_MPIDS[n_intervals])
        return get_structure_for_mpid(ALL_MPIDS[n_intervals])


@app.callback(
    Output("dummy-output", "children"),
    [Input(structure_component.id("scene"), "imageDataTimestamp")],
    [
        State("interval", "n_intervals"),
        State(structure_component.id("scene"), "imageData"),
    ],
)
def save_image(image_data_timestamp, n_intervals, image_data):
    if n_intervals and image_data:
        response = urllib.request.urlopen(image_data)
        fname = ALL_MPIDS[n_intervals]
        with open(SCREENSHOT_PATH / f"{fname}.png", "wb") as f:
            f.write(response.file.read())


ctc.register_crystal_toolkit(app=app, layout=my_layout)

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
