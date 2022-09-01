import itertools
from multiprocessing import cpu_count

import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash import callback_context
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from dash_mp_components import GraphComponent
from dscribe.descriptors import SOAP
from dscribe.kernels import REMatchKernel
from pymatgen.ext.matproj import MPRester
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
from pymatgen.analysis.graphs import MoleculeGraph
from pymatgen.analysis.graphs import StructureGraph
from pymatgen.analysis.local_env import cn_opt_params, LocalStructOrderParams
from pymatgen.core.structure import Molecule, Structure
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.util.string import unicodeify_species, unicodeify
from sklearn.preprocessing import normalize

from crystal_toolkit.components.structure import StructureMoleculeComponent
from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import (
    get_data_list,
    Columns,
    Column,
    get_tooltip,
    cite_me,
    Loading,
    H5,
    Label,
)


def _get_local_order_parameters(structure_graph, n):
    """
    A copy of the method in pymatgen.analysis.local_env which
    can operate on StructureGraph directly.

    Calculate those local structure order parameters for
    the given site whose ideal CN corresponds to the
    underlying motif (e.g., CN=4, then calculate the
    square planar, tetrahedral, see-saw-like,
    rectangular see-saw-like order paramters).
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
    if cn in [int(k_cn) for k_cn in cn_opt_params.keys()]:
        names = [k for k in cn_opt_params[cn].keys()]
        types = []
        params = []
        for name in names:
            types.append(cn_opt_params[cn][name][0])
            tmp = (
                cn_opt_params[cn][name][1] if len(cn_opt_params[cn][name]) > 1 else None
            )
            params.append(tmp)
        lostops = LocalStructOrderParams(types, parameters=params)
        sites = [structure_graph.structure[n]] + [
            connected_site.site
            for connected_site in structure_graph.get_connected_sites(n)
        ]
        lostop_vals = lostops.get_order_parameters(
            sites, 0, indices_neighs=[i for i in range(1, cn + 1)]
        )
        d = {}
        for i, lostop in enumerate(lostop_vals):
            d[names[i]] = lostop
        return d
    else:
        return None


class LocalEnvironmentPanel(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("graph")
        self.create_store(
            "display_options",
            initial_data={"color_scheme": "Jmol", "color_scale": None},
        )

    @property
    def title(self):
        return "Local Environments"

    @property
    def description(self):
        return "Analyze the local chemical environments in your crystal."

    @property
    def loading_text(self):
        return "Analyzing environments"

    def contents_layout(self) -> html.Div:

        algorithm_choices = self.get_choice_input(
            label="Analysis method",
            kwarg_label="algorithm",
            state={"algorithm": "chemenv"},
            options=[
                {"label": "ChemEnv", "value": "chemenv"},
                {"label": "LocalEnv", "value": "localenv"},
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

    def generate_callbacks(self, app, cache):

        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("analysis"), "children"),
            [Input(self.get_kwarg_id("algorithm"), "value")],
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
                            doi="10.26434/chemrxiv.11294480.v1",
                        ),
                        html.Br(),
                        distance_cutoff,
                        angle_cutoff,
                        html.Br(),
                        Loading(id=self.id("chemenv_analysis")),
                    ]
                )

            elif algorithm == "localenv":

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

            elif algorithm == "bondinggraph":

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

            elif algorithm == "soap":

                state = {
                    "rcut": 5.0,
                    "nmax": 2,
                    "lmax": 2,
                    "sigma": 0.2,
                    "crossover": True,
                    "average": False,
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

                average = self.get_bool_input(
                    label="Average",
                    kwarg_label="average",
                    state=state,
                    help_str="If enabled, the SOAP vector will be averaged across all sites.",
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

                normalize_kernel = self.get_bool_input(
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

        def _get_soap_graph(feature, label):

            spectrum = {
                "data": [
                    {
                        "coloraxis": "coloraxis",
                        #'hovertemplate': 'x: %{x}<br>y: %{y}<br>color: %{z}<extra></extra>',
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
            [Input(self.id(), "data"), Input(self.get_all_kwargs_id(), "value")],
        )
        def update_soap_analysis(struct, all_kwargs):

            if not struct:
                raise PreventUpdate

            struct = self.from_data(struct)
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
            feature = normalize(desc.create(atoms, n_jobs=cpu_count()))

            return _get_soap_graph(feature, "SOAP vector for this material")

        @cache.memoize(timeout=360)
        def _get_all_structs_from_elements(elements):
            structs = {}
            all_chemsyses = []
            for i in range(len(elements)):
                for els in itertools.combinations(elements, i + 1):
                    all_chemsyses.append("-".join(sorted(els)))

            with MPRester() as mpr:
                docs = mpr.query(
                    {"chemsys": {"$in": all_chemsyses}}, ["task_id", "structure"],
                )
            structs.update({d["task_id"]: d["structure"] for d in docs})
            return structs

        @app.callback(
            Output(self.id("soap_similarities"), "children"),
            [Input(self.id(), "data"), Input(self.get_all_kwargs_id(), "value")],
        )
        def update_soap_similarities(struct, all_kwargs):

            if not struct:
                raise PreventUpdate

            structs = {"input": self.from_data(struct)}
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
            features = {
                mpid: normalize(desc.create(atoms, n_jobs=cpu_count()))
                for mpid, atoms in atomss.items()
            }

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

            sorted_mpids = sorted(similarities.keys(), key=lambda x: -similarities[x])

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
            [Input(self.id("graph"), "data")],
        )
        def update_localenv_analysis(graph):

            if not graph:
                raise PreventUpdate

            graph = self.from_data(graph)

            return html.Div([str(_get_local_order_parameters(graph, 0))])

        @app.callback(
            Output(self.id("bondinggraph_analysis"), "children"),
            [
                Input(self.id("graph"), "data"),
                Input(self.id("display_options"), "data"),
            ],
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
                [GraphComponent(graph=graph_data, options=options)],
                style={"width": "65vmin", "height": "65vmin"},
            )

        @app.callback(
            Output(self.id("chemenv_analysis"), "children"),
            [
                Input(self.id(), "data"),
                Input(self.get_kwarg_id("distance_cutoff"), "value"),
                Input(self.get_kwarg_id("angle_cutoff"), "value"),
            ],
        )
        def get_chemenv_analysis(struct, distance_cutoff, angle_cutoff):

            if not struct:
                raise PreventUpdate

            struct = self.from_data(struct)
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
