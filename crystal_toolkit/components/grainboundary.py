import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

import pandas as pd

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from crystal_toolkit.core.panelcomponent import PanelComponent, PanelComponent2
from crystal_toolkit.helpers.layouts import (
    MessageContainer,
    MessageBody,
    Column,
    Columns,
)
from crystal_toolkit.helpers.mprester import MPRester
from pymatgen.util.string import unicodeify_spacegroup
from crystal_toolkit.components.structure import StructureMoleculeComponent


class GrainBoundaryPanel(PanelComponent2):
    @property
    def title(self):
        return "Grain Boundaries"

    @property
    def description(self):
        return "View computed grain boundary information for your crystal structure."

    def generate_callbacks(self, app, cache):

        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("inner_contents"), "children"), [Input(self.id(), "data")]
        )
        def retrieve_grain_boundaries(mpid):

            if not mpid or "mpid" not in mpid:
                raise PreventUpdate

            data = None

            with MPRester() as mpr:

                data = mpr.get_gb_data(mpid["mpid"])

            if not data:

                return (
                    "No grain boundary information computed for this crystal structure. "
                    "Grain boundary information has only been computed for elemental ground state "
                    "crystal structures at present."
                )

            table_data = [
                {
                    "Sigma": d["sigma"],
                    "Rotation Axis": f"{d['rotation_axis']}",
                    "Rotation Angle / º": f"{d['rotation_angle']:.2f}",
                    "Grain Boundary Plane": f"({' '.join(map(str, d['gb_plane']))})",
                    "Grain Boundary Energy / Jm⁻²": f"{d['gb_energy']:.2f}",
                }
                for d in data
            ]
            df = pd.DataFrame(table_data)

            table = dt.DataTable(
                id=self.id("table"),
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict("records"),
                style_cell={
                    "minWidth": "0px",
                    "maxWidth": "200px",
                    "whiteSpace": "normal",
                },
                css=[
                    {
                        "selector": ".dash-cell div.dash-cell-value",
                        "rule": "display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;",
                    }
                ],
                sort_action="native",
                sort_mode="multi",
            )

            view = html.Div(
                [
                    StructureMoleculeComponent(
                        data[2]["initial_structure"],
                        id=self.id("struct"),
                        static=True,
                        color_scheme="grain_label",
                    ).struct_layout
                ],
                style={"width": "400px", "height": "400px"},
            )

            return Columns([Column(table), Column(view)])
