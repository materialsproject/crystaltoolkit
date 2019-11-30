from collections import defaultdict
from itertools import combinations

import numpy as np
from pymatgen.core.sites import PeriodicSite
from pymatgen.core.structure import Structure
from pymatgen.analysis.graphs import StructureGraph

from crystal_toolkit.core.scene import Scene
from crystal_toolkit.core.legend import Legend

from typing import Optional


def _get_sites_to_draw(self, draw_image_atoms=True):
    """
    Returns a list of site indices and image vectors.
    """

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

    return set(sites_to_draw)


def get_structure_scene(
    self,
    origin=None,
    draw_image_atoms=True,
    bonded_sites_outside_unit_cell=False,
    legend: Optional[Legend] = None,
) -> Scene:

    legend = legend or Legend(self.structure)

    primitives = defaultdict(list)

    sites_to_draw = self._get_sites_to_draw(
        draw_image_atoms=draw_image_atoms,
        bonded_sites_outside_unit_cell=bonded_sites_outside_unit_cell,
    )

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

        site_scene = site.get_scene(origin=origin, legend=legend)
        for scene in site_scene.contents:
            primitives[scene.name] += scene.contents

    primitives["unit_cell"].append(self.structure.lattice.get_scene(origin=origin))

    return Scene(
        name=self.structure.composition.reduced_formula,
        contents=[Scene(name=k, contents=v) for k, v in primitives.items()],
        origin=origin,
    )


Structure.get_scene = get_structure_scene
