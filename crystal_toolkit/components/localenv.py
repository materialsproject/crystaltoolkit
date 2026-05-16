from __future__ import annotations

import itertools
from multiprocessing import cpu_count
from typing import TYPE_CHECKING
from warnings import warn

import dash_mp_components as mpc
from dash import callback_context, dcc, html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from monty.json import MontyDecoder
from pymatgen.analysis.chemenv.coordination_environments.chemenv_strategies import (
    SimplestChemenvStrategy,
)
from pymatgen.analysis.chemenv.coordination_environments.coordination_geometries import (
    AllCoordinationGeometries,
)
from pymatgen.analysis.chemenv.coordination_environments.coordination_geometry_finder import (
    LocalGeometryFinder,
)
from pymatgen.analysis.chemenv.coordination_environments.structure_environments import (
    LightStructureEnvironments,
)
from pymatgen.analysis.graphs import MoleculeGraph, StructureGraph
from pymatgen.analysis.lobster_env import LobsterNeighbors
from pymatgen.analysis.local_env import CN_OPT_PARAMS, LocalStructOrderParams
from pymatgen.core import Molecule, Structure
from pymatgen.ext.matproj import MPRester
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.util.string import unicodeify, unicodeify_species
from sklearn.preprocessing import normalize

from crystal_toolkit.components.structure import StructureMoleculeComponent
from crystal_toolkit.components.upload import LobsterEnvUploadComponent
from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import (
    H5,
    Column,
    Columns,
    Label,
    Loading,
    cite_me,
    get_table,
    get_tooltip,
)

if TYPE_CHECKING:
    from pymatgen.io.lobster import Charge, Icohplist

try:
    from dscribe.descriptors import SOAP
    from dscribe.kernels import REMatchKernel
except ImportError:
    no_soap_msg = (
        "Using dscribe SOAP and REMatchKernel requires the dscribe package "
        "which was made optional since it in turn requires numba and numba "
        "was a common source of installation issues."
    )
    SOAP = None


def _get_local_order_parameters(structure_graph, n):
    """A copy of the method in pymatgen.analysis.local_env which can operate on StructureGraph
    directly.

    Calculate those local structure order parameters for
    the given site whose ideal CN corresponds to the
    underlying motif (e.g., CN=4, then calculate the
    square planar, tetrahedral, see-saw-like,
    rectangular see-saw-like order parameters).

    Args:
        structure_graph: StructureGraph object
        n (int): site index.
    Returns (Dict[str, float]):
        A dict of order parameters (values) and the
        underlying motif type (keys; for example, tetrahedral).
    """
    # TODO: move me to pymatgen once stable

    # code from @nisse3000, moved here from graphs to avoid circular
    # import, also makes sense to have this as a general NN method
    cn = structure_graph.get_coordination_of_site(n)
    if cn in [int(k_cn) for k_cn in CN_OPT_PARAMS]:
        names = list(CN_OPT_PARAMS[cn])
        types = []
        params = []
        for name in names:
            types.append(CN_OPT_PARAMS[cn][name][0])
            tmp = (
                CN_OPT_PARAMS[cn][name][1] if len(CN_OPT_PARAMS[cn][name]) > 1 else None
            )
            params.append(tmp)
        lost_ops = LocalStructOrderParams(types, parameters=params)
        sites = [structure_graph.structure[n]] + [
            connected_site.site
            for connected_site in structure_graph.get_connected_sites(n)
        ]
        lost_op_vals = lost_ops.get_order_parameters(
            sites, 0, indices_neighs=list(range(1, cn + 1))
        )
        d = {}
        for idx, lost_op in enumerate(lost_op_vals):
            d[names[idx]] = lost_op
        return d
    return None


def _get_lobsterenv_inputs(data: dict):
    """Extract and deserialize lobsterenv inputs from data dict.

    Args:
        data: Dictionary containing obj_charge, obj_icohp, and structure

    Returns:
        Tuple of (structure, obj_icohp, obj_charge)

    Raises:
        ValueError: If charge and ICOHP data are not available.
    """
    data = data or {}

    obj_charge = data.get("obj_charge")
    obj_icohp = data.get("obj_icohp")
    struct = data.get("structure")

    if not obj_charge or not obj_icohp:
        raise ValueError(
            "LobsterEnv analysis requires LOBSTER outputs (ICOHP + charge data). "
            "Please provide `obj_icohp` and `obj_charge` in the component data."
        )

    if obj_charge and isinstance(obj_charge, dict):
        obj_charge = MontyDecoder().process_decoded(obj_charge)

    if obj_icohp and isinstance(obj_icohp, dict):
        obj_icohp = MontyDecoder().process_decoded(obj_icohp)

    if struct and isinstance(struct, dict):
        struct = MontyDecoder().process_decoded(struct)

    return struct, obj_icohp, obj_charge


def _extract_structure_from_data(data):
    """Extract structure from data, handling both simple structures and complex dicts.

    Args:
        data: Either a Structure/Molecule object or a dict containing structure key

    Returns:
        Structure or Molecule object
    """
    if not data:
        return None

    # If data is a dict with a structure key (lobsterenv format), extract it
    if isinstance(data, dict):
        if "structure" in data:
            struct = data.get("structure")
            if struct and isinstance(struct, dict):
                struct = MontyDecoder().process_decoded(struct)
            return struct
        # Otherwise it's a regular dict that might be serialized
        return MontyDecoder().process_decoded(data)

    # If it's already a Structure/Molecule, return as is
    return data


def _perform_lobsterenv_analysis(
    struct,
    obj_icohp: Icohplist,
    obj_charge: Charge,
    perc_strength_icohp: float,
    which_charge: str,
    only_cation_anion: bool,
    adapt_extremum: bool,
    noise_cutoff=1e-3,
):
    """Perform LobsterEnv local environment analysis.

    Args:
        struct: Structure object
        obj_icohp: pymatgen ICOHP/ICOBI/ICOOPLIST object
        obj_charge: pymatgen Charge object
        perc_strength_icohp: ICOHP cutoff percentage
        which_charge: Charge type ("Mulliken" or "Loewdin")
        only_cation_anion: Whether to only show cation-anion bonds
        adapt_extremum: Whether to adapt extremum to additional conditions
        noise_cutoff: Noise cutoff threshold for LOBSTER output (default: 1e-3)

    Returns:
        html.Div with the analysis results

    Raises:
        ValueError: If analysis fails
    """
    sga = SpacegroupAnalyzer(struct)
    symm_struct = sga.get_symmetrized_structure()
    inequivalent_indices = [indices[0] for indices in symm_struct.equivalent_indices]
    wyckoffs = symm_struct.wyckoff_symbols

    edge_weight_name = "ICOHP"
    edge_weight_units = ""
    if obj_icohp.are_coops:
        edge_weight_name = "ICOOP"
    elif obj_icohp.are_cobis:
        edge_weight_name = "ICOBI"
    else:
        edge_weight_units = "eV"

    edge_weight_name_mapping = {edge_weight_name: edge_weight_name}

    try:
        lobster_neighbors = LobsterNeighbors(
            icoxxlist_obj=obj_icohp,
            structure=struct,
            charge_obj=obj_charge,
            which_charge=which_charge,
            valences_from_charges=True,
            perc_strength_icohp=perc_strength_icohp,
            additional_condition=1 if only_cation_anion else 0,
            adapt_extremum_to_add_cond=adapt_extremum,
            are_coops=obj_icohp.are_coops,
            are_cobis=obj_icohp.are_cobis,
            noise_cutoff=noise_cutoff,
        )
    except ValueError as err:
        if (
            str(err) == "min() arg is an empty sequence"
            or str(err)
            == "All valences are equal to 0, additional_conditions 1, 3, 5 and 6 will not work"
        ) and only_cation_anion:
            raise ValueError(
                "No cations detected. Consider analyzing all bonds instead of only cation-anion bonds, "
                "or try adjusting the ICOHP cutoff percentage."
            ) from err
        raise ValueError(
            "LobsterEnv failed to initialize. Try adjusting the ICOHP cutoff percentage and retry."
        ) from err

    lse = lobster_neighbors.get_light_structure_environment(
        only_cation_environments=only_cation_anion, on_error="warn"
    )
    # except ValueError as err:
    #    raise ValueError(
    #        "LobsterEnv failed to determine local environments. Try adjusting the ICOHP cutoff percentage and retry."
    #    ) from err

    all_ce = AllCoordinationGeometries()
    envs = []

    for index, wyckoff in zip(inequivalent_indices, wyckoffs):
        env = lse.coordination_environments[index]
        if env[0]["ce_symbol"]:
            co = all_ce.get_geometry_from_mp_symbol(env[0]["ce_symbol"])

            datalist = [
                ["Site", unicodeify_species(struct[index].species_string)],
                ["Wyckoff Label", wyckoff],
            ]

            local_env_data = lobster_neighbors.get_nn_info(struct, index)

            # Get charges based on selected charge type
            charge_data = getattr(obj_charge, which_charge.lower(), obj_charge.mulliken)
            charges = [charge_data[index]]
            charges.extend([charge_data[i["site_index"]] for i in local_env_data])
            neighbour_weights = [i["edge_properties"]["ICOHP"] for i in local_env_data]

            # represent the local environment as a molecule
            mol = Molecule.from_sites(
                [struct[index], *lse.neighbors_sets[index][0].neighb_sites]
            )
            mol = mol.get_centered_molecule()

            # Add the charges as a site property (hover text)
            mol = mol.add_site_property("charge", charges)

            mg = MoleculeGraph.with_empty_graph(
                molecule=mol,
                name="bond_strength",
                edge_weight_name=edge_weight_name,
                edge_weight_units=edge_weight_units,
            )
            for i in range(1, len(mol)):
                mg.add_edge(0, i, weight=neighbour_weights[i - 1])

            view = html.Div(
                [
                    StructureMoleculeComponent(
                        struct_or_mol=mg,
                        disable_callbacks=True,
                        id=f"{struct.composition.reduced_formula}_site_{index}",
                        scene_settings={
                            "enableZoom": False,
                            "defaultZoom": 0.6,
                        },
                        site_get_scene_kwargs={
                            "edge_weight_name_mapping": edge_weight_name_mapping
                        },
                    )._sub_layouts["struct"]
                ],
                style={"width": "300px", "height": "300px"},
            )

            name = co.name
            if co.alternative_names:
                name += f" (also known as {', '.join(co.alternative_names)})"

            datalist.extend(
                [
                    ["Environment", name],
                    ["IUPAC Symbol", co.IUPAC_symbol_str],
                    [
                        get_tooltip(
                            "CSM",
                            "The continuous symmetry measure (CSM) describes the similarity to an "
                            "ideal coordination environment. It can be understood as a 'distance' to "
                            "a shape and ranges from 0 to 100 in which 0 corresponds to a "
                            "coordination environment that is exactly identical to the ideal one. A "
                            "CSM larger than 5.0 already indicates a relatively strong distortion of "
                            "the investigated coordination environment.",
                        ),
                        f"{env[0]['csm']:.2f}",
                    ],
                    ["Interactive View", view],
                ]
            )

            envs.append(get_table(rows=datalist))

    # Group environments in rows of 2
    envs_grouped = [envs[i : i + 2] for i in range(0, len(envs), 2)]
    analysis_contents = [
        Columns([Column(e, size=6) for e in env_group]) for env_group in envs_grouped
    ]

    return html.Div([html.Div(analysis_contents), html.Br()])


class LocalEnvironmentPanel(PanelComponent):
    """A panel to analyze the local chemical environments in a crystal."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.create_store("graph")
        self.create_store(
            "display_options",
            initial_data={"color_scheme": "Jmol", "color_scale": None},
        )
        # Create LobsterEnv upload component
        self.lobsterenv_upload = LobsterEnvUploadComponent(
            id=self.id("lobsterenv_upload")
        )

    @property
    def title(self) -> str:
        """Title of the panel."""
        return "Local Environments"

    @property
    def description(self) -> str:
        """Description of the panel."""
        return "Analyze the local chemical environments in your crystal."

    @property
    def loading_text(self):
        """Text to display while loading."""
        return "Analyzing environments"

    def contents_layout(self) -> html.Div:
        """HTML layout of the panel contents."""
        algorithm_choices = self.get_choice_input(
            label="Analysis method",
            kwarg_label="algorithm",
            state={"algorithm": "chemenv"},
            options=[
                {"label": "ChemEnv", "value": "chemenv"},
                {"label": "LocalEnv", "value": "localenv"},
                {"label": "LobsterEnv", "value": "lobsterenv"},
                {"label": "Bonding Graph", "value": "bondinggraph"},
                {"label": "SOAP", "value": "soap"},
            ],
            help_str="Choose an analysis method to examine the local chemical environment. "
            "Several methods exist and there is no guaranteed correct answer, so try multiple!",
        )

        analysis = html.Div(id=self.id("analysis"))

        return html.Div([algorithm_choices, html.Br(), analysis, html.Br()])

    @staticmethod
    def get_graph_data(graph, display_options):
        """Get the data for the graph visualization."""
        color_scheme = display_options.get("color_scheme", "Jmol")

        nodes = []
        edges = []

        struct_or_mol = StructureMoleculeComponent._get_struct_or_mol(graph)
        legend = Legend(struct_or_mol, color_scheme=color_scheme)

        for idx, node in enumerate(graph.graph.nodes()):
            # TODO: fix for disordered
            node_color = legend.get_color(
                struct_or_mol[node].species.elements[0], site=struct_or_mol[node]
            )

            nodes.append(
                {
                    "id": node,
                    "title": f"{struct_or_mol[node].species_string} site "
                    f"({graph.get_coordination_of_site(idx)} neighbors)",
                    "color": node_color,
                }
            )

        for u, v, d in graph.graph.edges(data=True):
            edge = {"from": u, "to": v, "arrows": ""}

            to_jimage = d.get("to_jimage", (0, 0, 0))

            # TODO: check these edge weights
            if isinstance(struct_or_mol, Structure):
                dist = struct_or_mol.get_distance(u, v, jimage=to_jimage)
            else:
                dist = struct_or_mol.get_distance(u, v)
            edge["length"] = 50 * dist

            if to_jimage != (0, 0, 0):
                edge["arrows"] = "to"
                label = f"{dist:.2f} Å to site at image vector {to_jimage}"
            else:
                label = f"{dist:.2f} Å between sites"

            if label:
                edge["title"] = label

            # if 'weight' in d:
            #   label += f" {d['weight']}"

            edges.append(edge)

        return {"nodes": nodes, "edges": edges}

    def generate_callbacks(self, app, cache) -> None:
        """Generate the callbacks for the panel interactions."""
        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("analysis"), "children"),
            Input(self.get_kwarg_id("algorithm"), "value"),
        )
        def run_algorithm(algorithm):
            algorithm = self.reconstruct_kwarg_from_state(
                callback_context.inputs, "algorithm"
            )

            if algorithm == "chemenv":
                state = {"distance_cutoff": 1.4, "angle_cutoff": 0.3}

                description = (
                    "The ChemEnv algorithm is developed by David Waroquiers et al. to analyze "
                    'local chemical environments. In this interactive app, the "SimplestChemenvStrategy" '
                    'and "LightStructureEnvironments" are used. For more powerful analysis, please use '
                    "the *pymatgen* code directly. Note that this analysis determines its own bonds independent "
                    "of those shown in the main crystal visualizer."
                )

                distance_cutoff = self.get_numerical_input(
                    label="Distance cut-off",
                    kwarg_label="distance_cutoff",
                    state=state,
                    help_str="Defines search radius by considering any atom within a radius "
                    "of the minimum nearest neighbor distance multiplied by the distance "
                    "cut-off.",
                    shape=(),
                )
                angle_cutoff = self.get_numerical_input(
                    label="Angle cut-off",
                    kwarg_label="angle_cutoff",
                    state=state,
                    help_str="Defines a tolerance whereby a neighbor atom is excluded if the solid angle "
                    "circumscribed by its Voronoi face is smaller than the angle tolerance "
                    "multiplied by the largest solid angle present in the crystal.",
                    shape=(),
                )

                return html.Div(
                    [
                        dcc.Markdown(description),
                        html.Br(),
                        cite_me(
                            cite_text="How to cite ChemEnv",
                            doi="10.1107/S2052520620007994",
                        ),
                        html.Br(),
                        distance_cutoff,
                        angle_cutoff,
                        html.Br(),
                        Loading(id=self.id("chemenv_analysis")),
                    ]
                )

            if algorithm == "localenv":
                description = (
                    "The LocalEnv algorithm is developed by Nils Zimmerman et al. whereby "
                    "an 'order parameter' is calculated that measures how well that "
                    "environment matches an ideal polyhedra. The order parameter "
                    "is a number from zero to one, with one being a perfect match."
                )

                return html.Div(
                    [
                        dcc.Markdown(description),
                        html.Br(),
                        cite_me(
                            cite_text="How to cite LocalEnv",
                            doi="10.3389/fmats.2017.00034",
                        ),
                        html.Br(),
                        Loading(id=self.id("localenv_analysis")),
                    ]
                )

            if algorithm == "lobsterenv":
                description = (
                    "The LobsterEnv algorithm is developed by George et al. to analyze "
                    "local chemical environments based on the outputs of LOBSTER calculations. "
                    "This analysis relies on the ICOHP values calculated by LOBSTER, which "
                    "are a measure of bond strength. The local environment is determined by including all neighbors "
                    "with ICOHP/ICOBI/ICOOP values stronger than a certain threshold. "
                    "The threshold can be set as a percentage of the strongest ICOHP/ICOBI/ICOOP in the structure, and can be adjusted using the slider below. "
                )

                lobsterenv_state = {
                    "lobsterenv-analysis-mode": "all",
                    "perc_strength_icohp": 0.15,
                    "which_charge": "Mulliken",
                    "adapt_extremum": True,
                    "noise_cutoff": 1e-3,
                }

                lobsterenv_analysis_options = [
                    {"label": "all", "value": "all"},
                    {"label": "cation-anion", "value": "cation-anion"},
                ]

                lobsterenv_analysis_mode = self.get_choice_input(
                    kwarg_label="lobsterenv-analysis-mode",
                    state=lobsterenv_state,
                    label="Analysis mode",
                    help_str="Choose whether to analyze all bonds or only cation-anion bonds",
                    options=lobsterenv_analysis_options,
                )

                charge_type_options = [
                    {"label": "Mulliken", "value": "Mulliken"},
                    {"label": "Loewdin", "value": "Loewdin"},
                ]

                charge_type = self.get_choice_input(
                    kwarg_label="which_charge",
                    state=lobsterenv_state,
                    label="Charge type",
                    help_str="Select the atomic charge type to use for the cation-anion classification",
                    options=charge_type_options,
                )

                icohp_cutoff = html.Div(
                    [
                        H5("Bond strength cutoff %"),
                        dcc.Slider(
                            id=self.id("perc_strength_icohp"),
                            min=0,
                            max=1,
                            step=0.01,
                            value=0.15,
                            marks={i: f"{i:.0%}" for i in [0, 0.25, 0.5, 0.75, 1]},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ],
                    style={"width": "100%"},
                )

                adapt_extremum = self.get_bool_input(
                    label="Adapt extremum to additional condition",
                    kwarg_label="adapt_extremum",
                    state=lobsterenv_state,
                    help_str="If enabled, adapts the ICOHP/ICOBI/ICOOP extremum based on additional conditions (cation-anion mode)",
                )

                noise_cutoff = self.get_numerical_input(
                    label="Noise cutoff",
                    kwarg_label="noise_cutoff",
                    state=lobsterenv_state,
                    help_str="Noise cutoff threshold for filtering small bond strength values",
                    shape=(),
                    min=0.0,
                )

                lobsterenv_controls = Columns(
                    [
                        Column([lobsterenv_analysis_mode, charge_type], size=3),
                        Column([icohp_cutoff], size=3),
                        Column([adapt_extremum, noise_cutoff], size=3),
                    ]
                )

                return html.Div(
                    [
                        cite_me(
                            cite_text="How to cite LobsterEnv",
                            doi="10.1002/cplu.202200123",
                        ),
                        html.Br(),
                        dcc.Markdown(description),
                        html.Br(),
                        # html.H5("Upload LOBSTER Results"),
                        self.lobsterenv_upload._sub_layouts["upload"],
                        html.Br(),
                        # html.H5("Analysis Parameters"),
                        # html.Br(),
                        lobsterenv_controls,
                        html.Br(),
                        Loading(id=self.id("lobsterenv_analysis")),
                    ]
                )

            if algorithm == "bondinggraph":
                description = (
                    "This is an alternative way to display the same bonds present in the "
                    "visualizer. Here, the bonding is displayed as a crystal graph, with "
                    "nodes as atoms and edges as bonds. The graph visualization is shown in an "
                    "abstract two-dimensional space."
                )

                return html.Div(
                    [
                        dcc.Markdown(description),
                        html.Br(),
                        Loading(id=self.id("bondinggraph_analysis")),
                    ]
                )

            if algorithm == "soap":
                state = {
                    "rcut": 5.0,
                    "nmax": 2,
                    "lmax": 2,
                    "sigma": 0.2,
                    "crossover": True,
                    "average": "off",
                    "rbf": "gto",
                    "alpha": 0.1,
                    "threshold": 1e-4,
                    "metric": "linear",
                    "normalize_kernel": True,
                }

                description = (
                    'The "Smooth Overlap of Atomic Positions" (SOAP) descriptor provides information on the local '
                    "atomic environment by encoding that environment as a power spectrum derived from the "
                    "spherical harmonics of atom-centered gaussian densities. The SOAP formalism is complex but is "
                    "described well in [Bartók et al.](https://doi.org/10.1103/PhysRevB.87.184115) "
                    "and the REMatch similarity kernel in [De et al.](https://doi.org/10.1039/c6cp00415f) "
                    "The implementation of SOAP in this "
                    "web app is provided by [DScribe](https://doi.org/10.1016/j.cpc.2019.106949).  "
                    ""
                    "SOAP kernels are commonly used in machine learning applications. This interface is provided to "
                    "help gain intuition and exploration of the behavior of SOAP kernels."
                )

                rcut = self.get_numerical_input(
                    label="Radial cut-off /Å",
                    kwarg_label="rcut",
                    state=state,
                    help_str="The radial cut-off that defines the local region being considered",
                    shape=(),
                    min=1.0001,
                )

                nmax = self.get_numerical_input(
                    label="N max.",
                    kwarg_label="nmax",
                    state=state,
                    help_str="Number of radial basis functions",
                    shape=(),
                    is_int=True,
                    min=1,
                    max=9,
                )

                lmax = self.get_numerical_input(
                    label="L max.",
                    kwarg_label="lmax",
                    state=state,
                    help_str="Maximum degree of spherical harmonics",
                    shape=(),
                    is_int=True,
                    min=1,
                    max=9,
                )

                sigma = self.get_numerical_input(
                    label="Sigma",
                    kwarg_label="sigma",
                    state=state,
                    help_str="The standard deviation of gaussians used to build atomic density",
                    shape=(),
                    min=0.00001,
                )

                rbf = self.get_choice_input(
                    label="Radial basis function",
                    kwarg_label="rbf",
                    state=state,
                    help_str="Polynomial basis is faster, spherical gaussian based was used in original formulation",
                    options=[
                        {"label": "Spherical gaussian basis", "value": "gto"},
                        {"label": "Polynomial basis", "value": "polynomial"},
                    ],
                    style={"width": "16rem"},  # TODO: remove in-line style
                )

                crossover = self.get_bool_input(
                    label="Crossover",
                    kwarg_label="crossover",
                    state=state,
                    help_str="If enabled, the power spectrum will include all combinations of elements present.",
                )

                average = self.get_choice_input(
                    label="Average",
                    kwarg_label="average",
                    state=state,
                    help_str="The averaging mode over the centers of interest",
                    options=[
                        {"label": "No averaging", "value": "off"},
                        {
                            "label": "Inner: Averaging over sites before summing up the magnetic quantum numbers",
                            "value": "inner",
                        },
                        {
                            "label": "Outer: Averaging over the power spectrum of different sites",
                            "value": "outer",
                        },
                    ],
                    style={"width": "16rem"},  # TODO: remove in-line style
                )

                alpha = self.get_numerical_input(
                    label="Alpha",
                    kwarg_label="alpha",
                    state=state,
                    help_str="Determines the entropic penalty in the REMatch kernel. As alpha goes to infinity, the "
                    "behavior of the REMatch kernel matches the behavior of the kernel where SOAP vectors "
                    "are averaged across all sites. As alpha goes to zero, the kernel matches the best match "
                    "kernel.",
                    shape=(),
                    min=0.00001,
                )

                threshold = self.get_numerical_input(
                    label="Sinkhorn threshold",
                    kwarg_label="threshold",
                    state=state,
                    help_str="Convergence threshold for the Sinkhorn algorithm. If values are too small, convergence "
                    "may not be possible, and calculation time will increase.",
                    shape=(),
                )

                metric = self.get_choice_input(
                    label="Metric",
                    kwarg_label="metric",
                    state=state,
                    help_str='See scikit-learn\'s documentation on "Pairwise metrics, Affinities and Kernels" '
                    "for an explanation of available metrics.",
                    options=[
                        # {"label": "Additive χ2", "value": "additive_chi2"},  # these seem to be unstable
                        # {"label": "Exponential χ2", "value": "chi2"},
                        {"label": "Linear", "value": "linear"},
                        {"label": "Polynomial", "value": "polynomial"},
                        {"label": "Radial basis function", "value": "rbf"},
                        {"label": "Laplacian", "value": "laplacian"},
                        {"label": "Sigmoid", "value": "sigmoid"},
                        {"label": "Cosine", "value": "cosine"},
                    ],
                    style={"width": "16rem"},  # TODO: remove in-line style
                )

                _normalize_kernel = self.get_bool_input(
                    label="Normalize",
                    kwarg_label="normalize_kernel",
                    state=state,
                    help_str="Whether or not to normalize the resulting similarity kernel.",
                )

                # metric_kwargs = self.get_dict_input()

                return html.Div(
                    [
                        dcc.Markdown(description),
                        html.Br(),
                        H5("SOAP parameters"),
                        rcut,
                        nmax,
                        lmax,
                        sigma,
                        rbf,
                        crossover,
                        average,
                        html.Br(),  # TODO: remove all html.Br(), add appropriate styles instead
                        html.Br(),
                        html.Div(id=self.id("soap_analysis")),
                        html.Br(),
                        html.Br(),
                        H5("Similarity metric parameters"),
                        html.Div(
                            "This will calculate structural similarity scores from materials in the "
                            "Materials Project in the same chemical system. Note that for large chemical "
                            "systems this step can take several minutes."
                        ),
                        html.Br(),
                        alpha,
                        threshold,
                        metric,
                        # normalize_kernel,
                        html.Br(),
                        html.Br(),
                        Loading(id=self.id("soap_similarities")),
                    ]
                )
            return None

        def _get_soap_graph(feature, label):
            spectrum = {
                "data": [
                    {
                        "coloraxis": "coloraxis",
                        # 'hovertemplate': 'x: %{x}<br>y: %{y}<br>color: %{z}<extra></extra>',
                        "type": "heatmap",
                        "z": feature.tolist(),
                    }
                ]
            }

            spectrum["layout"] = {
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "coloraxis": {
                    "colorscale": [
                        [0.0, "#0d0887"],
                        [0.1111111111111111, "#46039f"],
                        [0.2222222222222222, "#7201a8"],
                        [0.3333333333333333, "#9c179e"],
                        [0.4444444444444444, "#bd3786"],
                        [0.5555555555555556, "#d8576b"],
                        [0.6666666666666666, "#ed7953"],
                        [0.7777777777777778, "#fb9f3a"],
                        [0.8888888888888888, "#fdca26"],
                        [1.0, "#f0f921"],
                    ],
                    "showscale": False,
                },
                "margin": {"l": 0, "b": 0, "t": 0, "r": 0, "pad": 0},
                # "height": 20*feature.shape[0],  # for fixed size plots
                # "width": 20*feature.shape[1]
            }

            return Columns(
                [
                    Column(Label(label), size="1"),
                    Column(
                        dcc.Graph(
                            figure=spectrum,
                            config={"displayModeBar": False},
                            responsive=True,
                            style={"height": "60px"},
                        )
                    ),
                ]
            )

        @app.callback(
            Output(self.id("soap_analysis"), "children"),
            Input(self.id(), "data"),
            Input(self.get_all_kwargs_id(), "value"),
        )
        def update_soap_analysis(struct, all_kwargs):
            if not struct:
                raise PreventUpdate

            if not SOAP:
                warn(no_soap_msg)
                return mpc.Markdown(
                    "This feature will not work unless `dscribe` is installed on the server."
                )

            struct = _extract_structure_from_data(struct)
            if not struct:
                raise PreventUpdate

            kwargs = self.reconstruct_kwargs_from_state(callback_context.inputs)

            # TODO: make sure is_int kwarg information is enforced so that int() conversion is unnecessary
            desc = SOAP(
                species=[e.number for e in struct.composition.elements],
                sigma=kwargs["sigma"],
                rcut=kwargs["rcut"],
                nmax=int(kwargs["nmax"]),
                lmax=int(kwargs["lmax"]),
                periodic=True,
                crossover=kwargs["crossover"],
                sparse=False,
                average=kwargs["average"],
            )

            adaptor = AseAtomsAdaptor()
            atoms = adaptor.get_atoms(struct)

            # make a 2D vector even when it is averaged
            soap_output = desc.create(atoms, n_jobs=cpu_count())
            soap_output = soap_output.reshape((-1, soap_output.shape[-1]))
            feature = normalize(soap_output)

            return _get_soap_graph(feature, "SOAP vector for this material")

        @cache.memoize(timeout=360)
        def _get_all_structs_from_elements(elements):
            structs = {}
            all_chemsys = [
                "-".join(sorted(els))
                for idx in range(len(elements))
                for els in itertools.combinations(elements, idx + 1)
            ]
            with MPRester() as mpr:
                docs = mpr.query(
                    {"chemsys": {"$in": all_chemsys}}, ["task_id", "structure"]
                )
            structs.update({d["task_id"]: d["structure"] for d in docs})
            return structs

        @app.callback(
            Output(self.id("soap_similarities"), "children"),
            Input(self.id(), "data"),
            Input(self.get_all_kwargs_id(), "value"),
        )
        def update_soap_similarities(struct, all_kwargs):
            if not struct:
                raise PreventUpdate

            if not SOAP:
                warn(no_soap_msg)
                return mpc.Markdown(
                    "This feature will not work unless `dscribe` is installed on the server."
                )

            struct = _extract_structure_from_data(struct)
            if not struct:
                raise PreventUpdate

            structs = {"input": struct}
            kwargs = self.reconstruct_kwargs_from_state(callback_context.inputs)

            elements = [str(el) for el in structs["input"].composition.elements]
            structs.update(_get_all_structs_from_elements(elements))

            if not structs:
                raise PreventUpdate

            elements = {
                elem for s in structs.values() for elem in s.composition.elements
            }
            # TODO: make sure is_int kwarg information is enforced so that int() conversion is unnecessary
            desc = SOAP(
                species=[e.number for e in elements],
                sigma=kwargs["sigma"],
                rcut=kwargs["rcut"],
                nmax=int(kwargs["nmax"]),
                lmax=int(kwargs["lmax"]),
                periodic=True,
                crossover=kwargs["crossover"],
                sparse=False,
                average=kwargs["average"],
            )

            adaptor = AseAtomsAdaptor()
            atomss = {
                mpid: adaptor.get_atoms(struct) for mpid, struct in structs.items()
            }

            print(f"Calculating {len(atomss)} SOAP vectors")
            features = {}
            for mpid, atoms in atomss.items():
                # make a 2D vector even when it is averaged
                soap_output = desc.create(atoms, n_jobs=cpu_count())
                soap_output = soap_output.reshape((-1, soap_output.shape[-1]))
                feature = normalize(soap_output)
                features[mpid] = feature

            re = REMatchKernel(
                metric=kwargs["metric"],
                alpha=kwargs["alpha"],
                threshold=kwargs["threshold"],
                # normalize_kernel=kwargs["normalize_kernel"],
            )

            print("Calculating similarity kernel")
            similarities = {
                mpid: re.get_global_similarity(
                    re.get_pairwise_matrix(features["input"], feature)
                )
                for mpid, feature in features.items()
                if mpid != "input"
            }

            sorted_mpids = sorted(similarities, key=lambda x: -similarities[x])

            print("Generating similarity graphs")
            # TODO: was much slower using px.imshow (see prev commit)
            all_graphs = [
                _get_soap_graph(
                    features[mpid],
                    [
                        html.Span(
                            f"{unicodeify(structs[mpid].composition.reduced_formula)}"
                        ),
                        dcc.Markdown(f"[{mpid}](https://materialsproject.org/{mpid})"),
                        html.Span(f"{similarities[mpid]:.5f}"),
                    ],
                )
                for mpid in sorted_mpids
            ]

            print("Returning similarity graphs")
            return html.Div(all_graphs)

        @app.callback(
            Output(self.id("localenv_analysis"), "children"),
            Input(self.id("graph"), "data"),
        )
        def update_localenv_analysis(graph):
            if not graph:
                raise PreventUpdate

            graph = self.from_data(graph)

            return html.Div(
                [
                    str(_get_local_order_parameters(graph, 0)),
                    html.Br(),
                    html.Small("This functionality is still under development."),
                ]
            )

        @app.callback(
            Output(self.id("lobsterenv_analysis"), "children"),
            Input(self.id(), "data"),
            Input(self.lobsterenv_upload.id(), "data"),
            Input(self.id("perc_strength_icohp"), "value"),
            Input(self.get_kwarg_id("lobsterenv-analysis-mode"), "value"),
            Input(self.get_kwarg_id("which_charge"), "value"),
            Input(self.get_kwarg_id("adapt_extremum"), "value"),
            Input(self.get_kwarg_id("noise_cutoff"), "value"),
        )
        def update_lobsterenv_analysis(
            data,
            uploaded_data,
            perc_strength_icohp,
            analysis_mode,
            which_charge,
            adapt_extremum,
            noise_cutoff,
        ):
            """Generate LobsterEnv local environment analysis."""
            # Prioritize uploaded data over component data
            if (
                uploaded_data
                and uploaded_data.get("obj_icohp")
                and not uploaded_data.get("error")
            ):
                data = uploaded_data

            if not data:
                raise PreventUpdate

            # Handle slider value
            if isinstance(perc_strength_icohp, list):
                perc_strength_icohp = (
                    float(perc_strength_icohp[0]) if perc_strength_icohp else 0.15
                )
            else:
                perc_strength_icohp = (
                    float(perc_strength_icohp)
                    if perc_strength_icohp is not None
                    else 0.15
                )

            # Handle charge type
            which_charge = (
                which_charge[0]
                if isinstance(which_charge, list)
                else (which_charge or "Mulliken")
            )

            # Handle adapt_extremum
            adapt_extremum = (
                adapt_extremum[0]
                if isinstance(adapt_extremum, list)
                else (adapt_extremum if adapt_extremum is not None else True)
            )

            # Handle noise_cutoff
            noise_cutoff = (
                float(noise_cutoff[0])
                if isinstance(noise_cutoff, list)
                else (float(noise_cutoff) if noise_cutoff is not None else 1e-3)
            )

            try:
                struct, obj_icohp, obj_charge = _get_lobsterenv_inputs(data)
            except ValueError as e:
                return mpc.Markdown(str(e))

            if (
                not isinstance(data, dict)
                or "obj_icohp" not in data
                or "obj_charge" not in data
            ):
                return mpc.Markdown(
                    "LobsterEnv requires LOBSTER outputs (ICOHP + charge data). "
                    "Please provide `obj_icohp` and `obj_charge` in the component data or upload LOBSTER files."
                )

            # Determine if we should only show cation-anion bonds
            only_cation_anion = (
                analysis_mode == "cation-anion"
                if isinstance(analysis_mode, str)
                else analysis_mode[0] == "cation-anion"
            )

            try:
                return _perform_lobsterenv_analysis(
                    struct,
                    obj_icohp,
                    obj_charge,
                    perc_strength_icohp,
                    which_charge,
                    only_cation_anion,
                    adapt_extremum,
                    noise_cutoff,
                )
            except ValueError as e:
                return mpc.Markdown(str(e))

        @app.callback(
            Output(self.id("bondinggraph_analysis"), "children"),
            Input(self.id("graph"), "data"),
            Input(self.id("display_options"), "data"),
        )
        def update_bondinggraph_analysis(graph, display_options):
            if not graph:
                raise PreventUpdate

            graph = self.from_data(graph)
            display_options = self.from_data(display_options)

            graph_data = self.get_graph_data(graph, display_options)

            options = {
                "interaction": {
                    "hover": True,
                    "tooltipDelay": 0,
                    "zoomView": False,
                    "dragView": False,
                },
                "edges": {
                    "smooth": {"type": "dynamic"},
                    "length": 250,
                    "color": {"inherit": "both"},
                },
                "physics": {
                    "solver": "forceAtlas2Based",
                    "forceAtlas2Based": {"avoidOverlap": 1.0},
                    "stabilization": {"fit": True},
                },
            }

            return html.Div(
                [mpc.GraphComponent(graph=graph_data, options=options)],
                style={"width": "65vmin", "height": "65vmin"},
            )

        @app.callback(
            Output(self.id("chemenv_analysis"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("distance_cutoff"), "value"),
            Input(self.get_kwarg_id("angle_cutoff"), "value"),
        )
        def get_chemenv_analysis(struct, distance_cutoff, angle_cutoff):
            if not struct:
                raise PreventUpdate

            struct = _extract_structure_from_data(struct)
            if not struct:
                raise PreventUpdate

            kwargs = self.reconstruct_kwargs_from_state(callback_context.inputs)
            distance_cutoff = kwargs["distance_cutoff"]
            angle_cutoff = kwargs["angle_cutoff"]

            # TODO: remove these brittle guard statements, figure out more robust way to handle multiple input types
            if isinstance(struct, StructureGraph):
                struct = struct.structure

            def get_valences(struct):
                valences = [getattr(site.specie, "oxi_state", None) for site in struct]
                valences = [v for v in valences if v is not None]
                if len(valences) == len(struct):
                    return valences
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
                datalist = [
                    ["Site", unicodeify_species(struct[index].species_string)],
                    ["Wyckoff Label", wyckoff],
                ]

                if not lse.neighbors_sets[index]:
                    unknown_sites.append(f"{struct[index].species_string} ({wyckoff})")
                    continue

                # represent the local environment as a molecule
                mol = Molecule.from_sites(
                    [struct[index], *lse.neighbors_sets[index][0].neighb_sites]
                )
                mol = mol.get_centered_molecule()
                mg = MoleculeGraph.with_empty_graph(molecule=mol)
                for i in range(1, len(mol)):
                    mg.add_edge(0, i)

                view = html.Div(
                    [
                        StructureMoleculeComponent(
                            struct_or_mol=mg,
                            disable_callbacks=True,
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

                datalist.extend(
                    [
                        ["Environment", name],
                        ["IUPAC Symbol", co.IUPAC_symbol_str],
                        [
                            get_tooltip(
                                "CSM",
                                "The continuous symmetry measure (CSM) describes the similarity to an "
                                "ideal coordination environment. It can be understood as a 'distance' to "
                                "a shape and ranges from 0 to 100 in which 0 corresponds to a "
                                "coordination environment that is exactly identical to the ideal one. A "
                                "CSM larger than 5.0 already indicates a relatively strong distortion of "
                                "the investigated coordination environment.",
                            ),
                            f"{env[0]['csm']:.2f}",
                        ],
                        ["Interactive View", view],
                    ]
                )

                envs.append(get_table(rows=datalist))

            # TODO: switch to tiles?
            envs_grouped = [envs[i : i + 2] for i in range(0, len(envs), 2)]
            analysis_contents = [
                Columns([Column(e, size=6) for e in env_group])
                for env_group in envs_grouped
            ]

            if unknown_sites:
                unknown_sites = html.Strong(
                    f"The following sites were not identified: {', '.join(unknown_sites)}. "
                    f"Please try changing the distance or angle cut-offs to identify these sites, "
                    f"or try an alternative algorithm such as LocalEnv."
                )
            else:
                unknown_sites = html.Span()

            return html.Div([html.Div(analysis_contents), html.Br(), unknown_sites])
