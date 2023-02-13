from base64 import b64encode
from string import Template

import dash_mp_components as mpc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, no_update
from dash.exceptions import PreventUpdate
from emmet.core.tasks import TaskDoc
from emmet.core.vasp.material import MaterialsDoc
from mp_api.client import MPRestError, MPRester
from pymatgen.io.vasp.inputs import Incar, Kpoints, Kpoints_supported_modes

import crystal_toolkit.components as ctc
import crystal_toolkit.helpers.layouts as ctl
from crystal_toolkit.helpers.utils import get_box_title

class VaspTasksComponent(ctc.MPComponent):
    """
    A component to render a TaskDocument. The canonical
    dcc.Store can contain either a Materials Project task_id, and
    so retrieves relevant information via an API call, or a serialized
    TaskDocument.
    """

    # This component uses code developed by M K Horton and R Yang.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_structure_component = ctc.StructureMoleculeComponent(
            id=self.id("task-details-structure")
        )
        self.initial_structure_component = ctc.StructureMoleculeComponent(
            id=self.id("task-details-initial-structure")
        )

    def get_layout(self) -> ctl.Container:
        """
        Return the layout for a given calculation (task_id).
        """

        structure_layout = html.Div(
            [
                get_box_title("Structures"),
                mpc.Tabs(
                    [
                        self.final_structure_component.layout(),
                        self.initial_structure_component.layout(),
                    ],
                    labels=["Final Structure", "Initial Structure"],
                ),
            ]
        )

        return ctl.Container(
            html.Article(
                [
                    ctl.Columns(
                        [
                            ctl.Column(
                                [
                                    html.Div(id=self.id("error-message")),
                                    ctl.Box(
                                        html.Div(
                                            [
                                                get_box_title("Calculation Overview"),
                                                html.Div(id=self.id("overview-table")),
                                            ]
                                        )
                                    ),
                                    ctl.Box(structure_layout),
                                    ctl.Box(
                                        html.Div(
                                            [
                                                get_box_title("Convergence Graph"),
                                                html.Div(
                                                    id=self.id("convergence-graph")
                                                ),
                                            ]
                                        )
                                    ),
                                ]
                            ),
                            ctl.Column(
                                [
                                    ctl.Block(
                                        ctl.Box(
                                            html.Div(
                                                [
                                                    get_box_title("Calculation Output"),
                                                    html.Div(
                                                        id=self.id("output-table")
                                                    ),
                                                ]
                                            )
                                        )
                                    ),
                                    ctl.Block(
                                        ctl.Box(
                                            html.Div(
                                                [
                                                    get_box_title(
                                                        "Calculation Settings"
                                                    ),
                                                    html.Div(id=self.id("incar-table")),
                                                ]
                                            )
                                        )
                                    ),
                                    ctl.Block(
                                        ctl.Box(
                                            html.Div(
                                                [
                                                    get_box_title("K-point Sampling"),
                                                    html.Div(
                                                        id=self.id("kpoints-table")
                                                    ),
                                                ]
                                            )
                                        )
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            )
        )

    def get_table_with_incar_information(self, incar: dict) -> html.Div:
        """
        Formats INCAR data into a human-readable table.
        """
        if not incar:
            return html.Div("Calculation settings are not available for this task")
        else:
            incar_data = {}

            # formatting the INCAR dict with links to the vasp-wiki page
            for k, v in incar.items():
                # target = 'blank' so that the link will open in a new tab
                incar_data[
                    html.A(
                        k,
                        href=f"https://www.vasp.at/wiki/index.php/{k}",
                        target="blank",
                    )
                ] = str(v)

            # TODO: the incar_data values should be formatted so the list is shown as valid VASP input
            incar_list = ctl.Block(
                html.Div(
                    # Using "Calculation Settings" instead of "INCAR" since this is more
                    # understandable to new users, and it will be obvious what this is to
                    # people who already use VASP
                    ctl.get_data_list(incar_data),
                    className="mp-data-list",
                )
            )
            encoded_incar = b64encode(str(Incar(incar)).encode("ascii")).decode("ascii")

            download_incar_link = ctl.Block(
                html.A(
                    ctl.Button(
                        [
                            ctl.Icon(kind="download"),
                            html.Span(),
                            "Download VASP INCAR file",
                        ]
                    ),
                    download="INCAR",
                    href=f"data:text/plain;base64,{encoded_incar}",
                )
            )
            return html.Div([incar_list, download_incar_link])

    def get_table_with_kpoints_information(self, kpoints: Kpoints) -> html.Div:
        """
        Formats Kpoints object into human-readable table.

        Note: Kpoints display will vary depending on the type of
        calculation, e.g. line-mode.
        """
        if not kpoints:
            return html.Div("K-points data is not available for this task")
        else:
            kpoints_data = {}

            # kpoints.style can be one of the following:
            #     Automatic = 0
            #     Gamma = 1
            #     Monkhorst = 2
            #     Line_mode = 3
            #     Cartesian = 4
            #     Reciprocal = 5

            # re-format kpoints.style to something a human can understand
            # TODO: make sure that all possible kpoint styles are defined
            style_to_human_label = {
                "Monkhorst": "Monkhorst-Pack",
                "Gamma": "Monkhorst-Pack (Gamma-centered)",
                # "Automatic": ,
                "Line_mode": "Line mode for band structure calculation"
                # "Cartesian": ,
                # "Reciprocal":
            }

            kpoints_data["Style"] = style_to_human_label.get(
                str(kpoints.style), str(kpoints.style)
            )

            if (kpoints.style == Kpoints_supported_modes.Monkhorst) or (
                kpoints.style == Kpoints_supported_modes.Gamma
            ):
                # if it's an M-P grid, the first "kpts" will be the grid divisions
                # if it's line-mode etc., this is not the case because kpts list is actual kpts
                kpoints_data["Divisions"] = " × ".join(map(str, kpoints.kpts[0]))

            # only show comment if not an empty string
            if comment := kpoints.comment:
                kpoints_data["Comment"] = comment

            # only show number of k-points if defined
            if kpoints.num_kpts > 0:
                kpoints_data["Number of K-points"] = str(kpoints.num_kpts)

            kpoints_list = ctl.Block(
                html.Div(ctl.get_data_list(kpoints_data), className="mp-data-list")
            )
            encoded_kpoints = b64encode(str(kpoints).encode("ascii")).decode("ascii")

            download_kpoints_link = ctl.Block(
                html.A(
                    ctl.Button(
                        [
                            ctl.Icon(kind="download"),
                            html.Span(),
                            "Download VASP KPOINTS file",
                        ]
                    ),
                    download="KPOINTS",
                    href=f"data:text/plain;base64,{encoded_kpoints}",
                )
            )

            return html.Div([kpoints_list, download_kpoints_link])

    def get_table_with_overview_data(
        self, task_doc: TaskDoc, materials_doc: MaterialsDoc
    ) -> html.Div:

        overview_data = {}

        overview_data["Type"] = html.A(
            materials_doc.calc_types[task_doc.task_id].value,
            href="https://github.com/materialsproject/emmet/blob/main/emmet-core/emmet/core/vasp/calc_types/enums.py#:~:text=class%20CalcType",
            target="_blank",
        )

        if task_doc.last_updated is not None:
            overview_data["Last Updated"] = task_doc.last_updated.strftime("%B %d, %Y")

        overview_data["Calculation Method"] = mpc.Markdown(
            f"[VASP](https://vasp.at) {task_doc.calcs_reversed[0].vasp_version}"
        )

        overview_list = ctl.Block(
            html.Div(ctl.get_data_list(overview_data), className="mp-data-list")
        )

        return overview_list

    def get_convergence_graph_for_taskdoc(self, task_doc: TaskDoc) -> go.Figure:
        convergence_data = []
        total_index = 0
        d_final_calc = dict(task_doc.calcs_reversed[0])
        e_fr_final_energy = d_final_calc["output"]["ionic_steps"][-1][
            "electronic_steps"
        ][-1]["e_fr_energy"]
        e_0_final_energy = d_final_calc["output"]["ionic_steps"][-1][
            "electronic_steps"
        ][-1]["e_0_energy"]
        e_wo_entrp_final_energy = d_final_calc["output"]["ionic_steps"][-1][
            "electronic_steps"
        ][-1]["e_wo_entrp"]

        for calc in reversed(task_doc.calcs_reversed):
            d = dict(calc)
            for ionic_index, ionic_step in enumerate(d["output"]["ionic_steps"]):
                for elec_index, elec_step in enumerate(ionic_step["electronic_steps"]):
                    total_index += 1
                    convergence_data.append(
                        {
                            "ionic_step": ionic_index,
                            "electronic_step": elec_index,
                            "total_step": total_index,
                            "energy": elec_step["e_fr_energy"] - e_fr_final_energy,
                            "quantity": "Free Energy /eV",
                        }
                    )
                    convergence_data.append(
                        {
                            "ionic_step": ionic_index,
                            "electronic_step": elec_index,
                            "total_step": total_index,
                            "energy": elec_step["e_0_energy"] - e_0_final_energy,
                            "quantity": "Enthalpy /eV",  # TODO: double check
                        }
                    )
                    convergence_data.append(
                        {
                            "ionic_step": ionic_index,
                            "electronic_step": elec_index,
                            "total_step": total_index,
                            "energy": elec_step["e_wo_entrp"] - e_wo_entrp_final_energy,
                            "quantity": "Energy without Entropy /eV",
                        }
                    )
        df = pd.DataFrame(convergence_data)

        if df["ionic_step"].max() == 0:
            figure = px.scatter(
                df[df["quantity"] == "Free Energy /eV"],
                x="total_step",
                y="energy",
                log_y=False,
                color="ionic_step",
                labels={
                    "total_step": "Total number of steps",
                    "energy": "Δ Total Energy (eV)",
                },
            )
            figure.update_coloraxes(showscale=False)

        else:
            figure = px.scatter(
                df[df["quantity"] == "Free Energy /eV"],
                x="total_step",
                y="energy",
                log_y=False,
                color="ionic_step",
                labels={
                    "total_step": "Total number of steps",
                    "energy": "Δ Total Energy (eV)",
                    "ionic_step": "Ionic Steps",
                },
            )
            figure.update_coloraxes(colorbar_dtick=1)

        return figure

    def get_table_with_task_output(self, task_doc: TaskDoc) -> html.Div:
        total_energy = task_doc.output.energy
        density = task_doc.output.density
        bandgap = task_doc.calcs_reversed[0].output["bandgap"]
        # TODO: use pymatgen.symmetry.analyzer to determine the structure object symmetry

        output_data = {
            "Total energy": "{:.2f} eV".format(total_energy),
            # see also: material details page density
            "Density": html.Span(["{:.3f} g·cm".format(density), html.Sup("-3")]),
            "Band gap": "{:.2f} eV".format(bandgap),
        }

        output_list = ctl.Block(
            html.Div(ctl.get_data_list(output_data), className="mp-data-list")
        )
        return output_list

    def generate_callbacks(self, app, cache):
        @app.callback(
            output=dict(
                incar=Output(self.id("incar-table"), "children"),
                kpoints=Output(self.id("kpoints-table"), "children"),
                overview=Output(self.id("overview-table"), "children"),
                convergence=Output(self.id("convergence-graph"), "children"),
                output=Output(self.id("output-table"), "children"),
                error=Output(self.id("error-message"), "children"),
            ),
            inputs=dict(task_id=Input(self.id(), "data")),
        )
        def update_incar_kpoints_associated_tables(task_data):
            """
            Callback to retrieve data about KPOINTS and INCAR
            and return tables.
            """

            try:
                task_doc = self.get_task_doc(
                    task_data,
                    fields=[
                        "task_id",
                        "orig_inputs",
                        "calcs_reversed",
                        "output",
                        "last_updated",
                    ],
                )
                if not task_doc:
                    raise PreventUpdate

                # look-up associated materials data via MPRester if valid task_id
                # TODO: validate task_id
                with MPRester() as mpr:
                    materials_doc = mpr.materials.get_data_by_id(
                        task_doc.task_id,
                        fields=[
                            "material_id",
                            "calc_types",
                        ],
                    )

                # ValueError if task_id formatted incorrectly
                # MPRestError if data could not be retrieved
            except (ValueError, MPRestError) as exc:
                error_message = ctl.MessageContainer(
                    [
                        ctl.MessageHeader(f"Task data could not be retrieved. {exc}"),
                        ctl.MessageBody(
                            "Please report to feedback@materialsproject.org if you think this is in error."
                        ),
                    ]
                )
                return dict(
                    incar=no_update,
                    kpoints=no_update,
                    overview=no_update,
                    convergence=no_update,
                    output=no_update,
                    error=error_message,
                )

            incar: dict = task_doc.orig_inputs.incar
            incar_table = self.get_table_with_incar_information(incar)

            kpoints: Kpoints = task_doc.orig_inputs.kpoints
            kpoints_table = self.get_table_with_kpoints_information(kpoints)

            overview_table = self.get_table_with_overview_data(
                task_doc=task_doc, materials_doc=materials_doc
            )

            convergence_graph = ctl.Block(
                [
                    dcc.Graph(
                        figure=self.get_convergence_graph_for_taskdoc(
                            task_doc=task_doc
                        ),
                        config={"displayModeBar": False},
                    )
                ]
            )

            output_table = self.get_table_with_task_output(task_doc=task_doc)

            return dict(
                incar=incar_table,
                kpoints=kpoints_table,
                overview=overview_table,
                convergence=convergence_graph,
                output=output_table,
                error=html.Div([]),
            )

        @app.callback(
            Output(self.final_structure_component.id(), "data"),
            Output(self.initial_structure_component.id(), "data"),
            Input(self.id(), "data"),
        )
        def update_structure_from_task_id(task_data):
            """
            Callback to retrieve data about Structure
            and return visualization.
            """

            task_doc = self.get_task_doc(
                task_data, fields=["output.structure", "orig_inputs.poscar"]
            )
            if not task_doc:
                raise PreventUpdate

            return task_doc.output.structure, task_doc.orig_inputs.poscar.structure

    @staticmethod
    def get_task_doc(task_data, fields=None):

        if not task_data:
            return None

        if isinstance(task_data, TaskDoc):
            return TaskDoc

        with MPRester() as mpr:
            task_doc = mpr.tasks.get_data_by_id(task_data, fields=fields)

        return task_doc
