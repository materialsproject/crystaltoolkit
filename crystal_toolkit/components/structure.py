import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import warnings

from crystal_toolkit import Simple3DSceneComponent
from pymatgen.util.string import unicodeify_species
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import *

from matplotlib.cm import get_cmap

from pymatgen.core.composition import Composition
from pymatgen.core.sites import PeriodicSite
from pymatgen.core.lattice import Lattice
from pymatgen.analysis.graphs import StructureGraph, MoleculeGraph
from pymatgen.analysis.local_env import NearNeighbors
from pymatgen.core.periodic_table import Specie
from pymatgen.analysis.molecule_structure_comparator import CovalentRadius
from pymatgen.vis.structure_vtk import EL_COLORS
from pymatgen.core.structure import Structure, Molecule
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from sklearn.preprocessing import LabelEncoder
from palettable.colorbrewer.qualitative import Set1_9, Set2_8

from typing import Dict, Union, Optional, List, Tuple

from collections import defaultdict, OrderedDict

from itertools import combinations_with_replacement, chain
import re

from crystal_toolkit.core.scene import Scene, Spheres, Arrows

import numpy as np

# TODO: make dangling bonds "stubs"? (fixed length)

EL_COLORS["VESTA"]["bcp"] = [0, 0, 255]
EL_COLORS["VESTA"]["rcp"] = [255, 0, 0]
EL_COLORS["VESTA"]["ccp"] = [255, 255, 0]
EL_COLORS["Jmol"]["bcp"] = [0, 0, 255]
EL_COLORS["Jmol"]["rcp"] = [255, 0, 0]
EL_COLORS["Jmol"]["ccp"] = [255, 255, 0]


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

    default_scene_settings = {"cylinderScale": 0.1}

    def __init__(
        self,
        struct_or_mol=None,
        id=None,
        origin_component=None,
        scene_additions=None,
        bonding_strategy="CrystalNN",
        bonding_strategy_kwargs=None,
        color_scheme="VESTA",
        color_scale=None,
        radius_strategy="uniform",
        radius_scale=1.0,
        draw_image_atoms=True,
        bonded_sites_outside_unit_cell=False,
        hide_incomplete_bonds=False,
        show_compass=False,
        scene_settings=None,
        **kwargs,
    ):

        super().__init__(
            id=id, contents=struct_or_mol, origin_component=origin_component, **kwargs
        )

        self.default_title = "Crystal Toolkit"

        self.initial_scene_settings = (
            StructureMoleculeComponent.default_scene_settings.copy()
        )
        if scene_settings:
            self.initial_scene_settings.update(scene_settings)

        self.create_store("scene_settings", initial_data=self.initial_scene_settings)

        self.initial_graph_generation_options = {
            "bonding_strategy": bonding_strategy,
            "bonding_strategy_kwargs": bonding_strategy_kwargs,
        }
        self.create_store(
            "graph_generation_options",
            initial_data=self.initial_graph_generation_options,
        )

        self.initial_display_options = {
            "color_scheme": color_scheme,
            "color_scale": color_scale,
            "radius_strategy": radius_strategy,
            "radius_scale": radius_scale,
            "draw_image_atoms": draw_image_atoms,
            "bonded_sites_outside_unit_cell": bonded_sites_outside_unit_cell,
            "hide_incomplete_bonds": hide_incomplete_bonds,
            "show_compass": show_compass,
        }
        self.create_store("display_options", initial_data=self.initial_display_options)

        if scene_additions:
            self.initial_scene_additions = Scene(
                name="scene_additions", contents=scene_additions
            )
        else:
            self.initial_scene_additions = Scene(name="scene_additions")
        self.create_store(
            "scene_additions", initial_data=self.initial_scene_additions.to_json()
        )

        if struct_or_mol:
            # graph is cached explicitly, this isn't necessary but is an
            # optimization so that graph is only re-generated if bonding
            # algorithm changes
            graph = self._preprocess_input_to_graph(
                struct_or_mol,
                bonding_strategy=bonding_strategy,
                bonding_strategy_kwargs=bonding_strategy_kwargs,
            )
            scene, legend = self.get_scene_and_legend(
                graph,
                name=self.id(),
                scene_additions=self.initial_scene_additions,
                **self.initial_display_options,
            )
            if hasattr(struct_or_mol, "lattice"):
                self._lattice = struct_or_mol.lattice
        else:
            # component could be initialized without a structure, in which case
            # an empty scene should be displayed
            graph = None
            scene, legend = self.get_scene_and_legend(
                None,
                name=self.id(),
                scene_additions=self.initial_scene_additions,
                **self.initial_display_options,
            )

        self.initial_legend = legend
        self.create_store("legend_data", initial_data=self.initial_legend)

        self.initial_scene_data = scene.to_json()

        self.initial_graph = graph
        self.create_store("graph", initial_data=self.to_data(graph))

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("graph"), "data"),
            [
                Input(self.id("graph_generation_options"), "data"),
                Input(self.id("unit-cell-choice"), "value"),
                Input(self.id(), "data"),
            ],
        )
        def update_graph(graph_generation_options, unit_cell_choice, struct_or_mol):

            if not struct_or_mol:
                raise PreventUpdate

            struct_or_mol = self.from_data(struct_or_mol)
            graph_generation_options = self.from_data(graph_generation_options)

            if isinstance(struct_or_mol, Structure):
                if unit_cell_choice != "input":
                    if unit_cell_choice == "primitive":
                        struct_or_mol = struct_or_mol.get_primitive_structure()
                    elif unit_cell_choice == "conventional":
                        sga = SpacegroupAnalyzer(struct_or_mol)
                        struct_or_mol = sga.get_conventional_standard_structure()
                    elif unit_cell_choice == "reduced":
                        struct_or_mol = struct_or_mol.get_reduced_structure()

            graph = self._preprocess_input_to_graph(
                struct_or_mol,
                bonding_strategy=graph_generation_options["bonding_strategy"],
                bonding_strategy_kwargs=graph_generation_options[
                    "bonding_strategy_kwargs"
                ],
            )

            self.logger.debug("Constructed graph")

            return self.to_data(graph)

        @app.callback(
            Output(self.id("scene"), "data"),
            [
                Input(self.id("graph"), "data"),
                Input(self.id("display_options"), "data"),
            ],
        )
        def update_scene(graph, display_options):
            display_options = self.from_data(display_options)
            graph = self.from_data(graph)
            scene, legend = self.get_scene_and_legend(graph, **display_options)
            return scene.to_json()

        @app.callback(
            Output(self.id("legend_data"), "data"),
            [
                Input(self.id("graph"), "data"),
                Input(self.id("display_options"), "data"),
            ],
        )
        def update_legend(graph, display_options):
            # TODO: more cleanly split legend from scene generation
            display_options = self.from_data(display_options)
            graph = self.from_data(graph)
            struct_or_mol = self._get_struct_or_mol(graph)
            site_prop_types = self._analyze_site_props(struct_or_mol)
            colors, legend = self._get_display_colors_and_legend_for_sites(
                struct_or_mol,
                site_prop_types,
                color_scheme=display_options.get("color_scheme", None),
                color_scale=display_options.get("color_scale", None),
            )
            return self.to_data(legend)

        @app.callback(
            Output(self.id("color-scheme"), "options"),
            [Input(self.id("graph"), "data")],
        )
        def update_color_options(graph):

            options = [
                {"label": "Jmol", "value": "Jmol"},
                {"label": "VESTA", "value": "VESTA"},
                {"label": "Colorblind-friendly", "value": "colorblind_friendly"},
            ]
            graph = self.from_data(graph)
            struct_or_mol = self._get_struct_or_mol(graph)
            site_props = self._analyze_site_props(struct_or_mol)
            for site_prop_type in ("scalar", "categorical"):
                if site_prop_type in site_props:
                    for prop in site_props[site_prop_type]:
                        options += [{"label": f"Site property: {prop}", "value": prop}]

            return options

        @app.callback(
            Output(self.id("display_options"), "data"),
            [
                Input(self.id("color-scheme"), "value"),
                Input(self.id("radius_strategy"), "value"),
                Input(self.id("draw_options"), "value"),
            ],
            [State(self.id("display_options"), "data")],
        )
        def update_display_options(
            color_scheme, radius_strategy, draw_options, display_options
        ):
            display_options = self.from_data(display_options)
            display_options.update({"color_scheme": color_scheme})
            display_options.update({"radius_strategy": radius_strategy})
            display_options.update(
                {"draw_image_atoms": "draw_image_atoms" in draw_options}
            )
            display_options.update(
                {
                    "bonded_sites_outside_unit_cell": "bonded_sites_outside_unit_cell"
                    in draw_options
                }
            )
            display_options.update(
                {"hide_incomplete_bonds": "hide_incomplete_bonds" in draw_options}
            )

            if display_options == self.initial_display_options:
                raise PreventUpdate

            self.logger.debug("Display options updated")

            return self.to_data(display_options)

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

        @app.callback(
            Output(self.id("scene"), "toggleVisibility"),
            [Input(self.id("hide-show"), "value")],
            [State(self.id("hide-show"), "options")],
        )
        def update_visibility(values, options):
            visibility = {opt["value"]: (opt["value"] in values) for opt in options}
            return visibility

        @app.callback(
            [
                Output(self.id("legend_container"), "children"),
                Output(self.id("title_container"), "children"),
            ],
            [Input(self.id("legend_data"), "data")],
        )
        def update_legend(legend):

            legend = self.from_data(legend)

            if legend == self.initial_legend:
                raise PreventUpdate

            return self._make_legend(legend), self._make_title(legend)

        @app.callback(
            Output(self.id("graph_generation_options"), "data"),
            [
                Input(self.id("bonding_algorithm"), "value"),
                Input(self.id("bonding_algorithm_custom_cutoffs"), "data"),
            ],
        )
        def update_structure_viewer_data(bonding_algorithm, custom_cutoffs_rows):

            graph_generation_options = {
                "bonding_strategy": bonding_algorithm,
                "bonding_strategy_kwargs": None,
            }

            if graph_generation_options == self.initial_graph_generation_options:
                raise PreventUpdate

            if bonding_algorithm == "CutOffDictNN":
                # this is not the format CutOffDictNN expects (since that is not JSON
                # serializable), so we store as a list of tuples instead
                # TODO: make CutOffDictNN args JSON serializable
                custom_cutoffs = [
                    (row["A"], row["B"], float(row["A—B"]))
                    for row in custom_cutoffs_rows
                ]
                graph_generation_options["bonding_strategy_kwargs"] = {
                    "cut_off_dict": custom_cutoffs
                }
            return self.to_data(graph_generation_options)

        @app.callback(
            [
                Output(self.id("bonding_algorithm_custom_cutoffs"), "data"),
                Output(self.id("bonding_algorithm_custom_cutoffs_container"), "style"),
            ],
            [Input(self.id("bonding_algorithm"), "value")],
            [State(self.id("graph"), "data")],
        )
        def update_custom_bond_options(bonding_algorithm, graph):

            if not graph:
                raise PreventUpdate

            if bonding_algorithm == "CutOffDictNN":
                style = {}
            else:
                style = {"display": "none"}

            graph = self.from_data(graph)
            struct_or_mol = self._get_struct_or_mol(graph)
            # can't use type_of_specie because it doesn't work with disordered structures
            species = set(
                map(
                    str,
                    chain.from_iterable(
                        [list(c.keys()) for c in struct_or_mol.species_and_occu]
                    ),
                )
            )
            rows = [
                {"A": combination[0], "B": combination[1], "A—B": 0}
                for combination in combinations_with_replacement(species, 2)
            ]
            return rows, style

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

        try:
            formula = Composition.from_dict(legend["composition"]).reduced_formula
        except:
            # TODO: fix for Dummy Specie compositions
            formula = "Unknown"

        legend_colors = OrderedDict(
            sorted(list(legend["colors"].items()), key=lambda x: formula.find(x[1]))
        )

        legend_elements = [
            Button(
                html.Span(
                    name, className="icon", style={"color": get_font_color(color)}
                ),
                kind="static",
                style={"background-color": color},
            )
            for color, name in legend_colors.items()
        ]

        return Field(
            [Control(el, style={"margin-right": "0.2rem"}) for el in legend_elements],
            id=self.id("legend"),
            grouped=True,
        )

    def _make_title(self, legend):

        if not legend or (not legend.get("composition", None)):
            return H1(self.default_title, id=self.id("title"))

        composition = legend["composition"]
        if isinstance(composition, dict):

            # TODO: make Composition handle DummySpecie
            try:
                composition = Composition.from_dict(composition)
                formula = composition.reduced_formula
                formula_parts = re.findall(r"[^\d_]+|\d+", formula)
                formula_components = [
                    html.Sub(part) if part.isnumeric() else html.Span(part)
                    for part in formula_parts
                ]
            except:
                formula_components = list(composition.keys())

        return H1(
            formula_components, id=self.id("title"), style={"display": "inline-block"}
        )

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
                    [Icon(), html.Span(), "Download Image"],
                    kind="primary",
                    id=self.id("screenshot_button"),
                )
            ],
            # TODO: change to "bottom" when dropdown included
            style={"vertical-align": "top", "display": "inline-block"},
        )

        title_layout = html.Div(
            self._make_title(self.initial_legend), id=self.id("title_container")
        )

        legend_layout = html.Div(
            self._make_legend(self.initial_legend), id=self.id("legend_container")
        )

        nn_mapping = {
            "CrystalNN": "CrystalNN",
            "Custom Bonds": "CutOffDictNN",
            "Jmol Bonding": "JmolNN",
            "Minimum Distance (10% tolerance)": "MinimumDistanceNN",
            "O'Keeffe's Algorithm": "MinimumOKeeffeNN",
            "Hoppe's ECoN Algorithm": "EconNN",
            "Brunner's Reciprocal Algorithm": "BrunnerNN_reciprocal",
        }

        bonding_algorithm = dcc.Dropdown(
            options=[{"label": k, "value": v} for k, v in nn_mapping.items()],
            value="CrystalNN",
            id=self.id("bonding_algorithm"),
        )

        bonding_algorithm_custom_cutoffs = html.Div(
            [
                html.Br(),
                dt.DataTable(
                    columns=[
                        {"name": "A", "id": "A"},
                        {"name": "B", "id": "B"},
                        {"name": "A—B /Å", "id": "A—B"},
                    ],
                    editable=True,
                    id=self.id("bonding_algorithm_custom_cutoffs"),
                ),
                html.Br(),
            ],
            id=self.id("bonding_algorithm_custom_cutoffs_container"),
            style={"display": "none"},
        )

        options_layout = Field(
            [
                #  TODO: hide if molecule
                html.Label("Change unit cell:", className="mpc-label"),
                html.Div(
                    dcc.RadioItems(
                        options=[
                            {"label": "Input cell", "value": "input"},
                            {"label": "Primitive cell", "value": "primitive"},
                            {"label": "Conventional cell", "value": "conventional"},
                            {"label": "Reduced cell", "value": "reduced"},
                        ],
                        value="input",
                        id=self.id("unit-cell-choice"),
                        labelStyle={"display": "block"},
                        inputClassName="mpc-radio",
                    ),
                    className="mpc-control",
                ),
                html.Div(
                    [
                        html.Label("Change bonding algorithm: ", className="mpc-label"),
                        bonding_algorithm,
                        bonding_algorithm_custom_cutoffs,
                    ]
                ),
                html.Label("Change color scheme:", className="mpc-label"),
                html.Div(
                    dcc.Dropdown(
                        options=[
                            {"label": "VESTA", "value": "VESTA"},
                            {"label": "Jmol", "value": "Jmol"},
                        ],
                        value=self.initial_display_options["color_scheme"],
                        clearable=False,
                        id=self.id("color-scheme"),
                    ),
                    className="mpc-control",
                ),
                html.Label("Change atomic radii:", className="mpc-label"),
                html.Div(
                    dcc.Dropdown(
                        options=[
                            {"label": "Ionic", "value": "specified_or_average_ionic"},
                            {"label": "Covalent", "value": "covalent"},
                            {"label": "Van der Waals", "value": "van_der_waals"},
                            {"label": "Uniform (0.5Å)", "value": "uniform"},
                        ],
                        value=self.initial_display_options["radius_strategy"],
                        clearable=False,
                        id=self.id("radius_strategy"),
                    ),
                    className="mpc-control",
                ),
                html.Label("Draw options:", className="mpc-label"),
                html.Div(
                    [
                        dcc.Checklist(
                            options=[
                                {
                                    "label": "Draw repeats of atoms on periodic boundaries",
                                    "value": "draw_image_atoms",
                                },
                                {
                                    "label": "Draw atoms outside unit cell bonded to "
                                    "atoms within unit cell",
                                    "value": "bonded_sites_outside_unit_cell",
                                },
                                {
                                    "label": "Hide bonds where destination atoms are not shown",
                                    "value": "hide_incomplete_bonds",
                                },
                            ],
                            value=[
                                opt
                                for opt in (
                                    "draw_image_atoms",
                                    "bonded_sites_outside_unit_cell",
                                    "hide_incomplete_bonds",
                                )
                                if self.initial_display_options[opt]
                            ],
                            labelStyle={"display": "block"},
                            inputClassName="mpc-radio",
                            id=self.id("draw_options"),
                        )
                    ]
                ),
                html.Label("Hide/show:", className="mpc-label"),
                html.Div(
                    [
                        dcc.Checklist(
                            options=[
                                {"label": "Atoms", "value": "atoms"},
                                {"label": "Bonds", "value": "bonds"},
                                {"label": "Unit cell", "value": "unit_cell"},
                                {"label": "Polyhedra", "value": "polyhedra"},
                            ],
                            value=["atoms", "bonds", "unit_cell", "polyhedra"],
                            labelStyle={"display": "block"},
                            inputClassName="mpc-radio",
                            id=self.id("hide-show"),
                        )
                    ],
                    className="mpc-control",
                ),
            ]
        )

        return {
            "struct": struct_layout,
            "screenshot": screenshot_layout,
            "options": options_layout,
            "title": title_layout,
            "legend": legend_layout,
        }

    @property
    def standard_layout(self):
        return html.Div(
            self.all_layouts["struct"], style={"width": "100vw", "height": "100vh"}
        )

    @staticmethod
    def _preprocess_input_to_graph(
        input: Union[Structure, StructureGraph, Molecule, MoleculeGraph],
        bonding_strategy: str = "CrystalNN",
        bonding_strategy_kwargs: Optional[Dict] = None,
    ) -> Union[StructureGraph, MoleculeGraph]:

        if isinstance(input, Structure):

            # ensure fractional co-ordinates are normalized to be in [0,1)
            # (this is actually not guaranteed by Structure)
            try:
                input = input.as_dict(verbosity=0)
            except TypeError:
                # TODO: remove this, necessary for Slab(?), some structure subclasses don't have verbosity
                input = input.as_dict()
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
        else:
            geometric_center = (0, 0, 0)

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
    def _compass_from_lattice(
        lattice,
        origin=(0, 0, 0),
        scale=0.7,
        offset=0.15,
        compass_style="corner",
        **kwargs,
    ):
        # TODO: add along lattice
        """
        Get the display components of the compass
        :param lattice: the pymatgen Lattice object that contains the primitive lattice vectors
        :param origin: the reference position to place the compass
        :param scale: scale all the geometric objects that makes up the compass the lattice vectors are normalized before the scaling so everything should be the same size
        :param offset: shift the compass from the origin by a ratio of the diagonal of the cell relative the size 
        :return: list of cystal_toolkit.helper.scene objects that makes up the compass
        """
        o = -np.array(origin)
        o = o - offset * (lattice.matrix[0] + lattice.matrix[1] + lattice.matrix[2])
        a = lattice.matrix[0] / np.linalg.norm(lattice.matrix[0]) * scale
        b = lattice.matrix[1] / np.linalg.norm(lattice.matrix[1]) * scale
        c = lattice.matrix[2] / np.linalg.norm(lattice.matrix[2]) * scale
        a_arrow = [[o, o + a]]
        b_arrow = [[o, o + b]]
        c_arrow = [[o, o + c]]

        o_sphere = Spheres(positions=[o], color="black", radius=0.1 * scale)

        return [
            Arrows(
                a_arrow,
                color="red",
                radius=0.7 * scale,
                headLength=2.3 * scale,
                headWidth=1.4 * scale,
                **kwargs,
            ),
            Arrows(
                b_arrow,
                color="blue",
                radius=0.7 * scale,
                headLength=2.3 * scale,
                headWidth=1.4 * scale,
                **kwargs,
            ),
            Arrows(
                c_arrow,
                color="green",
                radius=0.7 * scale,
                headLength=2.3 * scale,
                headWidth=1.4 * scale,
                **kwargs,
            ),
            o_sphere,
        ]

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

        allowed_schemes = (
            ["VESTA", "Jmol", "colorblind_friendly"]
            + site_prop_types.get("scalar", [])
            + site_prop_types.get("categorical", [])
        )
        default_scheme = "Jmol"
        if color_scheme not in allowed_schemes:
            warnings.warn(
                f"Color scheme {color_scheme} not available, falling back to {default_scheme}."
            )
            color_scheme = default_scheme

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

            #  TODO: define fallback color as global variable
            # TODO: maybe fallback categorical based on letter, for DummySpecie?

            colors = []
            for site in struct_or_mol:
                elements = [sp.as_dict()["element"] for sp, _ in site.species.items()]
                colors.append(
                    [
                        get_color_hex(EL_COLORS[color_scheme].get(element, [0, 0, 0]))
                        for element in elements
                    ]
                )
                # construct legend
                for element in elements:
                    color = get_color_hex(
                        EL_COLORS[color_scheme].get(element, [0, 0, 0])
                    )
                    label = unicodeify_species(site.species_string)
                    if color in legend["colors"] and legend["colors"][color] != label:
                        legend["colors"][
                            color
                        ] = f"{element}ˣ"  # TODO: mixed valence, improve this
                    else:
                        legend["colors"][color] = label

        elif color_scheme == "colorblind_friendly":

            labels = [site.species_string for site in struct_or_mol]

            # thanks to https://doi.org/10.1038/nmeth.1618
            palette = [
                [0, 0, 0],  # 0, black
                [230, 159, 0],  # 1, orange
                [86, 180, 233],  # 2, sky blue
                [0, 158, 115],  #  3, bluish green
                [240, 228, 66],  # 4, yellow
                [0, 114, 178],  # 5, blue
                [213, 94, 0],  # 6, vermillion
                [204, 121, 167],  # 7, reddish purple
                [255, 255, 255],  #  8, white
            ]

            # similar to CPK
            preferred_colors = {
                "O": 6,
                "N": 2,
                "C": 0,
                "H": 8,
                "F": 3,
                "Cl": 3,
                "Fe": 1,
                "Br": 7,
                "I": 7,
                "P": 1,
                "S": 4,
            }

            if len(set(labels)) > len(palette):
                warnings.warn(
                    "Too many distinct types of site to use a color-blind friendly color scheme."
                )

        # colors = [......]
        # present_specie = sorted(struct_or_mol.types_of_specie)
        # if len(struct_or_mol.types_of_specie) > len(colors):
        #
        #    colors.append([DEFAULT_COLOR]*(len(struct_or_mol.types_of_specie)-len(colors))
        # # test for disordered structures too!
        # # try to prefer certain colors of certain elements for historical consistency
        # preferred_colors = {"O": 1}  # idx of colors
        # for el, idx in preferred_colors.items():
        #   if el in present_specie:
        #       want (idx of el in present_specie) to match idx
        #       colors.swap(idx to present_specie_idx)
        # color_scheme = {el:colors[idx] for idx, el in enumerate(sorted(struct_or_mol.types_of_specie))}

        elif color_scheme in site_prop_types.get("scalar", []):

            props = np.array(struct_or_mol.site_properties[color_scheme])

            # by default, use blue-grey-red color scheme,
            # so that zero is ~ grey, and positive/negative
            # are red/blue
            color_scale = color_scale or "coolwarm"
            # try to keep color scheme symmetric around 0
            prop_max = max([abs(min(props)), max(props)])
            prop_min = -prop_max

            cmap = get_cmap(color_scale)
            # normalize in [0, 1] range, as expected by cmap
            props_normed = (props - prop_min) / (prop_max - prop_min)

            def get_color_cmap(x):
                return [int(c * 255) for c in cmap(x)[0:3]]

            colors = [[get_color_hex(get_color_cmap(x))] for x in props_normed]

            # construct legend
            rounded_props = sorted(list(set([np.around(p, decimals=1) for p in props])))
            for prop in rounded_props:
                prop_normed = (prop - prop_min) / (prop_max - prop_min)
                c = get_color_hex(get_color_cmap(prop_normed))
                legend["colors"][c] = "{:.1f}".format(prop)

        elif color_scheme in site_prop_types.get("categorical", []):

            props = np.array(struct_or_mol.site_properties[color_scheme])

            palette = [get_color_hex(c) for c in Set1_9.colors]

            le = LabelEncoder()
            le.fit(props)
            transformed_props = le.transform(props)

            # if we have more categories than availiable colors,
            # arbitrarily group some categories together
            warnings.warn(
                "Too many categories for a complete categorical " "color scheme."
            )
            transformed_props = [
                p if p < len(palette) else -1 for p in transformed_props
            ]

            colors = [[palette[p]] for p in transformed_props]

            for category, p in zip(props, transformed_props):
                legend["colors"][palette[p]] = category

        return colors, legend

    @staticmethod
    def _get_display_radii_for_sites(
        struct_or_mol, radius_strategy="specified_or_average_ionic", radius_scale=1.0
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

            for comp_idx, (sp, occu) in enumerate(site.species.items()):

                radius = None

                if radius_strategy == "uniform":
                    radius = 0.5
                if radius_strategy == "atomic":
                    radius = sp.atomic_radius
                elif (
                    radius_strategy == "specified_or_average_ionic"
                    and isinstance(sp, Specie)
                    and sp.oxi_state
                ):
                    radius = sp.ionic_radius
                elif radius_strategy == "specified_or_average_ionic":
                    radius = sp.average_ionic_radius
                elif radius_strategy == "covalent":
                    el = str(getattr(sp, "element", sp))
                    radius = CovalentRadius.radius[el]
                elif radius_strategy == "van_der_waals":
                    radius = sp.van_der_waals_radius
                elif radius_strategy == "atomic_calculated":
                    radius = sp.atomic_radius_calculated

                if not radius:
                    warnings.warn(
                        "Radius unknown for {} and strategy {}, "
                        "setting to 1.0.".format(sp, radius_strategy)
                    )
                    radius = 1.0

                radius = radius * radius_scale
                site_radii.append(radius)

            radii.append(site_radii)

        return radii

    @staticmethod
    def get_scene_and_legend(
        graph: Union[StructureGraph, MoleculeGraph],
        name="StructureMoleculeComponent",
        color_scheme="Jmol",
        color_scale=None,
        radius_strategy="specified_or_average_ionic",
        radius_scale=1.0,
        ellipsoid_site_prop=None,
        draw_image_atoms=True,
        bonded_sites_outside_unit_cell=True,
        hide_incomplete_bonds=False,
        explicitly_calculate_polyhedra_hull=False,
        scene_additions=None,
        show_compass=True,
    ) -> Tuple[Scene, Dict[str, str]]:

        scene = Scene(name=name)

        if graph is None:
            return scene, {}

        struct_or_mol = StructureMoleculeComponent._get_struct_or_mol(graph)
        site_prop_types = StructureMoleculeComponent._analyze_site_props(struct_or_mol)

        radii = StructureMoleculeComponent._get_display_radii_for_sites(
            struct_or_mol, radius_strategy=radius_strategy, radius_scale=radius_scale
        )
        colors, legend = StructureMoleculeComponent._get_display_colors_and_legend_for_sites(
            struct_or_mol,
            site_prop_types,
            color_scale=color_scale,
            color_scheme=color_scheme,
        )

        # TODO: add set_display_color option, set_display_radius, set_ellipsoid
        # call it "set_display_options" ?
        # sets legend too! display_legend

        struct_or_mol.add_site_property("display_radius", radii)
        struct_or_mol.add_site_property("display_color", colors)

        origin = StructureMoleculeComponent._get_origin(struct_or_mol)

        scene = graph.get_scene(
            draw_image_atoms=draw_image_atoms,
            bonded_sites_outside_unit_cell=bonded_sites_outside_unit_cell,
            hide_incomplete_bonds=hide_incomplete_bonds,
            explicitly_calculate_polyhedra_hull=explicitly_calculate_polyhedra_hull,
            origin=origin,
        )

        scene.name = name
        # TODO: ...
        scene.origin = StructureMoleculeComponent._get_origin(struct_or_mol)

        if show_compass:
            scene.contents.append(
                StructureMoleculeComponent._compass_from_lattice(
                    struct_or_mol.lattice, origin=origin
                )
            )

        if scene_additions:
            scene.contents.append(scene_additions)

        return scene, legend
