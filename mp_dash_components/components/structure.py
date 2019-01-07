import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import warnings

from mp_dash_components import Simple3DSceneComponent
from mp_dash_components.components.core import MPComponent
from mp_dash_components.helpers.layouts import *

from matplotlib.cm import get_cmap

from pymatgen.core.composition import Composition
from pymatgen.core.sites import PeriodicSite
from pymatgen.analysis.graphs import StructureGraph, MoleculeGraph
from pymatgen.analysis.local_env import NearNeighbors
from pymatgen.transformations.standard_transformations import (
    AutoOxiStateDecorationTransformation,
)
from pymatgen.core.periodic_table import Specie, DummySpecie
from pymatgen.analysis.molecule_structure_comparator import CovalentRadius
from pymatgen.vis.structure_vtk import EL_COLORS
from pymatgen.core.structure import Structure, Molecule
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.util.string import unicodeify

from typing import Dict, Union, Optional, List, Tuple

from collections import defaultdict

from itertools import combinations

from mp_dash_components.helpers.scene import (
    Scene,
    Spheres,
    Cylinders,
    Lines,
    Surface,
    Convex,
    Cubes,
)

import numpy as np

from scipy.spatial import Delaunay

# TODO make dangling bonds "stubs"


class StructureMoleculeComponent(MPComponent):

    available_bonding_strategies = {
        subclass.__name__: subclass for subclass in NearNeighbors.__subclasses__()
    }

    available_radius_strategies = (
        "atomic",
        "specified_or_average_ionic",
        "covalent",
        "van_der_waals",
        "atomic_calculated",
        "uniform",
    )

    # TODO ...
    available_polyhedra_rules = ("prefer_large_polyhedra", "only_same_species")

    def __init__(
        self,
        struct_or_mol=None,
        id=None,
        origin_component=None,
        scene_additions=None,  # TODO add (add store also)
        bonding_strategy="JmolNN",
        bonding_strategy_kwargs=None,
        color_scheme="Jmol",
        color_scale=None,
        radius_strategy="uniform",
        draw_image_atoms=True,
        bonded_sites_outside_unit_cell=False,
    ):

        super().__init__(
            id=id, contents=struct_or_mol, origin_component=origin_component
        )

        options = {
            "bonding_strategy": bonding_strategy,
            "bonding_strategy_kwargs": bonding_strategy_kwargs,
            "color_scheme": color_scheme,
            "color_scale": color_scale,
            "radius_strategy": radius_strategy,
            "draw_image_atoms": draw_image_atoms,
            "bonded_sites_outside_unit_cell": bonded_sites_outside_unit_cell,
        }

        self.initial_scene_settings = {
            "lights": [
                {
                    "type": "DirectionalLight",
                    "args": ["#ffffff", 0.15],
                    "position": [-10, 10, 10],
                },
                # {"type":"AmbientLight", "args":["#eeeeee", 0.9]}
                {"type": "HemisphereLight", "args": ["#eeeeee", "#999999", 1.0]},
            ],
            "material": {
                "type": "MeshStandardMaterial",
                "parameters": {"roughness": 0.07, "metalness": 0.00},
            },
            "objectScale": 1.0,
            "cylinderScale": 0.1,
            "defaultSurfaceOpacity": 0.5,
            "staticScene": True,
        }

        self.options_store = dcc.Store(id=f"{id}_options", data=options)

        if struct_or_mol:
            # graph is cached explicitly, this isn't necessary but is an
            # optimization so that graph is only re-generated if bonding
            # algorithm changes
            graph = self._preprocess_input_to_graph(
                struct_or_mol,
                bonding_strategy=bonding_strategy,
                bonding_strategy_kwargs=bonding_strategy_kwargs,
            )
            scene, legend = self.get_scene_and_legend(graph, name=self.id(), **options)
        else:
            # component could be initialized without a structure, in which case
            # an empty scene should be displayed
            graph = None
            scene, legend = self.get_scene_and_legend(
                struct_or_mol, name=self.id(), **options
            )

        self.initial_legend = legend
        self.initial_scene_data = scene.to_json()
        # self.graph_store = dcc.Store(id=f"{id}_scene", data=graph)
        self.legend_store = dcc.Store(id=f"{id}_legend")

    def _generate_callbacks(self, app, cache):

        @app.callback(
            Output(self.id("scene"), "downloadRequest"),
            [Input(self.id("screenshot_button"), "n_clicks")],
            [State(self.id("scene"), "downloadRequest"), State(self.id(), "data")],
        )
        def screenshot_callback(n_clicks, current_requests, struct_or_mol):
            if n_clicks is None:
                raise PreventUpdate
            struct_or_mol = self.from_data(struct_or_mol)
            # TODO: this will break if store is structure/molecule graph ...
            formula = struct_or_mol.composition.reduced_formula
            if hasattr(struct_or_mol, "get_space_group_info"):
                spgrp = struct_or_mol.get_space_group_info()[0]
            else:
                spgrp = ""
            request_filename = "{}-{}-crystal-toolkit.png".format(formula, spgrp)
            if not current_requests:
                n_requests = 1
            else:
                n_requests = current_requests["n_requests"] + 1
            return {
                "n_requests": n_requests,
                "filename": request_filename,
                "filetype": "png",
            }

    def _make_legend(self, legend):

        if legend is None or (not legend.get("colors", None)):
            return html.Div(id=self.id("legend"))

        def get_font_color(hex_code):
            # ensures contrasting font color for background color
            c = tuple(int(hex_code[1:][i : i + 2], 16) for i in (0, 2, 4))
            if 1 - (c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114) / 255 < 0.5:
                font_color = "#000000"
            else:
                font_color = "#ffffff"
            return font_color

        legend_elements = [
            Button(
                html.Span(
                    name, className="icon", style={"color": get_font_color(color)}
                ),
                kind="static",
                style={"background-color": color},
            )
            for color, name in legend["colors"].items()
        ]

        return Field([Control(el, style={"margin-right": "0.2rem"}) for el in legend_elements], id=self.id("legend"), grouped=True)

    def _make_title(self, legend):

        if legend is None or (not legend.get("composition", None)):
            return html.Div(id=self.id("title"))

        composition = Composition.from_dict(legend["composition"])

        return H1(unicodeify(composition.reduced_formula), id=self.id("title"), style={"display": "inline-block"})

    @property
    def all_layouts(self):

        struct_layout = html.Div(
            Simple3DSceneComponent(
                id=self.id("scene"),
                data=self.initial_scene_data,
                settings=self.initial_scene_settings,
            ),
            style={
                "width": "100%",
                "height": "100%",
                "overflow": "hidden",
                "margin": "0 auto",
            },
        )

        screenshot_layout = html.Div(
            [
                Button(
                    [Icon(), html.Span(), "Download Screenshot"],
                    kind="primary",
                    id=self.id("screenshot_button"),
                )
            ],
            # TODO: change to "bottom" when dropdown included
            style={"vertical-align": "top", "display": "inline-block"},
        )

        title_layout = self._make_title(self.initial_legend)

        legend_layout = self._make_legend(self.initial_legend)

        ## hide if molecule
        # html.Div(id=self.id("preprocessing_choice"), children=[dcc.RadioItems(
        #    options=[
        #        {'label': 'Input', 'value': 'input'},
        #        {'label': 'Conventional', 'value': 'conventional'},
        #        {'label': 'Primitive', 'value': 'primitive'},
        #    ],
        #    value='conventional'
        # )])

        # options = {
        #    "bonding_strategy": bonding_strategy,
        #    "bonding_strategy_kwargs": bonding_strategy_kwargs,
        #    "color_scheme": color_scheme,
        #    "color_scale": color_scale,
        #    "radius_strategy": radius_strategy,
        #    "draw_image_atoms": draw_image_atoms,
        #    "bonded_sites_outside_unit_cell": bonded_sites_outside_unit_cell}

        # bonding_layout = ...
        # color_scheme_layout = ...
        # radius_layout = ...
        #
        # draw_layout = ... # draw_image_atoms, bonded_sites_outside_, add dangling bonds kwarg too
        #
        # hide_show_layout = ...
        #
        # download_layout = ...

        return {
            "struct": struct_layout,
            "screenshot": screenshot_layout,
            "title": title_layout,
            "legend": legend_layout,
        }

    @property
    def standard_layout(self):
        return self.all_layouts["struct"]

    @staticmethod
    def _preprocess_input_to_graph(
        input: Union[Structure, StructureGraph, Molecule, MoleculeGraph],
        bonding_strategy: str = "CrystalNN",
        bonding_strategy_kwargs: Optional[Dict] = None,
    ) -> Union[StructureGraph, MoleculeGraph]:

        if isinstance(input, Structure):

            # ensure fractional co-ordinates are normalized to be in [0,1)
            # (this is actually not guaranteed by Structure)
            input = input.as_dict(verbosity=0)
            for site in input["sites"]:
                site["abc"] = np.mod(site["abc"], 1)
            input = Structure.from_dict(input)

            if not input.is_ordered:
                # calculating bonds in disordered structures is currently very flaky
                bonding_strategy = "CutOffDictNN"

        # we assume most uses of this class will give a structure as an input argument,
        # meaning we have to calculate the graph for bonding information, however if
        # the graph is already known and supplied, we will use that
        if isinstance(input, StructureGraph) or isinstance(input, MoleculeGraph):
            graph = input
        else:
            if (
                bonding_strategy
                not in StructureMoleculeComponent.available_bonding_strategies.keys()
            ):
                raise ValueError(
                    "Bonding strategy not supported. Please supply a name "
                    "of a NearNeighbor subclass, choose from: {}".format(
                        ", ".join(
                            StructureMoleculeComponent.available_bonding_strategies.keys()
                        )
                    )
                )
            else:
                bonding_strategy_kwargs = bonding_strategy_kwargs or {}
                if bonding_strategy == "CutOffDictNN":
                    if "cut_off_dict" in bonding_strategy_kwargs:
                        # TODO: remove this hack by making args properly JSON serializable
                        bonding_strategy_kwargs["cut_off_dict"] = {
                            (x[0], x[1]): x[2]
                            for x in bonding_strategy_kwargs["cut_off_dict"]
                        }
                bonding_strategy = StructureMoleculeComponent.available_bonding_strategies[
                    bonding_strategy
                ](
                    **bonding_strategy_kwargs
                )
                try:
                    if isinstance(input, Structure):
                        graph = StructureGraph.with_local_env_strategy(
                            input, bonding_strategy
                        )
                    else:
                        graph = MoleculeGraph.with_local_env_strategy(
                            input, bonding_strategy
                        )
                except:
                    # for some reason computing bonds failed, so let's not have any bonds(!)
                    if isinstance(input, Structure):
                        graph = StructureGraph.with_empty_graph(input)
                    else:
                        graph = MoleculeGraph.with_empty_graph(input)

        return graph

    @staticmethod
    def _analyze_site_props(struct_or_mol):

        # store list of site props that are vectors, so these can be displayed as arrows
        # (implicitly assumes all site props for a given key are same type)
        site_prop_names = defaultdict(list)
        for name, props in struct_or_mol.site_properties.items():
            if isinstance(props[0], float) or isinstance(props[0], int):
                site_prop_names["scalar"].append(name)
            elif isinstance(props[0], list) and len(props[0]) == 3:
                if isinstance(props[0][0], list) and len(props[0][0]) == 3:
                    site_prop_names["matrix"].append(name)
                else:
                    site_prop_names["vector"].append(name)
            elif isinstance(props[0], str):
                site_prop_names["categorical"].append(name)

        return dict(site_prop_names)

    @staticmethod
    def _get_origin(struct_or_mol):

        if isinstance(struct_or_mol, Structure):
            # display_range = [0.5, 0.5, 0.5]
            # x_center = 0.5 * (max(display_range[0]) - min(display_range[0]))
            # y_center = 0.5 * (max(display_range[1]) - min(display_range[1]))
            # z_center = 0.5 * (max(display_range[2]) - min(display_range[2]))
            geometric_center = struct_or_mol.lattice.get_cartesian_coords(
                (0.5, 0.5, 0.5)
            )
        elif isinstance(struct_or_mol, Molecule):
            geometric_center = np.average(struct_or_mol.cart_coords, axis=0)

        return geometric_center

    @staticmethod
    def _get_struct_or_mol(graph) -> Union[Structure, Molecule]:
        if isinstance(graph, StructureGraph):
            return graph.structure
        elif isinstance(graph, MoleculeGraph):
            return graph.molecule
        else:
            raise ValueError

    @staticmethod
    def _get_display_colors_and_legend_for_sites(
        struct_or_mol, site_prop_types, color_scheme="Jmol", color_scale=None
    ) -> Tuple[List[List[str]], Dict]:
        """
        Note this returns a list of lists of strings since each
        site might have multiple colors defined if the site is
        disordered.

        The legend is a dictionary whose keys are colors and values
        are corresponding element names or values, depending on the color
        scheme chosen.
        """

        # TODO: check to see if there is a bug here due to Composition being unordered(?)

        legend = {"composition": struct_or_mol.composition.as_dict(), "colors": {}}

        # don't calculate color if one is explicitly supplied
        if "display_color" in struct_or_mol.site_properties:
            # don't know what the color legend (meaning) is, so return empty legend
            return (struct_or_mol.site_properties["display_color"], legend)

        def get_color_hex(x):
            return "#{:02x}{:02x}{:02x}".format(*x)

        if color_scheme not in ("VESTA", "Jmol", "colorblind_friendly"):

            if not struct_or_mol.is_ordered:
                raise ValueError(
                    "Can only use VESTA, Jmol or colorblind_friendly color "
                    "schemes for disordered structures or molecules, color "
                    "schemes based on site properties are ill-defined."
                )

            if (color_scheme not in site_prop_types.get("scalar", [])) and (
                color_scheme not in site_prop_types.get("categorical", [])
            ):

                raise ValueError(
                    "Unsupported color scheme. Should be VESTA, Jmol, "
                    "colorblind_friendly or a scalar (float) or categorical "
                    "(string) site property."
                )

        if color_scheme in ("VESTA", "Jmol"):

            colors = []
            for site in struct_or_mol:
                elements = [
                    sp.as_dict()["element"] for sp, _ in site.species_and_occu.items()
                ]
                colors.append(
                    [
                        get_color_hex(EL_COLORS[color_scheme][element])
                        for element in elements
                    ]
                )
                # construct legend
                for element in elements:
                    color = get_color_hex(EL_COLORS[color_scheme][element])
                    legend["colors"][color] = element

        elif color_scheme in site_prop_types.get("scalar", []):

            props = np.array(struct_or_mol.site_properties[color_scheme])

            # by default, use blue-grey-red color scheme,
            # so that zero is ~ grey, and positive/negative
            # are red/blue
            color_scale = color_scale or "coolwarm"
            # try to keep color scheme symmetric around 0
            color_max = max([abs(min(props)), max(props)])
            color_min = -color_max

            cmap = get_cmap(color_scale)
            # normalize in [0, 1] range, as expected by cmap
            props = (props - color_min) / (color_max - color_min)

            def get_color_cmap(x):
                return [int(c * 255) for c in cmap(x)[0:3]]

            colors = [[get_color_hex(get_color_cmap(x))] for x in props]
            # construct legend
            c = get_color_hex(color_min)
            legend["colors"][c] = "{}".format(get_color_cmap(color_min))
            if color_max != color_min:
                c = get_color_hex(get_color_cmap(color_max))
                legend["colors"][c] = "{}".format(color_max)

        elif color_scheme == "colorblind_friendly":
            raise NotImplementedError

        elif color_scheme in site_prop_types.get("categorical", []):
            # iter() a palettable  palettable.colorbrewer.qualitative
            # cmap.colors, check len, Set1_9 ?
            raise NotImplementedError

        return colors, legend

    @staticmethod
    def _primitives_from_lattice(lattice, origin=(0, 0, 0), **kwargs):

        o = -np.array(origin)
        a, b, c = lattice.matrix[0], lattice.matrix[1], lattice.matrix[2]
        line_pairs = [
            o,
            o + a,
            o,
            o + b,
            o,
            o + c,
            o + a,
            o + a + b,
            o + a,
            o + a + c,
            o + b,
            o + b + a,
            o + b,
            o + b + c,
            o + c,
            o + c + a,
            o + c,
            o + c + b,
            o + a + b,
            o + a + b + c,
            o + a + c,
            o + a + b + c,
            o + b + c,
            o + a + b + c,
        ]
        line_pairs = [line.tolist() for line in line_pairs]

        return Lines(line_pairs, **kwargs)

    @staticmethod
    def _get_ellipsoids_from_matrix(matrix):
        raise NotImplementedError
        # matrix = np.array(matrix)
        # eigenvalues, eigenvectors = np.linalg.eig(matrix)

    @staticmethod
    def _primitives_from_site(
        site,
        connected_sites=None,
        origin=(0, 0, 0),
        ellipsoid_site_prop=None,
        all_connected_sites_present=True,
        explicitly_calculate_polyhedra_hull=False,
    ):
        """
        Sites must have display_radius and display_color site properties.
        :param site:
        :param connected_sites:
        :param origin:
        :param ellipsoid_site_prop: (beta)
        :param all_connected_sites_present: if False, will not calculate
        polyhedra since this would be misleading
        :param explicitly_calculate_polyhedra_hull:
        :return:
        """

        atoms = []
        bonds = []
        polyhedron = []

        # for disordered structures
        is_ordered = site.is_ordered
        occu_start = 0.0

        # for thermal ellipsoids etc.
        if ellipsoid_site_prop:
            matrix = site.properties[ellipsoid_site_prop]
            ellipsoids = StructureMoleculeComponent._get_ellipsoids_from_matrix(matrix)
        else:
            ellipsoids = None

        position = np.subtract(site.coords, origin).tolist()

        # site_color is used for bonds and polyhedra, if multiple colors are
        # defined for site (e.g. a disordered site), then we use grey
        all_colors = set(site.properties["display_color"])
        if len(all_colors) > 1:
            site_color = "#555555"
        else:
            site_color = list(all_colors)[0]

        for idx, (sp, occu) in enumerate(site.species_and_occu.items()):

            if isinstance(sp, DummySpecie):

                cube = Cubes(positions=[position])
                atoms.append(cube)

            else:

                color = site.properties["display_color"][idx]
                radius = site.properties["display_radius"][idx]

                # TODO: make optional/default to None
                # in disordered structures, we fractionally color-code spheres,
                # drawing a sphere segment from phi_end to phi_start
                # (think a sphere pie chart)
                if not is_ordered:
                    phi_frac_end = occu_start + occu
                    phi_frac_start = occu_start
                    occu_start = phi_frac_end
                    phiStart = phi_frac_start * np.pi * 2
                    phiEnd = phi_frac_end * np.pi * 2
                else:
                    phiStart, phiEnd = None, None

                # TODO: add names for labels
                # name = "{}".format(sp)
                # if occu != 1.0:
                #    name += " ({}% occupancy)".format(occu)

                sphere = Spheres(
                    positions=[position],
                    color=color,
                    radius=radius,
                    phiStart=phiStart,
                    phiEnd=phiEnd,
                    ellipsoids=ellipsoids,
                )
                atoms.append(sphere)

        if connected_sites:

            all_positions = [position]
            for connected_site in connected_sites:

                connected_position = np.subtract(connected_site.site.coords, origin)
                bond_midpoint = np.add(position, connected_position) / 2

                cylinder = Cylinders(
                    positionPairs=[[position, bond_midpoint.tolist()]], color=site_color
                )
                bonds.append(cylinder)
                all_positions.append(connected_position.tolist())

            if len(connected_sites) > 3 and all_connected_sites_present:
                if explicitly_calculate_polyhedra_hull:

                    try:

                        # all_positions = [[0, 0, 0], [0, 0, 10], [0, 10, 0], [10, 0, 0]]
                        # gives...
                        # .convex_hull = [[2, 3, 0], [1, 3, 0], [1, 2, 0], [1, 2, 3]]
                        # .vertex_neighbor_vertices = [1, 2, 3, 2, 3, 0, 1, 3, 0, 1, 2, 0]

                        vertices_indices = Delaunay(
                            all_positions
                        ).vertex_neighbor_vertices
                        vertices = [all_positions[idx] for idx in vertices_indices]

                        polyhedron = [
                            Surface(
                                positions=vertices,
                                color=site.properties["display_color"][0],
                            )
                        ]

                    except Exception as e:

                        polyhedron = []

                else:

                    polyhedron = [Convex(positions=all_positions, color=site_color)]

        return {"atoms": atoms, "bonds": bonds, "polyhedra": polyhedron}

    @staticmethod
    def _get_display_radii_for_sites(
        struct_or_mol, radius_strategy="specified_or_average_ionic"
    ) -> List[List[float]]:
        """
        Note this returns a list of lists of floats since each
        site might have multiple radii defined if the site is
        disordered.
        """

        # don't calculate radius if one is explicitly supplied
        if "display_radius" in struct_or_mol.site_properties:
            return struct_or_mol.site_properties["display_radius"]

        if (
            radius_strategy
            not in StructureMoleculeComponent.available_radius_strategies
        ):
            raise ValueError(
                "Unknown radius strategy {}, choose from: {}".format(
                    radius_strategy,
                    StructureMoleculeComponent.available_radius_strategies,
                )
            )
        radii = []

        for site_idx, site in enumerate(struct_or_mol):

            site_radii = []

            for comp_idx, (sp, occu) in enumerate(site.species_and_occu.items()):

                radius = None

                if radius_strategy is "uniform":
                    radius = 0.5
                if radius_strategy is "atomic":
                    radius = sp.atomic_radius
                elif (
                    radius_strategy is "specified_or_average_ionic"
                    and isinstance(sp, Specie)
                    and sp.oxi_state
                ):
                    radius = sp.ionic_radius
                elif radius_strategy is "specified_or_average_ionic":
                    radius = sp.average_ionic_radius
                elif radius_strategy is "covalent":
                    el = str(getattr(sp, "element", sp))
                    radius = CovalentRadius.radius[el]
                elif radius_strategy is "van_der_waals":
                    radius = sp.van_der_waals_radius
                elif radius_strategy is "atomic_calculated":
                    radius = sp.atomic_radius_calculated

                if not radius:
                    warnings.warn(
                        "Radius unknown for {} and strategy {}, "
                        "setting to 1.0.".format(sp, radius_strategy)
                    )
                    radius = 1.0

                site_radii.append(radius)

            radii.append(site_radii)

        return radii

    @staticmethod
    def _get_sites_to_draw(
        struct_or_mol: Union[Structure, Molecule],
        graph: Union[StructureGraph, MoleculeGraph],
        draw_image_atoms=True,
        bonded_sites_outside_unit_cell=True,
    ):
        """
        Returns a list of site indices and image vectors.
        """

        sites_to_draw = [(idx, (0, 0, 0)) for idx in range(len(struct_or_mol))]

        # trivial in this case
        if isinstance(struct_or_mol, Molecule):
            return sites_to_draw

        if draw_image_atoms:

            for idx, site in enumerate(struct_or_mol):

                zero_elements = [
                    idx
                    for idx, f in enumerate(site.frac_coords)
                    if np.allclose(f, 0, atol=0.05)
                ]

                coord_permutations = [
                    x
                    for l in range(1, len(zero_elements) + 1)
                    for x in combinations(zero_elements, l)
                ]

                for perm in coord_permutations:
                    sites_to_draw.append(
                        (idx, (int(0 in perm), int(1 in perm), int(2 in perm)))
                    )

                one_elements = [
                    idx
                    for idx, f in enumerate(site.frac_coords)
                    if np.allclose(f, 1, atol=0.05)
                ]

                coord_permutations = [
                    x
                    for l in range(1, len(one_elements) + 1)
                    for x in combinations(one_elements, l)
                ]

                for perm in coord_permutations:
                    sites_to_draw.append(
                        (idx, (-int(0 in perm), -int(1 in perm), -int(2 in perm)))
                    )

        if bonded_sites_outside_unit_cell:

            # TODO: subtle bug here, see mp-5020, expansion logic not quite right
            sites_to_append = []
            for (n, jimage) in sites_to_draw:
                connected_sites = graph.get_connected_sites(n, jimage=jimage)
                for connected_site in connected_sites:
                    if connected_site.jimage != (0, 0, 0):
                        sites_to_append.append(
                            (connected_site.index, connected_site.jimage)
                        )
            sites_to_draw += sites_to_append

        return sites_to_draw

    @staticmethod
    def get_scene_and_legend(
        struct_or_mol: Union[Structure, StructureGraph, Molecule, MoleculeGraph],
        name="unknown_structure_or_molecule",
        bonding_strategy="CrystalNN",
        bonding_strategy_kwargs=None,
        color_scheme="Jmol",
        color_scale=None,
        radius_strategy="specified_or_average_ionic",
        ellipsoid_site_prop=None,
        draw_image_atoms=True,
        bonded_sites_outside_unit_cell=True,
        hide_incomplete_bonds=False,
        explicitly_calculate_polyhedra_hull=False,
    ) -> Tuple[Scene, Dict[str, str]]:

        if not name:
            raise ValueError("Please supply a non-empty name.")

        scene = Scene(name=name)

        if struct_or_mol is None:
            return scene, {}

        graph = StructureMoleculeComponent._preprocess_input_to_graph(
            struct_or_mol,
            bonding_strategy=bonding_strategy,
            bonding_strategy_kwargs=bonding_strategy_kwargs,
        )
        struct_or_mol = StructureMoleculeComponent._get_struct_or_mol(graph)
        radii = StructureMoleculeComponent._get_display_radii_for_sites(
            struct_or_mol, radius_strategy=radius_strategy
        )
        site_prop_types = StructureMoleculeComponent._analyze_site_props(struct_or_mol)
        colors, legend = StructureMoleculeComponent._get_display_colors_and_legend_for_sites(
            struct_or_mol,
            site_prop_types,
            color_scale=color_scale,
            color_scheme=color_scheme,
        )

        struct_or_mol.add_site_property("display_radius", radii)
        struct_or_mol.add_site_property("display_color", colors)

        origin = StructureMoleculeComponent._get_origin(struct_or_mol)

        primitives = defaultdict(list)
        sites_to_draw = StructureMoleculeComponent._get_sites_to_draw(
            struct_or_mol,
            graph,
            draw_image_atoms=draw_image_atoms,
            bonded_sites_outside_unit_cell=bonded_sites_outside_unit_cell,
        )

        for (idx, jimage) in sites_to_draw:

            site = struct_or_mol[idx]
            if jimage != (0, 0, 0):
                connected_sites = graph.get_connected_sites(idx, jimage=jimage)
                site = PeriodicSite(
                    site.species_and_occu,
                    np.add(site.frac_coords, jimage),
                    site.lattice,
                    properties=site.properties,
                )
            else:
                connected_sites = graph.get_connected_sites(idx)

            true_number_of_connected_sites = len(connected_sites)
            connected_sites_being_drawn = [
                cs for cs in connected_sites if (cs.index, cs.jimage) in sites_to_draw
            ]
            number_of_connected_sites_drawn = len(connected_sites_being_drawn)
            all_connected_sites_present = (
                true_number_of_connected_sites == number_of_connected_sites_drawn
            )
            if hide_incomplete_bonds:
                # only draw bonds if the destination site is also being drawn
                connected_sites = connected_sites_being_drawn

            site_primitives = StructureMoleculeComponent._primitives_from_site(
                site,
                connected_sites=connected_sites,
                all_connected_sites_present=all_connected_sites_present,
                origin=origin,
                ellipsoid_site_prop=ellipsoid_site_prop,
                explicitly_calculate_polyhedra_hull=explicitly_calculate_polyhedra_hull,
            )
            for k, v in site_primitives.items():
                primitives[k] += v

        # we are here ...
        # select polyhedra
        # split by atom type at center
        # see if any intersect, if yes split further
        # order sets, with each choice, go to add second set etc if don't intersect
        # they intersect if centre atom forms vertex of another atom (caveat: centre atom may not actually be inside polyhedra! not checking for this, add todo)
        # def _set_intersects() ->bool:
        # def _split_set() ->List: (by type, then..?)
        # def _order_sets()... pick 1, ask can add 2? etc

        if isinstance(struct_or_mol, Structure):
            primitives["unit_cell"].append(
                StructureMoleculeComponent._primitives_from_lattice(
                    struct_or_mol.lattice, origin=origin
                )
            )

        sub_scenes = [Scene(name=k, contents=v) for k, v in primitives.items()]
        scene.contents = sub_scenes

        return scene, legend
