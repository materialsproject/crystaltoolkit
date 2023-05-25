from __future__ import annotations

from typing import TYPE_CHECKING, Any

import dash
import plotly.express as px
import plotly.io as pio
from dash import dcc, html
from dash.dependencies import Input, Output, State

import crystal_toolkit.components as ctc
from crystal_toolkit.apps.examples.utils import (
    load_and_store_matbench_dataset,
    matbench_dielectric_desc,
)
from crystal_toolkit.helpers.utils import get_data_table
from crystal_toolkit.settings import SETTINGS

if TYPE_CHECKING:
    from pymatgen.core import Structure

pio.templates.default = "plotly_white"


__author__ = "Janosh Riebesell"
__date__ = "2022-07-21"
__email__ = "janosh@lbl.gov"

"""
Run this app with:
    python crystal_toolkit/apps/examples/matbench_dielectric_structure_on_hover.py
"""


df_diel = load_and_store_matbench_dataset("matbench_dielectric")

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
struct_title = html.H2(
    "Try hovering on a point in the plot to see its corresponding structure",
    id="struct-title",
    style=dict(position="absolute", padding="1ex 1em", maxWidth="25em"),
)
graph_structure_div = html.Div(
    [
        graph,
        html.Div([struct_title, structure_component.layout()]),
    ],
    style=dict(display="flex", gap="2em", margin="2em 0"),
)
table = get_data_table(
    df_diel.drop(columns="structure").reset_index(), id="data-table", virtualized=False
)
app.layout = html.Div(
    [hover_click_dropdown, graph_structure_div, table, matbench_dielectric_desc],
    style=dict(margin="2em", padding="1em"),
)
ctc.register_crystal_toolkit(app=app, layout=app.layout)


@app.callback(
    Output(structure_component.id(), "data"),
    Output(struct_title, "children"),
    Output(table, "style_data_conditional"),
    Input(graph, "hoverData"),
    Input(graph, "clickData"),
    State(hover_click_dd, "value"),
)
def update_structure(
    hover_data: dict[str, list[dict[str, Any]]],
    click_data: dict[str, list[dict[str, Any]]],  # needed only as callback trigger
    dropdown_value: str,
) -> tuple[Structure, str]:
    """Update StructureMoleculeComponent with pymatgen structure when user clicks or hovers a
    scatter point.
    """
    triggered = dash.callback_context.triggered[0]
    if dropdown_value == "click" and triggered["prop_id"].endswith(".hoverData"):
        # do nothing if we're in update-on-click mode but callback was triggered by hover event
        raise dash.exceptions.PreventUpdate

    # hover_data and click_data are identical since a hover event always precedes a click so
    # we always use hover_data
    data = hover_data["points"][0]
    material_id = data.get("customdata", ["missing _id"])[0]

    structure = df_diel.structure[material_id]
    formula = df_diel.formula[material_id]

    # highlight corresponding row in table
    style_data_conditional = {
        "if": {"row_index": material_id},
        "backgroundColor": "#3D9970",
        "color": "white",
    }

    return structure, formula, [style_data_conditional]


if __name__ == "__main__":
    app.run(debug=True, port=8050)
