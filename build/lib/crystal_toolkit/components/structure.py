import os
import re
import sys
import warnings
from collections import OrderedDict
from itertools import chain, combinations_with_replacement
from typing import Dict, Optional, Tuple, Union

import dash
import dash_table as dt
import numpy as np
from dash.dependencies import Input, Output, State, MATCH
from dash.exceptions import PreventUpdate
from dash_mp_components import CrystalToolkitScene
from pymatgen.analysis.graphs import MoleculeGraph, StructureGraph
from pymatgen.analysis.local_env import NearNeighbors
from pymatgen.core.composition import Composition
from pymatgen.core.periodic_table import DummySpecie
from pymatgen.core.structure import Molecule, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.scene import Scene
from crystal_toolkit.helpers.layouts import *
from crystal_toolkit.settings import SETTINGS

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# TODO: make dangling bonds "stubs"? (fixed length)

DEFAULTS = {
    "color_scheme": "VESTA",
    "bonding_strategy": "CrystalNN",
    "radius_strategy": "uniform",
    "draw_image_atoms": True,
    "bonded_sites_outside_unit_cell": False,
    "hide_incomplete_bonds": True,
    "show_compass": True,
    "unit_cell_choice": "input",
}


class StructureMoleculeComponent(MPComponent):
    """
    A component to display pymatgen Structure, Molecule, StructureGraph
    and MoleculeGraph objects.
    """

    available_bonding_strategies = {
        subclass.__name__: subclass for subclass in NearNeighbors.__subclasses__()
    }

    default_scene_settings = {
        "extractAxis": True,
        # For visual diff testing, we change the renderer
        # to SVG since this WebGL support is more difficult
        # in headless browsers / CI.
        "renderer": "svg" if SETTINGS.TEST_MODE else "webgl",
        "secondaryObjectView": False,
    }

    # what to show for the title_layout if structure/molecule not loaded
    default_title = "Crystal Toolkit"

    def __init__(
        self,
        struct_or_mol: Optional[
            Union[Structure, StructureGraph, Molecule, MoleculeGraph]
        ] = None,
        id: str = None,
        scene_additions: Optional[Scene] = None,
        bonding_strategy: str = DEFAULTS["bonding_strategy"],
        bonding_strategy_kwargs: Optional[dict] = None,
        color_scheme: str = DEFAULTS["color_scheme"],
        color_scale: Optional[str] = None,
        radius_strategy: str = DEFAULTS["radius_strategy"],
        unit_cell_choice: str = DEFAULTS["unit_cell_choice"],
        draw_image_atoms: bool = DEFAULTS["draw_image_atoms"],
        bonded_sites_outside_unit_cell: bool = DEFAULTS[
            "bonded_sites_outside_unit_cell"
        ],
        hide_incomplete_bonds: bool = DEFAULTS["hide_incomplete_bonds"],
        show_compass: bool = DEFAULTS["show_compass"],
        scene_settings: Optional[Dict] = None,
        **kwargs,
    ):
        """
        Create a StructureMoleculeComponent from a structure or molecule.

        :param struct_or_mol: input structure or molecule
        :param id: canonical id
        :param scene_additions: extra geometric elements to add to the 3D scene
        :param bonding_strategy: bonding strategy from pymatgen NearNeighbors class
        :param bonding_strategy_kwargs: options for the bonding strategy
        :param color_scheme: color scheme, see Legend class
        :param color_scale: color scale, see Legend class
        :param radius_strategy: radius strategy, see Legend class
        :param draw_image_atoms: whether to draw repeats of atoms on periodic images
        :param bonded_sites_outside_unit_cell: whether to draw sites bonded outside the unit cell
        :param hide_incomplete_bonds: whether to hide or show incomplete bonds
        :param show_compass: whether to hide or show the compass
        :param scene_settings: scene settings (lighting etc.) to pass to CrystalToolkitScene
        :param kwargs: extra keyword arguments to pass to MPComponent
        """

        super().__init__(id=id, default_data=struct_or_mol, **kwargs)

        self.initial_scene_settings = self.default_scene_settings.copy()
        if scene_settings:
            self.initial_scene_settings.update(scene_settings)

        self.create_store("scene_settings", initial_data=self.initial_scene_settings)

        # unit cell choice and bonding algorithms need to come from a settings
        # object (in a dcc.Store) guaranteed to be present in layout, rather
        # than from the controls themselves -- since these are optional and
        # may not be present in the layout
        self.create_store(
            "graph_generation_options",
            initial_data={
                "bonding_strategy": bonding_strategy,
                "bonding_strategy_kwargs": bonding_strategy_kwargs,
                "unit_cell_choice": unit_cell_choice,
            },
        )

        self.create_store(
            "display_options",
            initial_data={
                "color_scheme": color_scheme,
                "color_scale": color_scale,
                "radius_strategy": radius_strategy,
                "draw_image_atoms": draw_image_atoms,
                "bonded_sites_outside_unit_cell": bonded_sites_outside_unit_cell,
                "hide_incomplete_bonds": hide_incomplete_bonds,
                "show_compass": show_compass,
            },
        )

        if scene_additions:
            initial_scene_additions = Scene(
                name="scene_additions", contents=scene_additions
            ).to_json()
        else:
            initial_scene_additions = None
        self.create_store("scene_additions", initial_data=initial_scene_additions)

        if struct_or_mol:
            # graph is cached explicitly, this isn't necessary but is an
            # optimization so that graph is only re-generated if bonding
            # algorithm changes
            struct_or_mol = self._preprocess_structure(
                struct_or_mol, unit_cell_choice=unit_cell_choice
            )
            graph = self._preprocess_input_to_graph(
                struct_or_mol,
                bonding_strategy=bonding_strategy,
                bonding_strategy_kwargs=bonding_strategy_kwargs,
            )
            scene, legend = self.get_scene_and_legend(
                graph,
                scene_additions=self.initial_data["scene_additions"],
                **self.initial_data["display_options"],
            )
            if hasattr(struct_or_mol, "lattice"):
                self._lattice = struct_or_mol.lattice
        else:
            # component could be initialized without a structure, in which case
            # an empty scene should be displayed
            graph = None
            scene, legend = self.get_scene_and_legend(
                None,
                scene_additions=self.initial_data["scene_additions"],
                **self.initial_data["display_options"],
            )

        self.create_store("legend_data", initial_data=legend)
        self.create_store("graph", initial_data=graph)

        # this is used by a CrystalToolkitScene component, not a dcc.Store
        self._initial_data["scene"] = scene

        # hide axes inset for molecules
        if isinstance(struct_or_mol, Molecule) or isinstance(
            struct_or_mol, MoleculeGraph
        ):
            self.scene_kwargs = {"axisView": "HIDDEN"}
        else:
            self.scene_kwargs = {}

    def generate_callbacks(self, app, cache):

        # a lot of the verbosity in this callback is to support custom bonding
        # this is not the format CutOffDictNN expects (since that is not JSON
        # serializable), so we store as a list of tuples instead
        # TODO: make CutOffDictNN args JSON serializable
        app.clientside_callback(
            """
            function (bonding_strategy, custom_cutoffs_rows, unit_cell_choice) {
            
                const bonding_strategy_kwargs = {}
                if (bonding_strategy === 'CutOffDictNN') {
                    const cut_off_dict = []
                    custom_cutoffs_rows.forEach(function(row) {
                        cut_off_dict.push([row['A'], row['B'], parseFloat(row['A—B'])])
                    })
                    bonding_strategy_kwargs.cut_off_dict = cut_off_dict
                }
            
                return {
                    bonding_strategy: bonding_strategy,
                    bonding_strategy_kwargs: bonding_strategy_kwargs,
                    unit_cell_choice: unit_cell_choice
                }
            }
            """,
            Output(self.id("graph_generation_options"), "data"),
            [
                Input(self.id("bonding_algorithm"), "value"),
                Input(self.id("bonding_algorithm_custom_cutoffs"), "data"),
                Input(self.id("unit-cell-choice"), "value"),
            ],
        )

        app.clientside_callback(
            """
            function (values, options) {
                const visibility = {}
                options.forEach(function (opt) {
                    visibility[opt.value] = Boolean(values.includes(opt.value))
                })
                return visibility
            }
            """,
            Output(self.id("scene"), "toggleVisibility"),
            [Input(self.id("hide-show"), "value")],
            [State(self.id("hide-show"), "options")],
        )

        app.clientside_callback(
            """
            function (colorScheme, radiusStrategy, drawOptions, displayOptions) {
            
                const newDisplayOptions = Object.assign({}, displayOptions);
                newDisplayOptions.color_scheme = colorScheme
                newDisplayOptions.radius_strategy = radiusStrategy
                newDisplayOptions.draw_image_atoms = drawOptions.includes('draw_image_atoms')
                newDisplayOptions.bonded_sites_outside_unit_cell =  drawOptions.includes('bonded_sites_outside_unit_cell')
                newDisplayOptions.hide_incomplete_bonds = drawOptions.includes('hide_incomplete_bonds')

                return newDisplayOptions
            }
            """,
            Output(self.id("display_options"), "data"),
            [
                Input(self.id("color-scheme"), "value"),
                Input(self.id("radius_strategy"), "value"),
                Input(self.id("draw_options"), "value"),
            ],
            [State(self.id("display_options"), "data")],
        )

        @app.callback(
            Output(self.id("graph"), "data"),
            [
                Input(self.id("graph_generation_options"), "data"),
                Input(self.id(), "data"),
            ],
            [State(self.id("graph"), "data")],
        )
        @cache.memoize()
        def update_graph(graph_generation_options, struct_or_mol, current_graph):

            if not struct_or_mol:
                raise PreventUpdate

            struct_or_mol = self.from_data(struct_or_mol)
            current_graph = self.from_data(current_graph)

            bonding_strategy_kwargs = graph_generation_options[
                "bonding_strategy_kwargs"
            ]

            # TODO: add additional check here?
            unit_cell_choice = graph_generation_options["unit_cell_choice"]
            struct_or_mol = self._preprocess_structure(struct_or_mol, unit_cell_choice)

            graph = self._preprocess_input_to_graph(
                struct_or_mol,
                bonding_strategy=graph_generation_options["bonding_strategy"],
                bonding_strategy_kwargs=bonding_strategy_kwargs,
            )

            if (
                current_graph
                and graph.structure == current_graph.structure
                and graph == current_graph
            ):
                raise PreventUpdate

            return graph

        @app.callback(
            Output(self.id("scene"), "data"),
            [
                Input(self.id("graph"), "data"),
                Input(self.id("display_options"), "data"),
                Input(self.id("scene_additions"), "data"),
            ],
        )
        @cache.memoize()
        def update_scene(graph, display_options, scene_additions):
            if not graph or not display_options:
                raise PreventUpdate
            display_options = self.from_data(display_options)
            graph = self.from_data(graph)
            scene, legend = self.get_scene_and_legend(
                graph, **display_options, scene_additions=scene_additions
            )
            return scene

        @app.callback(
            Output(self.id("legend_data"), "data"),
            [
                Input(self.id("graph"), "data"),
                Input(self.id("display_options"), "data"),
                Input(self.id("scene_additions"), "data"),
            ],
        )
        @cache.memoize()
        def update_legend_and_colors(graph, display_options, scene_additions):
            if not graph or not display_options:
                raise PreventUpdate
            display_options = self.from_data(display_options)
            graph = self.from_data(graph)
            scene, legend = self.get_scene_and_legend(
                graph, **display_options, scene_additions=scene_additions
            )
            return legend

        @app.callback(
            Output(self.id("color-scheme"), "options"),
            [Input(self.id("legend_data"), "data")],
        )
        def update_color_options(legend_data):

            # TODO: make client-side
            color_options = [
                {"label": "Jmol", "value": "Jmol"},
                {"label": "VESTA", "value": "VESTA"},
                {"label": "Accessible", "value": "accessible"},
            ]

            if not legend_data:
                return color_options

            for option in legend_data["available_color_schemes"]:
                color_options += [
                    {"label": f"Site property: {option}", "value": option}
                ]

            return color_options

        # app.clientside_callback(
        #     """
        #     function (legendData) {
        #
        #         var colorOptions = [
        #             {label: "Jmol", value: "Jmol"},
        #             {label: "VESTA", value: "VESTA"},
        #             {label: "Accessible", value: "accessible"},
        #         ]
        #
        #
        #
        #         return colorOptions
        #     }
        #     """,
        #     Output(self.id("color-scheme"), "options"),
        #     [Input(self.id("legend_data"), "data")]
        # )

        @app.callback(
            Output(self.id("scene"), "imageRequest"),
            [Input(self.id("screenshot_button"), "n_clicks")],
            [State(self.id("scene"), "imageRequest"), State(self.id(), "data")],
        )
        @cache.memoize()
        def trigger_screenshot(n_clicks, current_requests, struct_or_mol):
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
                "fileType": "png",
            }

        @app.callback(
            Output(self.id("title_container"), "children"),
            [Input(self.id("legend_data"), "data")],
        )
        @cache.memoize()
        def update_title(legend):

            if not legend:
                raise PreventUpdate

            legend = self.from_data(legend)

            return self._make_title(legend)

        @app.callback(
            Output(self.id("legend_container"), "children"),
            [Input(self.id("legend_data"), "data")],
        )
        @cache.memoize()
        def update_legend(legend):

            if not legend:
                raise PreventUpdate

            legend = self.from_data(legend)

            return self._make_legend(legend)

        @app.callback(
            [
                Output(self.id("bonding_algorithm_custom_cutoffs"), "data"),
                Output(self.id("bonding_algorithm_custom_cutoffs_container"), "style"),
            ],
            [Input(self.id("bonding_algorithm"), "value")],
            [
                State(self.id("graph"), "data"),
                State(self.id("bonding_algorithm_custom_cutoffs_container"), "style"),
            ],
        )
        @cache.memoize()
        def update_custom_bond_options(bonding_algorithm, graph, current_style):

            if not graph:
                raise PreventUpdate

            if bonding_algorithm == "CutOffDictNN":
                style = {}
            else:
                style = {"display": "none"}
                if style == current_style:
                    # no need to update rows if we're not showing them
                    raise PreventUpdate

            graph = self.from_data(graph)
            rows = self._make_bonding_algorithm_custom_cuffoff_data(graph)

            return rows, style

    def _make_legend(self, legend):

        if not legend:
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
            # TODO: fix legend for Dummy Specie compositions
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
                style={"backgroundColor": color},
            )
            for color, name in legend_colors.items()
        ]

        return Field(
            [Control(el, style={"marginRight": "0.2rem"}) for el in legend_elements],
            id=self.id("legend"),
            grouped=True,
        )

    def _make_title(self, legend):

        if not legend or (not legend.get("composition", None)):
            return H2(self.default_title, id=self.id("title"))

        composition = legend["composition"]
        if isinstance(composition, dict):

            try:
                composition = Composition.from_dict(composition)

                # strip DummySpecie if present (TODO: should be method in pymatgen)
                composition = Composition(
                    {
                        el: amt
                        for el, amt in composition.items()
                        if not isinstance(el, DummySpecie)
                    }
                )
                composition = composition.get_reduced_composition_and_factor()[0]
                formula = composition.reduced_formula
                formula_parts = re.findall(r"[^\d_]+|\d+", formula)
                formula_components = [
                    html.Sub(part.strip())
                    if part.isnumeric()
                    else html.Span(part.strip())
                    for part in formula_parts
                ]
            except:
                formula_components = list(map(str, composition.keys()))

        return H2(
            formula_components, id=self.id("title"), style={"display": "inline-block"}
        )

    @staticmethod
    def _make_bonding_algorithm_custom_cuffoff_data(graph):
        if not graph:
            return [{"A": None, "B": None, "A—B": None}]
        struct_or_mol = StructureMoleculeComponent._get_struct_or_mol(graph)
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
        return rows

    @property
    def _sub_layouts(self):

        struct_layout = html.Div(
            CrystalToolkitScene(
                id=self.id("scene"),
                data=self.initial_data["scene"],
                settings=self.initial_scene_settings,
                sceneSize="100%",
                **self.scene_kwargs,
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
                    [Icon(kind="download"), html.Span(), "Download Image"],
                    kind="primary",
                    id=self.id("screenshot_button"),
                )
            ],
            # TODO: change to "bottom" when dropdown included
            style={"verticalAlign": "top", "display": "inline-block"},
        )

        title_layout = html.Div(
            self._make_title(self._initial_data["legend_data"]),
            id=self.id("title_container"),
        )

        legend_layout = html.Div(
            self._make_legend(self._initial_data["legend_data"]),
            id=self.id("legend_container"),
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
            value=self.initial_data["graph_generation_options"]["bonding_strategy"],
            clearable=False,
            id=self.id("bonding_algorithm"),
            persistence=SETTINGS.PERSISTENCE,
            persistence_type=SETTINGS.PERSISTENCE_TYPE,
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
                    data=self._make_bonding_algorithm_custom_cuffoff_data(
                        self.initial_data.get("default")
                    ),
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
                    dcc.Dropdown(
                        options=[
                            {"label": "Input cell", "value": "input"},
                            {"label": "Primitive cell", "value": "primitive"},
                            {"label": "Conventional cell", "value": "conventional"},
                            {
                                "label": "Reduced cell (Niggli)",
                                "value": "reduced_niggli",
                            },
                            {"label": "Reduced cell (LLL)", "value": "reduced_lll"},
                        ],
                        value="input",
                        clearable=False,
                        id=self.id("unit-cell-choice"),
                        persistence=SETTINGS.PERSISTENCE,
                        persistence_type=SETTINGS.PERSISTENCE_TYPE,
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
                            {"label": "Accessible", "value": "accessible"},
                        ],
                        value=self.initial_data["display_options"]["color_scheme"],
                        clearable=False,
                        persistence=SETTINGS.PERSISTENCE,
                        persistence_type=SETTINGS.PERSISTENCE_TYPE,
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
                            {
                                "label": f"Uniform ({Legend.uniform_radius}Å)",
                                "value": "uniform",
                            },
                        ],
                        value=self.initial_data["display_options"]["radius_strategy"],
                        clearable=False,
                        persistence=SETTINGS.PERSISTENCE,
                        persistence_type=SETTINGS.PERSISTENCE_TYPE,
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
                                if self.initial_data["display_options"][opt]
                            ],
                            labelStyle={"display": "block"},
                            inputClassName="mpc-radio",
                            id=self.id("draw_options"),
                            persistence=SETTINGS.PERSISTENCE,
                            persistence_type=SETTINGS.PERSISTENCE_TYPE,
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
                                {"label": "Axes", "value": "axes"},
                            ],
                            value=["atoms", "bonds", "unit_cell", "polyhedra"],
                            labelStyle={"display": "block"},
                            inputClassName="mpc-radio",
                            id=self.id("hide-show"),
                            persistence=SETTINGS.PERSISTENCE,
                            persistence_type=SETTINGS.PERSISTENCE_TYPE,
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

    def layout(self, size: str = "500px") -> html.Div:
        """
        :param size: a CSS string specifying width/height of Div
        :return: A html.Div containing the 3D structure or molecule
        """
        return html.Div(
            self._sub_layouts["struct"], style={"width": size, "height": size}
        )

    @staticmethod
    def _preprocess_structure(
        struct_or_mol: Union[Structure, StructureGraph, Molecule, MoleculeGraph],
        unit_cell_choice: Literal[
            "input", "primitive", "conventional", "reduced_niggli", "reduced_lll"
        ] = "input",
    ):
        if isinstance(struct_or_mol, Structure):
            if unit_cell_choice != "input":
                if unit_cell_choice == "primitive":
                    struct_or_mol = struct_or_mol.get_primitive_structure()
                elif unit_cell_choice == "conventional":
                    sga = SpacegroupAnalyzer(struct_or_mol)
                    struct_or_mol = sga.get_conventional_standard_structure()
                elif unit_cell_choice == "reduced_niggli":
                    struct_or_mol = struct_or_mol.get_reduced_structure(
                        reduction_algo="niggli"
                    )
                elif unit_cell_choice == "reduced_lll":
                    struct_or_mol = struct_or_mol.get_reduced_structure(
                        reduction_algo="LLL"
                    )
        return struct_or_mol

    @staticmethod
    def _preprocess_input_to_graph(
        input: Union[Structure, StructureGraph, Molecule, MoleculeGraph],
        bonding_strategy: str = DEFAULTS["bonding_strategy"],
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
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        if isinstance(input, Structure):
                            graph = StructureGraph.with_local_env_strategy(
                                input, bonding_strategy
                            )
                        else:
                            graph = MoleculeGraph.with_local_env_strategy(
                                input, bonding_strategy, reorder=False
                            )
                except:
                    # for some reason computing bonds failed, so let's not have any bonds(!)
                    if isinstance(input, Structure):
                        graph = StructureGraph.with_empty_graph(input)
                    else:
                        graph = MoleculeGraph.with_empty_graph(input)

        return graph

    @staticmethod
    def _get_struct_or_mol(
        graph: Union[StructureGraph, MoleculeGraph, Structure, Molecule]
    ) -> Union[Structure, Molecule]:
        if isinstance(graph, StructureGraph):
            return graph.structure
        elif isinstance(graph, MoleculeGraph):
            return graph.molecule
        elif isinstance(graph, Structure) or isinstance(graph, Molecule):
            return graph
        else:
            raise ValueError

    @staticmethod
    def get_scene_and_legend(
        graph: Optional[Union[StructureGraph, MoleculeGraph]],
        color_scheme=DEFAULTS["color_scheme"],
        color_scale=None,
        radius_strategy=DEFAULTS["radius_strategy"],
        draw_image_atoms=DEFAULTS["draw_image_atoms"],
        bonded_sites_outside_unit_cell=DEFAULTS["bonded_sites_outside_unit_cell"],
        hide_incomplete_bonds=DEFAULTS["hide_incomplete_bonds"],
        explicitly_calculate_polyhedra_hull=False,
        scene_additions=None,
        show_compass=DEFAULTS["show_compass"],
    ) -> Tuple[Scene, Dict[str, str]]:

        scene = Scene(name="StructureMoleculeComponentScene")

        if graph is None:
            return scene, {}

        struct_or_mol = StructureMoleculeComponent._get_struct_or_mol(graph)

        # TODO: add radius_scale
        legend = Legend(
            struct_or_mol,
            color_scheme=color_scheme,
            radius_scheme=radius_strategy,
            cmap_range=color_scale,
        )

        if isinstance(graph, StructureGraph):
            scene = graph.get_scene(
                draw_image_atoms=draw_image_atoms,
                bonded_sites_outside_unit_cell=bonded_sites_outside_unit_cell,
                hide_incomplete_edges=hide_incomplete_bonds,
                explicitly_calculate_polyhedra_hull=explicitly_calculate_polyhedra_hull,
                legend=legend,
            )
        elif isinstance(graph, MoleculeGraph):
            scene = graph.get_scene(legend=legend)

        scene.name = "StructureMoleculeComponentScene"

        if hasattr(struct_or_mol, "lattice"):
            axes = struct_or_mol.lattice._axes_from_lattice()
            axes.visible = show_compass
            scene.contents.append(axes)

        if scene_additions:
            # TODO: need a Scene.from_json() to make this work
            raise NotImplementedError
            scene["contents"].append(scene_additions)

        return scene.to_json(), legend.get_legend()

    def screenshot_layout(self):
        """
        :return: A layout including a button to trigger a screenshot download.
        """
        return self._sub_layouts["screenshot"]

    def options_layout(self):
        """
        :return: A layout including options to change the appearance, bonding, etc.
        """
        return self._sub_layouts["options"]

    def title_layout(self):
        """
        :return: A layout including the composition of the structure/molecule as a title.
        """
        return self._sub_layouts["title"]

    def legend_layout(self):
        """
        :return: A layout including a legend for the structure/molecule.
        """
        return self._sub_layouts["legend"]
