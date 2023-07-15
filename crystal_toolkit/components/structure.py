from __future__ import annotations

import re
import warnings
from base64 import b64encode
from itertools import chain, combinations_with_replacement
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal

import numpy as np
from dash import dash_table as dt
from dash.dependencies import Component, Input, Output, State
from dash.exceptions import PreventUpdate
from dash_mp_components import CrystalToolkitScene
from emmet.core.settings import EmmetSettings
from frozendict import frozendict
from pymatgen.analysis.graphs import MoleculeGraph, StructureGraph
from pymatgen.analysis.local_env import NearNeighbors
from pymatgen.core import Composition, Molecule, Species, Structure
from pymatgen.core.periodic_table import DummySpecie
from pymatgen.io.vasp.sets import MPRelaxSet
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.scene import Scene
from crystal_toolkit.helpers.layouts import H2, Field, dcc, html
from crystal_toolkit.settings import SETTINGS

# TODO: make dangling bonds "stubs"? (fixed length)

DEFAULTS: dict[str, str | bool] = {
    "color_scheme": "VESTA",
    "bonding_strategy": "CrystalNN",
    "radius_strategy": "uniform",
    "draw_image_atoms": True,
    "bonded_sites_outside_unit_cell": False,
    "hide_incomplete_bonds": True,
    "show_compass": True,
    "unit_cell_choice": "input",
    "show_legend": True,
    "show_settings": True,
    "show_controls": True,
    "show_expand_button": True,
    "show_image_button": True,
    "show_export_button": True,
    "show_position_button": True,
}


class StructureMoleculeComponent(MPComponent):
    """A component to display pymatgen Structure, Molecule, StructureGraph and MoleculeGraph
    objects.
    """

    available_bonding_strategies = frozendict(
        {subcls.__name__: subcls for subcls in NearNeighbors.__subclasses__()}
    )

    default_scene_settings = frozendict(
        extractAxis=True,
        # For visual diff testing, we change the renderer to SVG since this WebGL
        # support is more difficult in headless browsers / CI.
        renderer="svg" if SETTINGS.TEST_MODE else "webgl",
        secondaryObjectView=False,
    )

    # what to show for the title_layout if structure/molecule not loaded
    default_title = "Crystal Toolkit"

    # human-readable label to file extension
    # downloading Molecules has not yet been added
    download_options = frozendict(
        Structure={
            "CIF (Symmetrized)": {"fmt": "cif", "symprec": EmmetSettings().SYMPREC},
            "CIF": {"fmt": "cif"},
            "POSCAR": {"fmt": "poscar"},
            "JSON": {"fmt": "json"},
            "Prismatic": {"fmt": "prismatic"},
            "VASP Input Set (MPRelaxSet)": {},  # special
        }
    )

    def __init__(
        self,
        struct_or_mol: (
            None | Structure | StructureGraph | Molecule | MoleculeGraph
        ) = None,
        id: str | None = None,
        className: str = "box",
        scene_additions: Scene | None = None,
        bonding_strategy: str = DEFAULTS["bonding_strategy"],
        bonding_strategy_kwargs: dict | None = None,
        color_scheme: str = DEFAULTS["color_scheme"],
        color_scale: str | None = None,
        radius_strategy: str = DEFAULTS["radius_strategy"],
        unit_cell_choice: str = DEFAULTS["unit_cell_choice"],
        draw_image_atoms: bool = DEFAULTS["draw_image_atoms"],
        bonded_sites_outside_unit_cell: bool = DEFAULTS[
            "bonded_sites_outside_unit_cell"
        ],
        hide_incomplete_bonds: bool = DEFAULTS["hide_incomplete_bonds"],
        show_compass: bool = DEFAULTS["show_compass"],
        scene_settings: dict | None = None,
        group_by_site_property: str | None = None,
        show_legend: bool = DEFAULTS["show_legend"],
        show_settings: bool = DEFAULTS["show_settings"],
        show_controls: bool = DEFAULTS["show_controls"],
        show_expand_button: bool = DEFAULTS["show_expand_button"],
        show_image_button: bool = DEFAULTS["show_image_button"],
        show_export_button: bool = DEFAULTS["show_export_button"],
        show_position_button: bool = DEFAULTS["show_position_button"],
        **kwargs,
    ) -> None:
        """Create a StructureMoleculeComponent from a structure or molecule.

        Args:
            struct_or_mol (None |, optional): input structure or molecule. Defaults to None.
            id (str, optional): canonical id. Defaults to None.
            className (str, optional): extra geometric elements to add to the 3D scene. Defaults to "box".
            scene_additions (Scene | None, optional): bonding strategy from pymatgen NearNeighbors class.
                Defaults to None.
            bonding_strategy (str, optional): options for the bonding strategy.
            bonding_strategy_kwargs (dict | None, optional): color scheme, see Legend class.
                Defaults to None.
            color_scheme (str, optional): color scale, see Legend class.
            color_scale (str | None, optional): radius strategy, see Legend class.
                Defaults to None.
            radius_strategy (str, optional):  optional): radius strategy, see Legend class.
            unit_cell_choice (str, optional): whether to draw repeats of atoms on periodic images.
            draw_image_atoms (bool, optional): whether to draw sites bonded outside the unit cell.
            bonded_sites_outside_unit_cell (bool, optional): whether to hide or show incomplete bonds.
                Defaults to DEFAULTS[ "bonded_sites_outside_unit_cell" ].
            hide_incomplete_bonds (bool, optional): whether to hide or show the compass.
            show_compass (bool, optional): scene settings (lighting etc.) to pass to CrystalToolkitScene.
            scene_settings (dict | None, optional): a site property used for grouping of atoms for
                mouseover/interaction. Defaults to None.
            group_by_site_property (str | None, optional): a site property used for grouping of atoms for
                mouseover/interaction. Defaults to None.
            show_legend (bool, optional):  optional): show or hide legend panel within the scene.
            show_settings (bool, optional): show or hide scene control bar.
            show_controls (bool, optional): show or hide the full screen button within the scene control bar.
            show_expand_button (bool, optional): show or hide the image download button within the scene control bar.
            show_image_button (bool, optional): show or hide the file export button within the scene control bar.
            show_export_button (bool, optional): show or hide the revert position button within the scene control bar.
            show_position_button (bool, optional): extra keyword arguments to pass to MPComponent. e.g. Wyckoff label.
            **kwargs: a CSS dimension specifying width/height of Div.
        """
        super().__init__(id=id, default_data=struct_or_mol, **kwargs)
        self.className = className
        self.show_legend = show_legend
        self.show_settings = show_settings
        self.show_controls = show_controls
        self.show_expand_button = show_expand_button
        self.show_image_button = show_image_button
        self.show_export_button = show_export_button
        self.show_position_button = show_position_button

        self.initial_scene_settings = {**self.default_scene_settings}
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
                "group_by_site_property": group_by_site_property,
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
        if isinstance(struct_or_mol, (Molecule, MoleculeGraph)):
            self.scene_kwargs = {"axisView": "HIDDEN"}
        else:
            self.scene_kwargs = {}

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        # TODO due to the current increment ID counter until unique, incl. component ID in the repr breaks unit tests
        # consider adding ID to repr once ID creation is less brittle
        # id = self._id
        struct_or_mol = self._initial_data["default"]
        formula = getattr(struct_or_mol, "formula", None)
        atoms = getattr(struct_or_mol, "num_sites", None)
        return f"StructureMoleculeComponent({formula=}, {atoms=})"

    def generate_callbacks(self, app, cache) -> None:
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
            Input(self.id("bonding_algorithm"), "value"),
            Input(self.id("bonding_algorithm_custom_cutoffs"), "data"),
            Input(self.id("unit-cell-choice"), "value"),
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
            Input(self.id("hide-show"), "value"),
            State(self.id("hide-show"), "options"),
        )

        app.clientside_callback(
            """
            function (colorScheme, radiusStrategy, drawOptions, displayOptions) {

                const newDisplayOptions = {...displayOptions}
                newDisplayOptions.color_scheme = colorScheme
                newDisplayOptions.radius_strategy = radiusStrategy
                newDisplayOptions.draw_image_atoms = drawOptions.includes('draw_image_atoms')
                newDisplayOptions.bonded_sites_outside_unit_cell = drawOptions.includes(
                    'bonded_sites_outside_unit_cell'
                )
                newDisplayOptions.hide_incomplete_bonds = drawOptions.includes('hide_incomplete_bonds')

                return newDisplayOptions
            }
            """,
            Output(self.id("display_options"), "data"),
            Input(self.id("color-scheme"), "value"),
            Input(self.id("radius_strategy"), "value"),
            Input(self.id("draw_options"), "value"),
            State(self.id("display_options"), "data"),
        )

        @app.callback(
            Output(self.id("graph"), "data"),
            Input(self.id("graph_generation_options"), "data"),
            Input(self.id(), "data"),
            State(self.id("graph"), "data"),
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

            # don't update if the graph did not change.
            if current_graph:
                graph_struct_or_mol = (
                    graph.structure
                    if isinstance(graph, StructureGraph)
                    else graph.molecule
                )
                current_graph_struct_or_mol = (
                    current_graph.structure
                    if isinstance(current_graph, StructureGraph)
                    else current_graph.molecule
                )
                if (
                    graph_struct_or_mol == current_graph_struct_or_mol
                    and graph == current_graph
                ):
                    raise PreventUpdate

            return graph

        @app.callback(
            Output(self.id("scene"), "data"),
            Input(self.id("graph"), "data"),
            Input(self.id("display_options"), "data"),
            Input(self.id("scene_additions"), "data"),
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
            Input(self.id("graph"), "data"),
            Input(self.id("display_options"), "data"),
            Input(self.id("scene_additions"), "data"),
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
            Input(self.id("legend_data"), "data"),
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
        #         const colorOptions = [
        #             {label: "Jmol", value: "Jmol"},
        #             {label: "VESTA", value: "VESTA"},
        #             {label: "Accessible", value: "accessible"},
        #         ]
        #         return colorOptions
        #     }
        #     """,
        #     Output(self.id("color-scheme"), "options"),
        #     Input(self.id("legend_data"), "data"),
        # )

        @app.callback(
            Output(self.id("download-image"), "data"),
            Input(self.id("scene"), "imageDataTimestamp"),
            State(self.id("scene"), "imageData"),
            State(self.id(), "data"),
        )
        def download_image(image_data_timestamp, image_data, data):
            if not image_data_timestamp:
                raise PreventUpdate

            struct_or_mol = self.from_data(data)
            if isinstance(struct_or_mol, StructureGraph):
                formula = struct_or_mol.structure.composition.reduced_formula
            elif isinstance(struct_or_mol, MoleculeGraph):
                formula = struct_or_mol.molecule.composition.reduced_Formula
            else:
                formula = struct_or_mol.composition.reduced_formula
            spg_symbol = (
                struct_or_mol.get_space_group_info()[0]
                if hasattr(struct_or_mol, "get_space_group_info")
                else ""
            )
            request_filename = f"{formula}-{spg_symbol}-crystal-toolkit.png"

            return {
                "content": image_data[len("data:image/png;base64,") :],
                "filename": request_filename,
                "base64": True,
                "type": "image/png",
            }

        @app.callback(
            Output(self.id("download-structure"), "data"),
            Input(self.id("scene"), "fileTimestamp"),
            State(self.id("scene"), "fileType"),
            State(self.id(), "data"),
        )
        def download_structure(file_timestamp, download_option, data):
            if not file_timestamp:
                raise PreventUpdate

            structure = self.from_data(data)
            if isinstance(structure, StructureGraph):
                structure = structure.structure

            file_prefix = structure.composition.reduced_formula

            if "VASP" not in download_option:
                extension = self.download_options["Structure"][download_option]["fmt"]
                options = self.download_options["Structure"][download_option]

                try:
                    contents = structure.to(**options)
                except Exception as exc:
                    # don't fail silently, tell user what went wrong
                    contents = exc

                base64 = b64encode(contents.encode("utf-8")).decode("ascii")

                download_data = {
                    "content": base64,
                    "base64": True,
                    "type": "text/plain",
                    "filename": f"{file_prefix}.{extension}",
                }

            else:
                if "Relax" in download_option:
                    vis = MPRelaxSet(structure)
                    expected_filename = "MPRelaxSet.zip"
                else:
                    raise ValueError("No other VASP input sets currently supported.")

                with TemporaryDirectory() as tmpdir:
                    vis.write_input(tmpdir, potcar_spec=True, zip_output=True)
                    path = Path(tmpdir) / expected_filename
                    bytes = b64encode(path.read_bytes()).decode("ascii")

                download_data = {
                    "content": bytes,
                    "base64": True,
                    "type": "application/zip",
                    "filename": f"{file_prefix} {expected_filename}",
                }

            return download_data

        @app.callback(
            Output(self.id("title_container"), "children"),
            Input(self.id("legend_data"), "data"),
        )
        @cache.memoize()
        def update_title(legend):
            if not legend:
                raise PreventUpdate

            legend = self.from_data(legend)

            return self._make_title(legend)

        @app.callback(
            Output(self.id("legend_container"), "children"),
            Input(self.id("legend_data"), "data"),
        )
        @cache.memoize()
        def update_legend(legend):
            if not legend:
                raise PreventUpdate

            legend = self.from_data(legend)

            return self._make_legend(legend)

        @app.callback(
            Output(self.id("bonding_algorithm_custom_cutoffs"), "data"),
            Output(self.id("bonding_algorithm_custom_cutoffs_container"), "style"),
            Input(self.id("bonding_algorithm"), "value"),
            State(self.id("graph"), "data"),
            State(self.id("bonding_algorithm_custom_cutoffs_container"), "style"),
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
            rows = self._make_bonding_algorithm_custom_cutoff_data(graph)

            return rows, style

    def _make_legend(self, legend):
        if not legend:
            return html.Div(id=self.id("legend"))

        def get_font_color(hex_code):
            # ensures contrasting font color for background color
            c = tuple(int(hex_code[1:][i : i + 2], 16) for i in (0, 2, 4))
            return (
                "black"
                if 1 - (c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114) / 255 < 0.5
                else "white"
            )

        legend_colors = {
            key: self._legend.get_color(Species(key))
            for key, val in legend["composition"].items()
        }

        legend_elements = [
            html.Span(
                html.Span(
                    name, className="icon", style={"color": get_font_color(color)}
                ),
                className="button is-static is-rounded",
                style={"backgroundColor": color},
            )
            for name, color in legend_colors.items()
        ]

        return html.Div(
            legend_elements,
            id=self.id("legend"),
            style={"display": "flex"},
            className="buttons",
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
            except Exception:
                formula_components = list(map(str, composition))

        return H2(
            formula_components, id=self.id("title"), style={"display": "inline-block"}
        )

    @staticmethod
    def _make_bonding_algorithm_custom_cutoff_data(graph) -> list[dict[str, Any]]:
        if not graph:
            return [{"A": None, "B": None, "A—B": None}]
        struct_or_mol = StructureMoleculeComponent._get_struct_or_mol(graph)
        # can't use type_of_specie because it doesn't work with disordered structures
        species = set(
            map(
                str,
                chain.from_iterable([list(c) for c in struct_or_mol.species_and_occu]),
            )
        )
        return [  # rows
            {"A": combination[0], "B": combination[1], "A—B": 0}
            for combination in combinations_with_replacement(species, 2)
        ]

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        title_layout = html.Div(
            self._make_title(self._initial_data["legend_data"]),
            id=self.id("title_container"),
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
            options=[{"label": key, "value": val} for key, val in nn_mapping.items()],
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
                    data=self._make_bonding_algorithm_custom_cutoff_data(
                        self.initial_data.get("default")
                    ),
                    id=self.id("bonding_algorithm_custom_cutoffs"),
                ),
                html.Br(),
            ],
            id=self.id("bonding_algorithm_custom_cutoffs_container"),
            style={"display": "none"},
        )

        if self.show_settings:
            options_layout = Field(
                [
                    # TODO: hide if molecule
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
                            html.Label(
                                "Change bonding algorithm: ", className="mpc-label"
                            ),
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
                                {
                                    "label": "Ionic",
                                    "value": "specified_or_average_ionic",
                                },
                                {"label": "Covalent", "value": "covalent"},
                                {"label": "Van der Waals", "value": "van_der_waals"},
                                {
                                    "label": f"Uniform ({Legend.uniform_radius}Å)",
                                    "value": "uniform",
                                },
                            ],
                            value=self.initial_data["display_options"][
                                "radius_strategy"
                            ],
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
        else:
            options_layout = None

        if self.show_legend:
            legend_layout = html.Div(
                self._make_legend(self._initial_data["legend_data"]),
                id=self.id("legend_container"),
            )
        else:
            legend_layout = None

        struct_layout = html.Div(
            [
                CrystalToolkitScene(
                    [options_layout, legend_layout],
                    id=self.id("scene"),
                    className=self.className,
                    data=self.initial_data["scene"],
                    settings=self.initial_scene_settings,
                    sceneSize="100%",
                    fileOptions=list(self.download_options["Structure"]),
                    showControls=self.show_controls,
                    showExpandButton=self.show_expand_button,
                    showImageButton=self.show_image_button,
                    showExportButton=self.show_export_button,
                    showPositionButton=self.show_position_button,
                    **self.scene_kwargs,
                ),
                dcc.Download(id=self.id("download-image")),
                dcc.Download(id=self.id("download-structure")),
            ]
        )

        return {
            "struct": struct_layout,
            "options": options_layout,
            "title": title_layout,
            "legend": legend_layout,
        }

    def layout(self, size: str = "500px") -> html.Div:
        """Get the layout for this component.

        Args:
            size (str, optional): a CSS dimension specifying width/height of Div. Defaults to "500px".

        Returns:
            html.Div: A html.Div containing the 3D structure or molecule
        """
        return html.Div(
            self._sub_layouts["struct"], style={"width": size, "height": size}
        )

    @staticmethod
    def _preprocess_structure(
        struct_or_mol: Structure | StructureGraph | Molecule | MoleculeGraph,
        unit_cell_choice: Literal[
            "input", "primitive", "conventional", "reduced_niggli", "reduced_lll"
        ] = "input",
    ):
        if isinstance(struct_or_mol, StructureGraph) and unit_cell_choice != "input":
            # if a user is visualizing a StructureGraph, but wants to change the unit cell
            # convention, currently this means we have to convert the StructureGraph back
            # to a Structure; this will remove all bonding information and mean bonding
            # will also have to be re-calculated
            struct_or_mol = struct_or_mol.structure
        if isinstance(struct_or_mol, Structure) and unit_cell_choice != "input":
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
        input: Structure | StructureGraph | Molecule | MoleculeGraph,
        bonding_strategy: str = DEFAULTS["bonding_strategy"],
        bonding_strategy_kwargs: dict | None = None,
    ) -> StructureGraph | MoleculeGraph:
        if isinstance(input, Structure):
            # ensure fractional coordinates are normalized to be in [0,1)
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
        if isinstance(input, (StructureGraph, MoleculeGraph)):
            graph = input
        else:
            if (
                bonding_strategy
                not in StructureMoleculeComponent.available_bonding_strategies
            ):
                valid_subclasses = ", ".join(
                    StructureMoleculeComponent.available_bonding_strategies
                )
                raise ValueError(
                    "Bonding strategy not supported. Please supply a name of a NearNeighbor "
                    f"subclass, choose from: {valid_subclasses}"
                )
            else:
                bonding_strategy_kwargs = bonding_strategy_kwargs or {}
                if (
                    bonding_strategy == "CutOffDictNN"
                    and "cut_off_dict" in bonding_strategy_kwargs
                ):
                    # TODO: remove this hack by making args properly JSON serializable
                    bonding_strategy_kwargs["cut_off_dict"] = {
                        (x[0], x[1]): x[2]
                        for x in bonding_strategy_kwargs["cut_off_dict"]
                    }
                bonding_strategy = (
                    StructureMoleculeComponent.available_bonding_strategies[
                        bonding_strategy
                    ](**bonding_strategy_kwargs)
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
                except Exception:
                    # for some reason computing bonds failed, so let's not have any bonds(!)
                    if isinstance(input, Structure):
                        graph = StructureGraph.with_empty_graph(input)
                    else:
                        graph = MoleculeGraph.with_empty_graph(input)

        return graph

    @staticmethod
    def _get_struct_or_mol(
        graph: StructureGraph | MoleculeGraph | Structure | Molecule,
    ) -> Structure | Molecule:
        if isinstance(graph, StructureGraph):
            return graph.structure
        if isinstance(graph, MoleculeGraph):
            return graph.molecule
        if isinstance(graph, (Structure, Molecule)):
            return graph
        raise ValueError(
            f"Invalid input type {graph}, expected one of Structure, Molecule, StructureGraph or MoleculeGraph"
        )

    def get_scene_and_legend(
        self,
        graph: StructureGraph | MoleculeGraph | None,
        color_scheme: str = DEFAULTS["color_scheme"],  # type: ignore[assignment]
        color_scale: tuple[float, float] | None = None,
        radius_strategy=DEFAULTS["radius_strategy"],
        draw_image_atoms=DEFAULTS["draw_image_atoms"],
        bonded_sites_outside_unit_cell=DEFAULTS["bonded_sites_outside_unit_cell"],
        hide_incomplete_bonds=DEFAULTS["hide_incomplete_bonds"],
        explicitly_calculate_polyhedra_hull=False,
        scene_additions=None,
        show_compass=DEFAULTS["show_compass"],
        group_by_site_property=None,
    ) -> tuple[Scene, dict[str, str]]:
        """Get the scene and legend for a given graph.

        Args:
            graph (StructureGraph | MoleculeGraph | None): The graph to get the scene and legend for.
            color_scheme (str, optional): Color scheme for the graph. Defaults to "VESTA".
            color_scale (tuple[float, float], optional): A range of values to map to the
                color scale. Defaults to None.
            radius_strategy (str, optional): Strategy for determining atomic radii. Defaults to "uniform".
            draw_image_atoms (bool, optional): Whether to draw atoms in image cells. Defaults to True.
            bonded_sites_outside_unit_cell (bool, optional): Whether to draw bonded sites outside
                the unit cell. Defaults to False.
            hide_incomplete_bonds (bool, optional): Whether to hide incomplete bonds. Defaults to True.
            explicitly_calculate_polyhedra_hull (bool, optional): Whether to explicitly
                calculate the convex hull of polyhedra. Defaults to False.
            scene_additions (dict, optional): Additional contents to include in the scene. Defaults to None.
            show_compass (bool, optional): Whether to show a compass in the scene. Defaults to True.
            group_by_site_property (str, optional): Property by which to group sites. Defaults to None.

        Returns:
            tuple[Scene, dict[str, str]]: A tuple containing the scene and legend for the given graph.
        """
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
        self._legend = legend

        if isinstance(graph, StructureGraph):
            scene = graph.get_scene(
                draw_image_atoms=draw_image_atoms,
                bonded_sites_outside_unit_cell=bonded_sites_outside_unit_cell,
                hide_incomplete_edges=hide_incomplete_bonds,
                explicitly_calculate_polyhedra_hull=explicitly_calculate_polyhedra_hull,
                group_by_site_property=group_by_site_property,
                legend=legend,
            )
        elif isinstance(graph, MoleculeGraph):
            scene = graph.get_scene(legend=legend)

        scene.name = "StructureMoleculeComponentScene"

        if hasattr(struct_or_mol, "lattice"):
            axes = struct_or_mol.lattice._axes_from_lattice()
            axes.visible = show_compass
            scene.contents.append(axes)

        scene_json = scene.to_json()

        if scene_additions:
            # TODO: this might be cleaner if we had a Scene.from_json() method
            scene_json["contents"].append(scene_additions)

        return scene_json, legend.get_legend()

    def title_layout(self):
        """A layout including the composition of the structure/molecule as a title."""
        return self._sub_layouts["title"]
