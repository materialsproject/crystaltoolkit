import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


from crystal_toolkit.core.panelcomponent import PanelComponent, PanelComponent2
from crystal_toolkit.helpers.layouts import (
    MessageContainer,
    MessageBody,
    Label,
    H4,
    get_data_list,
    Columns,
    Column,
)

from crystal_toolkit.components.structure import StructureMoleculeComponent

from pymatgen.analysis.chemenv.coordination_environments.coordination_geometries import (
    AllCoordinationGeometries,
)
from pymatgen.analysis.chemenv.coordination_environments.coordination_geometry_finder import (
    LocalGeometryFinder,
)
from pymatgen.analysis.chemenv.coordination_environments.chemenv_strategies import (
    SimplestChemenvStrategy,
    MultiWeightsChemenvStrategy,
)
from pymatgen.analysis.chemenv.coordination_environments.structure_environments import (
    LightStructureEnvironments,
)

from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core.structure import Molecule
from pymatgen.analysis.graphs import MoleculeGraph


class LocalEnvironmentPanel(PanelComponent2):
    @property
    def title(self):
        return "Local Environments"

    @property
    def description(self):
        return "Analyze the local chemical environments in your crystal."

    @property
    def loading_text(self):
        return "Analyzing environments"

    def generate_callbacks(self, app, cache):

        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("inner_contents"), "children"), [Input(self.id(), "data")]
        )
        def add_initial_layout(data):

            algorithm_choices = html.Div(
                [
                    Label("Algorithm:"),
                    dcc.RadioItems(
                        id=self.id("algorithm"),
                        options=[
                            {"label": "ChemEnv", "value": "chemenv"},
                            {"label": "LocalEnv", "value": "localenv"},
                        ],
                        inputClassName="mpc-radio",
                        labelClassName="mpc-radio",
                        value="chemenv",
                    ),
                ]
            )

            analysis = html.Div(id=self.id("analysis"))

            return html.Div([algorithm_choices, html.Br(), analysis, html.Br()])

        @app.callback(
            Output(self.id("analysis"), "children"),
            [Input(self.id("algorithm"), "value")],
            [State(self.id(), "data")],
        )
        def run_algorithm(algorithm, struct):

            if not struct:
                raise PreventUpdate

            if algorithm != "chemenv":
                return html.Div(
                    "Not available on the web yet, use the pymatgen code to run this analysis."
                )

            struct = self.from_data(struct)

            if algorithm == "chemenv":

                description = (
                    "The ChemEnv algorithm is developed by ... et al ... "
                    "This interactive version uses sensible defaults, but for "
                    "more powerful options please consult the code."
                )

                description = ""

                return html.Div(
                    [html.Div(description), html.Br(), get_chemenv_analysis(struct)]
                )

        def get_chemenv_analysis(struct, distance_cutoff=1.41, angle_cutoff=0.3):

            lgf = LocalGeometryFinder()
            lgf.setup_structure(structure=struct)

            se = lgf.compute_structure_environments(
                maximum_distance_factor=distance_cutoff
            )
            strategy = SimplestChemenvStrategy(
                distance_cutoff=distance_cutoff, angle_cutoff=angle_cutoff
            )
            lse = LightStructureEnvironments.from_structure_environments(
                strategy=strategy, structure_environments=se
            )
            all_ce = AllCoordinationGeometries()

            # decide which indices to present to user
            sga = SpacegroupAnalyzer(struct)
            symm_struct = sga.get_symmetrized_structure()
            equivalent_indices = symm_struct.equivalent_indices
            wyckoffs = symm_struct.wyckoff_symbols

            envs = []
            unknown_sites = []

            for indices, wyckoff in zip(equivalent_indices, wyckoffs):

                idx = indices[0]
                datalist = {
                    "Site": struct[idx].species_string,
                    "Wyckoff Label": wyckoff,
                }

                if not lse.neighbors_sets[idx]:
                    unknown_sites.append(f"{struct[idx].species_string} ({wyckoff})")
                    continue

                # represent the local environment as a molecule
                mol = Molecule.from_sites(
                    [struct[idx]] + lse.neighbors_sets[idx][0].neighb_sites
                )
                mol = mol.get_centered_molecule()
                mg = MoleculeGraph.with_empty_graph(molecule=mol)
                for i in range(1, len(mol)):
                    mg.add_edge(0, i)

                view = html.Div(
                    [
                        StructureMoleculeComponent(
                            struct_or_mol=mg,
                            static=True,
                            id=f"site_{idx}",
                            scene_settings={"enableZoom": False, "defaultZoom": 0.6},
                        ).all_layouts["struct"]
                    ],
                    style={"width": "300px", "height": "300px"},
                )

                env = lse.coordination_environments[idx]
                co = all_ce.get_geometry_from_mp_symbol(env[0]["ce_symbol"])
                name = co.name
                if co.alternative_names:
                    name += f" (also known as {', '.join(co.alternative_names)})"

                datalist.update(
                    {
                        "Environment": name,
                        "IUPAC Symbol": co.IUPAC_symbol_str,
                        "CSM": f"{env[0]['csm']:.2f}%",
                        "Interactive View": view,
                    }
                )

                envs.append(get_data_list(datalist))

            # TODO: switch to tiles?
            envs_grouped = [envs[i : i + 2] for i in range(0, len(envs), 2)]
            analysis_contents = []
            for env_group in envs_grouped:
                analysis_contents.append(Columns([Column(e) for e in env_group]))

            unknown_sites = html.Div(
                f"The following sites were not identified: {', '.join(unknown_sites)}"
            )

            return html.Div([analysis_contents, html.Br(), unknown_sites])
