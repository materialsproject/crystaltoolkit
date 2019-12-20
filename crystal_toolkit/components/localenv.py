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
    get_tooltip,
    cite_me,
    PRIMARY_COLOR,
)
from crystal_toolkit.helpers.inputs import get_float_input

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
from pymatgen.util.string import unicodeify_species


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
                            {"label": "Chemenv Analysis", "value": "chemenv"},
                            {"label": "LocalEnv Analysis", "value": "localenv"},
                            {"label": "Bonding Graph", "value": "bondinggraph"},
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
                    "The Chemenv algorithm is developed by David Waroquiers et al. to analyze "
                    'local chemical environments. In this interactive app, the "SimplestChemenvStrategy" '
                    'and "LightStructureEnvironments" are used. For more powerful analysis, please use '
                    "the *pymatgen* code."
                )

                distance_cutoff = get_float_input(
                    id=self.id("distance_cutoff"),
                    default=1.4,
                    label="Distance cut-off",
                    help="Defines search radius by considering any atom within a radius "
                    "of the minimum nearest neighbor distance multiplied by the distance "
                    "cut-off.",
                )
                angle_cutoff = get_float_input(
                    id=self.id("angle_cutoff"),
                    default=0.3,
                    label="Angle cut-off",
                    help="Defines a tolerance whereby a neighbor atom is excluded if the solid angle "
                    "circumscribed by its Voronoi face is smaller than the angle tolerance "
                    "multiplied by the largest solid angle present in the crystal.",
                )

                return html.Div(
                    [
                        dcc.Markdown(description),
                        html.Br(),
                        cite_me(
                            manual_ref="Chemenv: A fast and robust coordination environment identification tool, "
                            "David Waroquiers et al. (2019)",
                            cite_text="Cite Chemenv Analysis",
                        ),
                        html.Br(),
                        distance_cutoff,
                        angle_cutoff,
                        html.Br(),
                        dcc.Loading(
                            id=self.id("chemenv_analysis"), color=PRIMARY_COLOR
                        ),
                    ]
                )

        @app.callback(
            Output(self.id("localenv_analysis"), "children"), [Input(self.id(), "data")]
        )
        def update_localenv_analysis(data):
            ...

        @app.callback(
            Output(self.id("chemenv_analysis"), "children"),
            [
                Input(self.id(), "data"),
                Input(self.id("distance_cutoff"), "value"),
                Input(self.id("angle_cutoff"), "value"),
            ],
        )
        def get_chemenv_analysis(struct, distance_cutoff, angle_cutoff):

            if not struct:
                raise PreventUpdate

            struct = self.from_data(struct).structure
            distance_cutoff = float(distance_cutoff)
            angle_cutoff = float(angle_cutoff)

            def get_valences(struct):
                valences = [getattr(site.specie, "oxi_state", None) for site in struct]
                valences = [v for v in valences if v is not None]
                if len(valences) == len(struct):
                    return valences
                else:
                    return "undefined"

            # decide which indices to present to user
            sga = SpacegroupAnalyzer(struct)
            symm_struct = sga.get_symmetrized_structure()
            inequivalent_indices = [
                indices[0] for indices in symm_struct.equivalent_indices
            ]
            wyckoffs = symm_struct.wyckoff_symbols

            lgf = LocalGeometryFinder()
            lgf.setup_structure(structure=struct)

            se = lgf.compute_structure_environments(
                maximum_distance_factor=distance_cutoff + 0.01,
                only_indices=inequivalent_indices,
                valences=get_valences(struct),
            )
            strategy = SimplestChemenvStrategy(
                distance_cutoff=distance_cutoff, angle_cutoff=angle_cutoff
            )
            lse = LightStructureEnvironments.from_structure_environments(
                strategy=strategy, structure_environments=se
            )
            all_ce = AllCoordinationGeometries()

            envs = []
            unknown_sites = []

            for index, wyckoff in zip(inequivalent_indices, wyckoffs):

                datalist = {
                    "Site": unicodeify_species(struct[index].species_string),
                    "Wyckoff Label": wyckoff,
                }

                if not lse.neighbors_sets[index]:
                    unknown_sites.append(f"{struct[index].species_string} ({wyckoff})")
                    continue

                # represent the local environment as a molecule
                mol = Molecule.from_sites(
                    [struct[index]] + lse.neighbors_sets[index][0].neighb_sites
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
                            id=f"{struct.composition.reduced_formula}_site_{index}",
                            scene_settings={"enableZoom": False, "defaultZoom": 0.6},
                        )._sub_layouts["struct"]
                    ],
                    style={"width": "300px", "height": "300px"},
                )

                env = lse.coordination_environments[index]
                co = all_ce.get_geometry_from_mp_symbol(env[0]["ce_symbol"])
                name = co.name
                if co.alternative_names:
                    name += f" (also known as {', '.join(co.alternative_names)})"

                datalist.update(
                    {
                        "Environment": name,
                        "IUPAC Symbol": co.IUPAC_symbol_str,
                        get_tooltip(
                            "CSM",
                            "The continuous symmetry measure (CSM) describes the similarity to an "
                            "ideal coordination environment. It can be understood as a 'distance' to "
                            "a shape and ranges from 0 to 100 in which 0 corresponds to a "
                            "coordination environment that is exactly identical to the ideal one. A "
                            "CSM larger than 5.0 already indicates a relatively strong distortion of "
                            "the investigated coordination environment.",
                        ): f"{env[0]['csm']:.2f}",
                        "Interactive View": view,
                    }
                )

                envs.append(get_data_list(datalist))

            # TODO: switch to tiles?
            envs_grouped = [envs[i : i + 2] for i in range(0, len(envs), 2)]
            analysis_contents = []
            for env_group in envs_grouped:
                analysis_contents.append(
                    Columns([Column(e, size=6) for e in env_group])
                )

            if unknown_sites:
                unknown_sites = html.Strong(
                    f"The following sites were not identified: {', '.join(unknown_sites)}. "
                    f"Please try changing the distance or angle cut-offs to identify these sites, "
                    f"or try an alternative algorithm such as LocalEnv."
                )
            else:
                unknown_sites = html.Span()

            return html.Div([html.Div(analysis_contents), html.Br(), unknown_sites])
