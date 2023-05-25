from __future__ import annotations

from typing import TYPE_CHECKING

import dash
import plotly.io as pio
from dash import dash_table, html
from dash.dependencies import Input, Output

import crystal_toolkit.components as ctc
import crystal_toolkit.helpers.layouts as ctl
from crystal_toolkit.apps.examples.utils import (
    load_and_store_matbench_dataset,
    matbench_dielectric_desc,
)
from crystal_toolkit.settings import SETTINGS

if TYPE_CHECKING:
    from pymatgen.core import Structure

pio.templates.default = "plotly_white"


__author__ = "Janosh Riebesell"
__date__ = "2022-07-21"
__email__ = "janosh@lbl.gov"

"""
Run this app with:
    python crystal_toolkit/apps/examples/matbench_dielectric_datatable_xrd.py
"""

df_diel = load_and_store_matbench_dataset("matbench_dielectric")

datatable_diel = dash_table.DataTable(
    data=df_diel.drop(columns="structure").round(2).to_dict("records"),
    id="datatable-diel",
    page_size=50,
)


structure_component = ctc.StructureMoleculeComponent(id="structure")
xrd_component = ctc.XRayDiffractionComponent(id="xrd")

structure_xrd_stacked = html.Div(
    [structure_component.layout(), xrd_component.layout()],
    style=dict(display="grid", gap="2em", alignContent="start"),
)
page_title = ctl.H1(
    "Matbench Dielectric Dataset", style=dict(textAlign="center", marginTop="1em")
)
description = html.P(
    "Click a table cell to view its structure and XRD plot.",
    style=dict(textAlign="center"),
)

app = dash.Dash(prevent_initial_callbacks=True, assets_folder=SETTINGS.ASSETS_PATH)
main_div = html.Div(
    [datatable_diel, structure_xrd_stacked],
    style=dict(margin="2em", display="flex", gap="2em", justifyContent="center"),
)
app.layout = html.Div([page_title, description, main_div, matbench_dielectric_desc])

ctc.register_crystal_toolkit(app=app, layout=app.layout)


@app.callback(
    Output(structure_component.id(), "data"),
    # currently broken due to internal callback in XRayDiffractionComponent
    # Output(xrd_component.id(), "data"),
    Input(datatable_diel, "active_cell"),
)
def update_structure(active_cell: dict[str, int | str]) -> Structure:
    """Update StructureMoleculeComponent with pymatgen structure when user clicks on new scatter
    point.
    """
    row_idx = active_cell["row"]
    return df_diel.structure[row_idx]


if __name__ == "__main__":
    app.run(debug=True, port=8050)
