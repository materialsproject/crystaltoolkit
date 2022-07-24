import os
from typing import Any

import dash
import plotly.express as px
import plotly.io as pio
from dash import dcc, html
from dash.dependencies import Input, Output, State
from pymatgen.core import Structure
from pymatviz.utils import get_crystal_sys
from tqdm import tqdm

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

pio.templates.default = "plotly_white"


__author__ = "Janosh Riebesell"
__date__ = "2022-07-21"
__email__ = "janosh@lbl.gov"

"""
Run this app with:
```
python crystal_toolkit/apps/examples/matbench_dielectric_structure_on_hover.py
```

About the matbench_dielectric dataset:

Intended use: Machine learning task to predict refractive index from structure.
    All data from Materials Project. Removed entries having a formation energy (or energy
    above the convex hull) more than 150meV and those having refractive indices less than
    1 and those containing noble gases. Retrieved April 2, 2019.
Input: Pymatgen Structure of the material
Target variable: refractive index n (unitless)
Entries: 636
URL: https://ml.materialsproject.org/projects/matbench_dielectric
"""

data_path = os.path.join(os.path.dirname(__file__), "matbench_dielectric.json.gz")

if os.path.isfile(data_path):
    import pandas as pd

    df_diel = pd.read_json(data_path)
else:
    try:
        from matminer.datasets import load_dataset

        df_diel = load_dataset("matbench_dielectric")

        df_diel[["spg_symbol", "spg_num"]] = [
            struct.get_space_group_info()
            for struct in tqdm(df_diel.structure, desc="Getting space groups")
        ]

        df_diel["crystal_sys"] = [get_crystal_sys(x) for x in df_diel.spg_num]

        df_diel["volume"] = [x.volume for x in df_diel.structure]
        df_diel["formula"] = [x.formula for x in df_diel.structure]

        df_diel.to_json(data_path, default_handler=lambda x: x.as_dict())
    except ImportError:
        print(
            "Matminer is not installed but needed to download a dataset. Run `pip install matminer`"
        )


plot_labels = {
    "crystal_sys": "Crystal system",
    "n": "Refractive index n",
    "spg_num": "Space group",
}

fig_n_vs_volume = px.scatter(
    df_diel.round(2),
    x="volume",
    y="n",
    color="crystal_sys",
    labels=plot_labels,
    size="n",
    hover_data=[df_diel.index, "spg_num"],
    hover_name="formula",
    range_x=[0, 1500],
)
title = "Matbench Dielectric: Refractive Index vs. Volume"
fig_n_vs_volume.update_layout(
    title=dict(text=f"<b>{title}</b>", x=0.5, font_size=20),
    legend=dict(x=1, y=1, xanchor="right"),
    margin=dict(b=20, l=40, r=20, t=100),
)
# slightly increase scatter point size (lower sizeref means larger)
fig_n_vs_volume.update_traces(marker_sizeref=0.05, selector=dict(mode="markers"))


structure_component = ctc.StructureMoleculeComponent(id="structure")

app = dash.Dash(prevent_initial_callbacks=True, assets_folder=SETTINGS.ASSETS_PATH)
graph = dcc.Graph(
    id="volume-vs-refract-idx-scatter-plot",
    figure=fig_n_vs_volume,
    style={"width": "90vh"},
)
hover_click_dd = dcc.Dropdown(
    id="hover-click-dropdown",
    options=["hover", "click"],
    value="hover",
    clearable=False,
    style=dict(minWidth="5em"),
)
hover_click_dropdown = html.Div(
    [html.Label("Update structure on:", style=dict(fontWeight="bold")), hover_click_dd],
    style=dict(
        display="flex",
        placeContent="center",
        placeItems="center",
        gap="1em",
        margin="1em",
    ),
)
graph_structure_div = html.Div(
    [graph, structure_component.layout(size="800px")],
    style=dict(display="flex", gap="2em"),
)
app.layout = html.Div(
    [hover_click_dropdown, graph_structure_div],
    style=dict(margin="2em"),
)
ctc.register_crystal_toolkit(app=app, layout=app.layout)


@app.callback(
    Output(structure_component.id(), "data"),
    Input(graph.id, "hoverData"),
    Input(graph.id, "clickData"),
    State(hover_click_dd.id, "value"),
)
def update_structure(
    hover_data: dict[str, list[dict[str, Any]]],
    click_data: dict[str, list[dict[str, Any]]],  # needed as callback trigger
    dropdown_value: str,
) -> Structure | None:
    """Update StructureMoleculeComponent with pymatgen structure when user clicks on
    new scatter point.
    """
    triggered = dash.callback_context.triggered[0]
    if dropdown_value == "click" and triggered["prop_id"].endswith(".hoverData"):
        # do nothing if we're in update-on-click mode but callback was triggered by hover event
        raise dash.exceptions.PreventUpdate

    # hover_data and click_data are identical since a hover event always precedes a click so
    # we always use hover_data
    data = hover_data["points"][0]
    material_id = data.get("customdata", ["missing _id"])[0]

    structure = df_diel.structure.get(material_id)

    return structure


if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
