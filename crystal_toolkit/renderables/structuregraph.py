from __future__ import annotations

from collections import defaultdict
from itertools import combinations

import numpy as np
from matplotlib.cm import get_cmap
from pymatgen.analysis.graphs import StructureGraph
from pymatgen.core.sites import PeriodicSite

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.scene import Scene


def _get_sites_to_draw(
    self, draw_image_atoms=True, bonded_sites_outside_unit_cell=False
):
    """Returns a list of site indices and image vectors."""

    sites_to_draw = [(idx, (0, 0, 0)) for idx in range(len(self.structure))]

    if draw_image_atoms:

        for idx, site in enumerate(self.structure):

            zero_elements = [
                idx
                for idx, f in enumerate(site.frac_coords)
                if np.allclose(f, 0, atol=0.05)
            ]

            coord_permutations = [
                x
                for length in range(1, len(zero_elements) + 1)
                for x in combinations(zero_elements, length)
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
                for length in range(1, len(one_elements) + 1)
                for x in combinations(one_elements, length)
            ]

            for perm in coord_permutations:
                sites_to_draw.append(
                    (idx, (-int(0 in perm), -int(1 in perm), -int(2 in perm)))
                )

    if bonded_sites_outside_unit_cell:

        sites_to_append = []
        for (n, jimage) in sites_to_draw:
            connected_sites = self.get_connected_sites(n, jimage=jimage)
            for connected_site in connected_sites:
                if connected_site.jimage != (0, 0, 0):
                    sites_to_append.append(
                        (connected_site.index, connected_site.jimage)
                    )
        sites_to_draw += sites_to_append

    # remove any duplicate sites
    # (can happen when enabling bonded_sites_outside_unit_cell,
    #  since this works by following bonds, and a single site outside the
    #  unit cell can be bonded to multiple atoms within it)
    return set(sites_to_draw)


def get_structure_graph_scene(
    self,
    origin=None,
    draw_image_atoms=True,
    bonded_sites_outside_unit_cell=True,
    hide_incomplete_edges=False,
    incomplete_edge_length_scale=0.3,
    color_edges_by_edge_weight=False,
    edge_weight_color_scale="coolwarm",
    explicitly_calculate_polyhedra_hull=False,
    legend: Legend | None = None,
    group_by_site_property: str | None = None,
    bond_radius: float = 0.1,
) -> Scene:

    origin = origin or list(
        -self.structure.lattice.get_cartesian_coords([0.5, 0.5, 0.5])
    )

    legend = legend or Legend(self.structure)

    # we get primitives from each site individually, then
    # combine into one big Scene
    primitives = defaultdict(list)

    sites_to_draw = self._get_sites_to_draw(
        draw_image_atoms=draw_image_atoms,
        bonded_sites_outside_unit_cell=bonded_sites_outside_unit_cell,
    )

    color_edges = False
    if color_edges_by_edge_weight:

        weights = [e[2].get("weight") for e in self.graph.edges(data=True)]
        weights = np.array([w for w in weights if w])

        if any(weights):

            cmap = get_cmap(edge_weight_color_scale)

            # try to keep color scheme symmetric around 0
            weight_max = max([abs(min(weights)), max(weights)])
            weight_min = -weight_max

            def get_weight_color(weight):
                if not weight:
                    weight = 0
                x = (weight - weight_min) / (weight_max - weight_min)
                return "#{:02x}{:02x}{:02x}".format(
                    *[int(c * 255) for c in cmap(x)[0:3]]
                )

            color_edges = True

    if group_by_site_property:
        # we will create sub-scenes for each group of atoms
        # for example, if the Structure has a "wyckoff" site property
        # this might be used to allow grouping by Wyckoff position,
        # this then changes mouseover/interaction behavior with this scene
        grouped_atom_scene_contents = defaultdict(list)

    for (idx, jimage) in sites_to_draw:

        site = self.structure[idx]
        if jimage != (0, 0, 0):
            connected_sites = self.get_connected_sites(idx, jimage=jimage)
            site = PeriodicSite(
                site.species,
                np.add(site.frac_coords, jimage),
                site.lattice,
                properties=site.properties,
            )
        else:
            connected_sites = self.get_connected_sites(idx)

        connected_sites = [
            cs for cs in connected_sites if (cs.index, cs.jimage) in sites_to_draw
        ]
        connected_sites_not_drawn = [
            cs for cs in connected_sites if (cs.index, cs.jimage) not in sites_to_draw
        ]

        if color_edges:

            connected_sites_colors = [
                get_weight_color(cs.weight) for cs in connected_sites
            ]
            connected_sites_not_drawn_colors = [
                get_weight_color(cs.weight) for cs in connected_sites_not_drawn
            ]

        else:

            connected_sites_colors = None
            connected_sites_not_drawn_colors = None

        site_scene = site.get_scene(
            connected_sites=connected_sites,
            connected_sites_not_drawn=connected_sites_not_drawn,
            hide_incomplete_edges=hide_incomplete_edges,
            incomplete_edge_length_scale=incomplete_edge_length_scale,
            connected_sites_colors=connected_sites_colors,
            connected_sites_not_drawn_colors=connected_sites_not_drawn_colors,
            explicitly_calculate_polyhedra_hull=explicitly_calculate_polyhedra_hull,
            legend=legend,
            bond_radius=bond_radius,
        )

        for scene in site_scene.contents:

            if group_by_site_property and scene.name == "atoms":

                group_name = f"{site.properties[group_by_site_property]}"
                scene.contents[0].tooltip = group_name
                grouped_atom_scene_contents[group_name] += scene.contents

            else:

                primitives[scene.name] += scene.contents

    if group_by_site_property:
        atoms_scenes: list[Scene] = []
        for k, v in grouped_atom_scene_contents.items():
            atoms_scenes.append(Scene(name=k, contents=v))
        primitives["atoms"] = atoms_scenes

    primitives["unit_cell"].append(self.structure.lattice.get_scene())

    # why primitives comprehension? just make explicit! more readable
    return Scene(
        name="StructureGraph",
        origin=origin,
        contents=[
            Scene(name=k, contents=v, origin=origin) for k, v in primitives.items()
        ],
    )


StructureGraph._get_sites_to_draw = _get_sites_to_draw
StructureGraph.get_scene = get_structure_graph_scene
