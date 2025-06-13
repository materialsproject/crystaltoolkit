from __future__ import annotations

import warnings
from importlib.metadata import version
from typing import TYPE_CHECKING

from dash.dependencies import Component, Input, Output
from lobsterpy.cohp.analyze import Analysis
from lobsterpy.cohp.describe import Description
from plotly.subplots import make_subplots
from pymatgen.analysis.graphs import MoleculeGraph
from pymatgen.core import Molecule, Structure
from pymatgen.electronic_structure.cohp import CompleteCohp
from pymatgen.electronic_structure.dos import LobsterCompleteDos
from pymatgen.io.lobster.inputs import Lobsterin
from pymatgen.io.lobster.outputs import (
    Bandoverlaps,
    Charge,
    Icohplist,
    Lobsterout,
    MadelungEnergies,
)
from pymatgen.util.string import unicodeify_species

from crystal_toolkit.components.bandstructure import BandstructureAndDosComponent
from crystal_toolkit.components.structure import StructureMoleculeComponent
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import (
    H4,
    Column,
    Columns,
    MessageBody,
    MessageContainer,
    dcc,
    get_table,
    html,
)

if TYPE_CHECKING:
    import plotly.graph_objects as go
    from pymatgen.io.vasp.outputs import Vasprun

warnings.filterwarnings("ignore")


class CohpAndDosComponent(MPComponent):
    def __init__(
        self,
        charge_obj: Charge | None = None,
        completecohp_obj: CompleteCohp | None = None,
        icohplist_obj: Icohplist | None = None,
        madelung_obj: MadelungEnergies | None = None,
        mpid: str | None = None,
        density_of_states: LobsterCompleteDos | None = None,
        lobsterin_obj: Lobsterin | None = None,
        lobsterout_obj: Lobsterout | None = None,
        bandoverlaps_obj: Bandoverlaps | None = None,
        vasprun_obj: Vasprun | None = None,
        structure_obj: Structure | None = None,
        id: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            id=id,
            default_data={
                "charge_obj": charge_obj,
                "completecohp_obj": completecohp_obj,
                "icohplist_obj": icohplist_obj,
                "madelung_obj": madelung_obj,
                "mpid": mpid,
                "density_of_states": density_of_states,
                "lobsterin_obj": lobsterin_obj,
                "lobsterout_obj": lobsterout_obj,
                "bandoverlaps_obj": bandoverlaps_obj,
                "vasprun_obj": vasprun_obj,
                "structure_obj": structure_obj,
            },
            **kwargs,
        )

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        completecohp_obj, charge_obj, icohplist_obj, madelung_obj, dos = (
            CohpAndDosComponent._get_plot_inputs(self.initial_data["default"])
        )

        fig = CohpAndDosComponent.get_figure(
            charge_obj=charge_obj,
            completecohp_obj=completecohp_obj,
            madelung_obj=madelung_obj,
            icohplist_obj=icohplist_obj,
            dos=dos,
        )

        # Main plot
        graph = html.Div(
            [
                dcc.Graph(
                    figure=fig,
                    config={"displayModeBar": False},
                    responsive=True,
                    style={"width": "100%"},
                )
            ],
            id=self.id("cohp-dos-graph"),
        )

        analysis_options = [
            {"label": "all", "value": "all"},
            {"label": "cation-anion", "value": "cation-anion"},
        ]

        state = {"analysis-mode": "all"}

        analysis_mode = html.Div(
            [
                self.get_choice_input(
                    kwarg_label="analysis-mode",
                    state=state,
                    label="LobsterPy analysis mode",
                    help_str="Analysis mode to choose from",
                    options=analysis_options,
                )
            ],
            style={"width": "200px"},
            id=self.id("options-container"),
        )

        analysis_description = CohpAndDosComponent.get_summary_text(
            charge_obj=charge_obj,
            completecohp_obj=completecohp_obj,
            icohplist_obj=icohplist_obj,
            dos=dos,
            madelung_obj=madelung_obj,
            which_bonds="all",
        )

        calc_quality_description = self.get_calc_quality_text(
            input_dict=self._get_all_inputs(self.initial_data["default"])
        )

        lobsterpy_version = version("lobsterpy")

        repo_link = html.A(
            f"LobsterPy v{lobsterpy_version}",
            href="https://github.com/JaGeo/LobsterPy.git",
            style={"white-space": "nowrap"},
        )

        analysis_description_div = html.Div(
            [
                MessageContainer(
                    MessageBody(
                        [f"{analysis_description} - ", repo_link],
                    ),
                    kind="dark",
                    size="normal",
                ),
            ],
            id=self.id("analysis-description"),
            # style={"position": "relative"}
        )

        calc_quality_description_div = html.Div(
            [
                MessageContainer(
                    MessageBody(
                        [f"{calc_quality_description}"],
                    ),
                    kind="info",
                    size="normal",
                )
            ],
            id=self.id("calc-quality-description"),
            # style={"position": "relative"}
        )

        # LobsterPy local environments
        local_envs = html.Div(
            children=[
                CohpAndDosComponent.get_lobster_local_envs(
                    charge_obj=charge_obj,
                    completecohp_obj=completecohp_obj,
                    icohplist_obj=icohplist_obj,
                    madelung_obj=madelung_obj,
                    which_bonds="all",
                )
            ],
            id=self.id("local-env-lobsterpy"),
        )

        return {
            "graph": graph,
            "analysis-mode": analysis_mode,
            "analysis-description": analysis_description_div,
            "calc-quality-description": calc_quality_description_div,
            "local-envs": local_envs,
        }

    def layout(self):
        """Return the layout of the component."""
        # Get the sub-layouts
        # and create the main layout
        sub_layouts = self._sub_layouts

        graph = sub_layouts["graph"]

        controls = Columns(
            [
                Column(
                    [
                        sub_layouts["analysis-mode"],
                    ]
                )
            ]
        )

        # Create the description div
        description_header = H4(
            "Bonding analysis summary",
            id=self.id("summary_text"),
            style={"display": "inline-block"},
        )

        description_div = Columns([Column([sub_layouts["analysis-description"]])])

        calc_quality_header = H4(
            "Calculation quality",
            id=self.id("calc-quality-text"),
            style={"display": "inline-block"},
        )
        calc_quality_div = Columns([Column([sub_layouts["calc-quality-description"]])])

        # Create the local environments div
        local_envs_header = H4(
            "Local Environments identified via LobsterEnv",
            id=self.id("local-envs-text"),
            style={"display": "inline-block"},
        )
        local_envs_div = Columns([Column([sub_layouts["local-envs"]])])

        return Column(
            [
                controls,
                graph,
                html.Br(),
                description_header,
                description_div,
                calc_quality_header,
                calc_quality_div,
                local_envs_header,
                local_envs_div,
            ]
        )

    @staticmethod
    def _get_plot_inputs(
        data: dict | None,
    ) -> (
        tuple[CompleteCohp, Charge, Icohplist, MadelungEnergies, LobsterCompleteDos]
        | tuple[None, None, None, None, None]
    ):
        data = data or {}

        charge_obj = data.get("charge_obj")
        completecohp_obj = data.get("completecohp_obj")
        icohplist_obj = data.get("icohplist_obj")
        dos_obj = data.get("density_of_states")
        madelung_obj = data.get("madelung_obj")

        if charge_obj and isinstance(charge_obj, dict):
            charge_obj = Charge.from_dict(charge_obj)

        if completecohp_obj and isinstance(completecohp_obj, dict):
            completecohp_obj = CompleteCohp.from_dict(completecohp_obj)

        if icohplist_obj and isinstance(icohplist_obj, dict):
            icohplist_obj = Icohplist.from_dict(icohplist_obj)

        if dos_obj and isinstance(dos_obj, dict):
            dos_obj = LobsterCompleteDos.from_dict(dos_obj)

        if madelung_obj and isinstance(madelung_obj, dict):
            madelung_obj = MadelungEnergies.from_dict(madelung_obj)

        return completecohp_obj, charge_obj, icohplist_obj, madelung_obj, dos_obj

    @staticmethod
    def _get_all_inputs(
        data: dict | None,
    ) -> dict:
        data = data or {}

        charge_obj = data.get("charge_obj")
        completecohp_obj = data.get("completecohp_obj")
        icohplist_obj = data.get("icohplist_obj")
        lob_dos_obj = data.get("density_of_states")
        madelung_obj = data.get("madelung_obj")
        lobsterin_obj = data.get("lobsterin_obj")
        lobsterout_obj = data.get("lobsterout_obj")
        bandoverlaps_obj = data.get("bandoverlaps_obj")
        structure_obj = data.get("structure_obj")

        if charge_obj and isinstance(charge_obj, dict):
            data["charge_obj"] = Charge.from_dict(charge_obj)

        if completecohp_obj and isinstance(completecohp_obj, dict):
            data["completecohp_obj"] = CompleteCohp.from_dict(completecohp_obj)

        if icohplist_obj and isinstance(icohplist_obj, dict):
            data["icohplist_obj"] = Icohplist.from_dict(icohplist_obj)

        if lob_dos_obj and isinstance(lob_dos_obj, dict):
            data["density_of_states"] = LobsterCompleteDos.from_dict(lob_dos_obj)

        if madelung_obj and isinstance(madelung_obj, dict):
            data["madelung_obj"] = MadelungEnergies.from_dict(madelung_obj)

        if lobsterin_obj and isinstance(lobsterin_obj, dict):
            data["lobsterin_obj"] = Lobsterin.from_dict(lobsterin_obj)

        if lobsterout_obj and isinstance(lobsterout_obj, dict):
            data["lobsterout_obj"] = Lobsterout.from_dict(lobsterout_obj)

        if bandoverlaps_obj and isinstance(bandoverlaps_obj, dict):
            data["bandoverlaps_obj"] = Bandoverlaps.from_dict(bandoverlaps_obj)

        if structure_obj and isinstance(structure_obj, dict):
            data["structure_obj"] = Structure.from_dict(structure_obj)

        return data

    @staticmethod
    def get_calc_quality_text(
        input_dict: dict,
    ) -> str:
        """Get text description of calculation quality

        Args:
            input_dict: Dictionary containing the pymatgen objects.

        Returns:
            A string describing the calculation quality.
        """

        calc_quality_dict = Analysis.get_lobster_calc_quality_summary(
            charge_obj=input_dict.get("charge_obj"),
            lobster_completedos_obj=input_dict.get("density_of_states"),
            vasprun_obj=input_dict.get("vasprun_obj"),
            lobsterin_obj=input_dict.get("lobsterin_obj"),
            lobsterout_obj=input_dict.get("lobsterout_obj"),
            bandoverlaps_obj=input_dict.get("bandoverlaps_obj"),
            structure_obj=input_dict.get("structure_obj"),
            e_range=[-15, 0],
            dos_comparison=True,
            n_bins=256,
            bva_comp=True,
        )
        calc_quality_description = Description.get_calc_quality_description(
            calc_quality_dict
        )

        return " ".join(calc_quality_description)

    @staticmethod
    def get_lobster_local_envs(
        charge_obj, completecohp_obj, icohplist_obj, madelung_obj, which_bonds="all"
    ) -> str:
        """Get text description of local environments

        Args:
            input_dict: Dictionary containing the pymatgen objects.

        Returns:
            A string describing the local environments.
        """
        # Get the local environments using LobsterPy
        analyse = Analysis(
            charge_obj=charge_obj,
            madelung_obj=madelung_obj,
            icohplist_obj=icohplist_obj,
            completecohp_obj=completecohp_obj,
            path_to_poscar=None,
            path_to_icohplist=None,
            path_to_cohpcar=None,
            which_bonds=which_bonds,
            summed_spins=False,
        )

        envs = []  # list of local environments
        for site_ix, env in enumerate(analyse.lse.coordination_environments):
            if site_ix in analyse.seq_ineq_ions and env[0]["ce_symbol"]:
                # if env[0]["ce_symbol"]:
                data_list = []
                site_str = unicodeify_species(analyse.structure[site_ix].species_string)

                try:
                    data_list.extend(
                        [
                            ["Site", site_str],
                            [
                                "Environment",
                                Description._coordination_environment_to_text(
                                    env[0]["ce_symbol"]
                                ).capitalize(),
                            ],
                            ["IUPAC Symbol", env[0]["ce_symbol"]],
                            ["CSM", float(round(env[0]["csm"], 5))],
                        ]
                    )

                except KeyError:
                    data_list.extend(
                        [
                            ["Site", site_str],
                            [
                                "Environment",
                                Description._coordination_environment_to_text(
                                    env[0]["ce_symbol"]
                                ).capitalize(),
                            ],
                            ["IUPAC Symbol", env[0]["ce_symbol"]],
                            ["CSM", "NA"],
                        ]
                    )

                local_env_data = analyse.chemenv.get_nn_info(analyse.structure, site_ix)

                neighbour_sites = [i["site"] for i in local_env_data]
                central_site = analyse.structure[site_ix]
                neighbour_weights = [
                    i["edge_properties"]["ICOHP"] for i in local_env_data
                ]
                charges = [analyse.charge_obj.mulliken[site_ix]]
                charges.extend(
                    [
                        analyse.charge_obj.mulliken[i["site_index"]]
                        for i in local_env_data
                    ]
                )

                # Create a molecule object for the local environment
                # and add the charges as a site property
                mol = Molecule.from_sites([central_site, *neighbour_sites])
                mol = mol.get_centered_molecule()

                # Add the charges as a site property (hover text)
                mol = mol.add_site_property("charge", charges)

                mg = MoleculeGraph.with_empty_graph(
                    molecule=mol,
                    name="bond_strength",
                    edge_weight_name="ICOHP",
                    edge_weight_units="eV",
                )
                for i in range(1, len(mol)):
                    # Add the bond strength as an edge weight (hover text)
                    mg.add_edge(0, i, weight=neighbour_weights[i - 1])

                view = html.Div(
                    [
                        StructureMoleculeComponent(
                            struct_or_mol=mg,
                            disable_callbacks=True,
                            id=f"{analyse.structure.composition.reduced_formula}_site_{site_ix}",
                            scene_settings={
                                "enableZoom": False,
                                "defaultZoom": 0.6,
                            },
                        )._sub_layouts["struct"]
                    ],
                    style={"width": "300px", "height": "300px"},
                )

                data_list.append(["Interactive", view])

                envs.append(get_table(rows=data_list))

        envs_grouped = [envs[i : i + 2] for i in range(0, len(envs), 2)]
        # analysis_contents = [
        #    Columns([Column(e) for e in env_group]) for env_group in envs_grouped
        # ]
        analysis_contents = [
            Columns(
                [
                    Column(
                        html.Div(
                            e, style={"display": "flex", "justifyContent": "center"}
                        ),
                    )
                    for e in env_group
                ]
            )
            for env_group in envs_grouped
        ]

        return html.Div([html.Div(analysis_contents), html.Br()])

    @staticmethod
    def get_summary_text(
        charge_obj,
        completecohp_obj,
        icohplist_obj,
        dos,
        madelung_obj,
        which_bonds="all",
    ) -> str:
        """Get text description of bonding analysis and calculation quality

        Args:
            charge_obj:  pymatgen lobster.io.charge object.
            completecohp_obj: pymatgen.electronic_structure.cohp.CompleteCohp object
            icohplist_obj: pymatgen lobster.io.Icohplist object
            madelung_obj: pymatgen lobster.io.MadelungEnergies object
            which_bonds: Bonds to consider for the analysis.
            dos: pymatgen.electronic_structure.dos.LobsterCompleteDos object
            kwargs: Keyword arguments that get passed to InteractiveCohpPlotter.get_plot.
        Returns:
            A string describing the bonding analysis.
        """

        analyse = Analysis(
            charge_obj=charge_obj,
            madelung_obj=madelung_obj,
            icohplist_obj=icohplist_obj,
            completecohp_obj=completecohp_obj,
            path_to_poscar=None,
            path_to_icohplist=None,
            path_to_cohpcar=None,
            which_bonds=which_bonds,
            summed_spins=False,
        )

        description = Description(analysis_object=analyse)

        return " ".join(description.text)

        # return anaylsis_des

    @staticmethod
    def get_figure(
        charge_obj,
        completecohp_obj,
        icohplist_obj,
        dos,
        madelung_obj,
        dos_select="ap",
        energy_window=(-10.0, 5.0),
        which_bonds="all",
        **kwargs,
    ) -> go.Figure:
        """Get a COHP figure.

        Args:
            charge_obj:  pymatgen lobster.io.charge object.
            completecohp_obj: pymatgen.electronic_structure.cohp.CompleteCohp object
            icohplist_obj: pymatgen lobster.io.Icohplist object
            madelung_obj: pymatgen lobster.io.MadelungEnergies object
            kwargs: Keyword arguments that get passed to InteractiveCohpPlotter.get_plot.

        Returns:
            A plotly Figure object.
        """

        analyse = Analysis(
            charge_obj=charge_obj,
            madelung_obj=madelung_obj,
            icohplist_obj=icohplist_obj,
            completecohp_obj=completecohp_obj,
            path_to_poscar=None,
            path_to_icohplist=None,
            path_to_cohpcar=None,
            which_bonds=which_bonds,
            summed_spins=False,
        )

        description = Description(analysis_object=analyse)

        # Get the COHP plot
        cohp_fig = description.plot_interactive_cohps(
            ylim=[-10, 5], xlim=[-5, 5], hide=True
        )

        dos_traces = BandstructureAndDosComponent.get_dos_traces(
            dos=dos, energy_window=energy_window, dos_select=dos_select
        )

        fig = make_subplots(
            rows=1,
            cols=2,
            shared_yaxes=True,
            horizontal_spacing=0.05,
            column_widths=[0.6, 0.4],
        )

        # Adapt traces names and formatting to crystal-toolkit style
        for ix, trace in enumerate(cohp_fig.data):
            trace.visible = True
            trace.line.width = None
            if trace.line.dash:
                trace.line.dash = "dot"
            if trace.line.dash != "dot":
                trace.name = f"{cohp_fig.data[ix].name} (spin ↑)"
                legend_spin_down_name = trace.name.split(" (")
                cohp_fig.data[ix + 1].name = f"{legend_spin_down_name[0]} (spin ↓)"

            fig.add_trace(trace, row=1, col=1)

        for trace in dos_traces:
            fig.add_trace(trace, row=1, col=2)

        # Update axes layout to match Crystal Toolkit's aesthetic
        fig.update_layout(
            xaxis1=dict(
                title="COHP (eV)",
                range=[-5, 5],
                showgrid=False,
                linecolor="rgb(71,71,71)",
                mirror=True,
                domain=[0, 0.62],  # 60% width for COHP
            ),
            xaxis2=dict(
                title="DOS",
                showgrid=False,
                linecolor="rgb(71,71,71)",
                mirror=True,
                domain=[0.65, 1],  # 35% width for DOS
            ),
            yaxis=dict(
                title="E - E<sub>F</sub> (eV)",
                range=[-10, 5],
                showgrid=False,
                linecolor="rgb(71,71,71)",
                mirror=True,
            ),
            yaxis2=dict(
                range=[-10, 5], showgrid=False, linecolor="rgb(71,71,71)", mirror=True
            ),
            hovermode="closest",
            plot_bgcolor="rgba(230,230,230,230)",
            margin=dict(l=60, b=50, t=50, pad=0, r=30),
            # height=500,
            # width=1000,
            autosize=True,
            showlegend=True,
        )

        legend = dict(
            x=1.02,
            y=1.005,
            xanchor="left",
            yanchor="top",
            bordercolor="#333",
            borderwidth=2,
            traceorder="normal",
        )

        fig["layout"]["legend"] = legend

        return fig

    def generate_callbacks(self, app, cache) -> None:
        """Register callback functions for this component."""

        @app.callback(
            Output(self.id("cohp-dos-graph"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("analysis-mode"), "value"),
        )
        def update_graph(data, label_select):
            """Update the COHP and DOS graph."""

            # Get the data from the store
            completecohp_obj, charge_obj, icohplist_obj, madelung_obj, dos = (
                self._get_plot_inputs(data)
            )

            fig = self.get_figure(
                charge_obj=charge_obj,
                completecohp_obj=completecohp_obj,
                madelung_obj=madelung_obj,
                icohplist_obj=icohplist_obj,
                dos=dos,
                which_bonds=label_select
                if isinstance(label_select, str)
                else label_select[0],
            )

            return dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={"width": "100%"},
            )

        @app.callback(
            Output(self.id("analysis-description"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("analysis-mode"), "value"),
        )
        def update_text(data, label_select) -> MessageContainer:
            """Update the text description of the bonding analysis."""
            completecohp_obj, charge_obj, icohplist_obj, madelung_obj, dos = (
                self._get_plot_inputs(data)
            )

            analysis_description = self.get_summary_text(
                charge_obj=charge_obj,
                completecohp_obj=completecohp_obj,
                icohplist_obj=icohplist_obj,
                dos=dos,
                madelung_obj=madelung_obj,
                which_bonds=label_select
                if isinstance(label_select, str)
                else label_select[0],
            )

            lobsterpy_version = version("lobsterpy")

            repo_link = html.A(
                f"LobsterPy v{lobsterpy_version}",
                href="https://github.com/JaGeo/LobsterPy.git",
                style={"white-space": "nowrap"},
            )

            return MessageContainer(
                MessageBody([f"{analysis_description} - ", repo_link]),
                kind="dark",
                size="normal",
            )

        @app.callback(
            Output(self.id("local-env-lobsterpy"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("analysis-mode"), "value"),
        )
        def update_local_envs(data, label_select):
            """Update the local environments using LobsterEnv."""
            completecohp_obj, charge_obj, icohplist_obj, madelung_obj, _ = (
                self._get_plot_inputs(data)
            )

            return self.get_lobster_local_envs(
                charge_obj=charge_obj,
                completecohp_obj=completecohp_obj,
                icohplist_obj=icohplist_obj,
                madelung_obj=madelung_obj,
                which_bonds=label_select
                if isinstance(label_select, str)
                else label_select[0],
            )

            # return local_envs


class COHPAndDosPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cohp = CohpAndDosComponent()
        self.cohp.attach_from(self, this_store_name="mpid")

    @property
    def title(self) -> str:
        return "COHP and Density of States"

    @property
    def description(self) -> str:
        return "Display the COHP and density of states for this structure \
        if it has been calculated by the Materials Project."

    @property
    def initial_contents(self) -> html.Div:
        return html.Div(
            [
                super().initial_contents,
                html.Div([self.cohp.standard_layout], style={"display": "none"}),
            ]
        )

    def update_contents(self, new_store_contents, *args) -> html.Div:
        return self.cohp.standard_layout
