import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import plotly.graph_objs as go

from crystal_toolkit.helpers.layouts import Columns, Column
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.components.structure import StructureMoleculeComponent

from pymatgen.analysis.magnetism import CollinearMagneticStructureAnalyzer, Ordering
from pymatgen import MPRester

from collections import defaultdict


class MagnetismComponent(PanelComponent):
    @property
    def title(self):
        return "Magnetic Properties"

    @property
    def description(self):
        return (
            "Information on magnetic moments and magnetic "
            "ordering of this crystal structure."
        )

    @property
    def loading_text(self):
        return "Creating visualization of magnetic structure"

    def update_contents(self, new_store_contents):

        struct = self.from_data(new_store_contents)

        msa = CollinearMagneticStructureAnalyzer(struct, round_magmoms=1)
        if not msa.is_magnetic:
            # TODO: detect magnetic elements (?)
            return html.Div(
                "This structure is not magnetic or does not have "
                "magnetic information associated with it."
            )

        mag_species_and_magmoms = msa.magnetic_species_and_magmoms
        for k, v in mag_species_and_magmoms.items():
            if not isinstance(v, list):
                mag_species_and_magmoms[k] = [v]
        magnetic_atoms = "\n".join(
            [
                f"{sp} ({', '.join([f'{magmom} µB' for magmom in magmoms])})"
                for sp, magmoms in mag_species_and_magmoms.items()
            ]
        )

        magnetization_per_formula_unit = (
            msa.total_magmoms
            / msa.structure.composition.get_reduced_composition_and_factor()[1]
        )

        rows = []
        rows.append(
            (
                html.B("Total magnetization per formula unit"),
                html.Br(),
                f"{magnetization_per_formula_unit:.1f} µB",
            )
        )
        rows.append(
            (html.B("Atoms with local magnetic moments"), html.Br(), magnetic_atoms)
        )

        data_block = html.Div(
            [html.P([html.Span(cell) for cell in row]) for row in rows]
        )

        viewer = StructureMoleculeComponent(
            struct, id=self.id("magnetic_structure"), color_scheme="magmom", static=True
        )

        mp_data = self.collate_mp_data(struct)
        plot = self.create_plot_from_mp_data(mp_data)

        return Columns(
            [
                Column(
                    html.Div(
                        [viewer.struct_layout],
                        style={"height": "60vmin"},
                        id=self.id("structure-container"),
                    )
                ),
                Column(
                    [
                        data_block,
                        dcc.Graph(
                            id=self.id("graph"),
                            figure=plot,
                            config={"showLink": False, "displayModeBar": False},
                        ),
                    ]
                ),
            ]
        )

    @staticmethod
    def create_plot_from_mp_data(data):

        marker = {"symbol": "line-ew-open", "size": 100, "line": {"width": 6}}

        traces = defaultdict(lambda: defaultdict(list))

        # create a separate trace for each ordering type
        for k, v in sorted(data.items()):
            traces[v["ordering"]]["x"].append(0)
            traces[v["ordering"]]["y"].append(v["energy"])
            traces[v["ordering"]]["text"].append(k)

        traces = [
            go.Scatter(
                mode="markers",
                x=v["x"],
                y=v["y"],
                text=v["text"],
                name=k,
                marker=marker,
                hoverinfo="y+text",
            )
            for k, v in traces.items()
        ]

        layout = {
            "hovermode": "closest",
            "xaxis": {
                "range": [-1, 1],
                "showgrid": False,
                "zeroline": False,
                "showticklabels": False,
                "showline": False,
            },
            "yaxis": {
                # "type": "log",
                "showgrid": False,
                "zeroline": False,
                "showticklabels": True,
                "showline": True,
                "title": {
                    "text": "Energy above calculated ground state /meV",
                    "font": {"family": "IBM Plex Sans", "size": 20},
                },
                "tickfont": {"family": "IBM Plex Sans", "size": 18},
            },
            "legend": {"font": {"family": "IBM Plex Sans", "size": 18}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
        }

        return go.Figure(data=traces, layout=layout)

    @staticmethod
    def collate_mp_data(struct):

        mag_tasks = {}
        min_energy = 0

        ordering_labels = {
            "Unknown": "Unknown",
            "FM": "Ferromagnetic",
            "AFM": "Antiferromagnetic",
            "FiM": "Ferrimagnetic",
            "NM": "Non-magnetic",
        }

        with MPRester(endpoint="https://zola.lbl.gov/rest/v2") as mpr:

            # find similar structures in Materials Project
            mpids = mpr.find_structure(struct)

            # and all tasks for those materials, specifically their structures
            # and total energy per atom
            for d in mpr.query({"task_id": {"$in": mpids}}, ["task_ids"]):

                for task_id in d["task_ids"]:

                    add_task = True

                    task_struct = mpr.get_task_data(task_id, prop="structure")[0][
                        "structure"
                    ]
                    have_magmoms = "magmom" in task_struct.site_properties
                    task_energy = mpr.get_task_data(task_id, prop="energy_per_atom")[0][
                        "energy_per_atom"
                    ]
                    min_energy = min([min_energy, task_energy])
                    msa = CollinearMagneticStructureAnalyzer(task_struct)

                    if not have_magmoms:
                        ordering = "Unknown"
                    else:
                        ordering = msa.ordering.value

                        # group together similar orderings, only display lowest
                        # energy task for each ordering
                        mag_tasks_to_remove = []

                        for mag_task_id, mag_task in mag_tasks.items():
                            struct_to_compare = mag_task["struct"]
                            if msa.matches_ordering(struct_to_compare):
                                # if existing task is lower in energy, keep that one
                                if mag_task["energy"] < task_energy:
                                    add_task = False
                                # else remove existing task and add this one
                                else:
                                    mag_tasks_to_remove.append(mag_task_id)

                        # remove higher energy duplicate tasks
                        for mag_task_id in mag_tasks_to_remove:
                            del mag_tasks[mag_task_id]

                    if add_task:
                        mag_tasks[task_id] = {
                            "struct": task_struct,
                            "ordering": ordering_labels[ordering],
                            "energy": task_energy,
                        }

        for k, v in mag_tasks.items():
            v["energy"] = 1000 * (v["energy"] - min_energy)
            mag_tasks[k] = v

        return mag_tasks

    def generate_callbacks(self, app, cache):

        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("structure-container"), "children"),
            [Input(self.id("graph"), "clickData")],
        )
        def update_displayed_structure(clickData):

            if not clickData:
                raise PreventUpdate

            task_id = clickData["points"][0]["text"]

            with MPRester(endpoint="https://zola.lbl.gov/rest/v2") as mpr:
                struct = mpr.get_task_data(task_id, prop="structure")[0]["structure"]

            print(struct)

            viewer = StructureMoleculeComponent(
                struct,
                id=self.id("magnetic_structure"),
                color_scheme="magmom",
                static=True,
            )

            return viewer.struct_layout
