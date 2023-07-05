from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Sequence

import numpy as np
from pymatgen.core import PeriodicSite, Structure

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.scene import Scene


def _get_sites_to_draw(self, draw_image_atoms=True):
    """Returns a list of site indices and image vectors."""
    sites_to_draw = [(idx, (0, 0, 0)) for idx in range(len(self))]

    if not draw_image_atoms:  # return early if we don't need to search for image atoms
        return set(sites_to_draw)

    for idx, site in enumerate(self):
        zero_elements = [
            idx
            for idx, frac_coord in enumerate(site.frac_coords)
            if np.allclose(frac_coord, 0, atol=0.05)
        ]

        coord_permutations = [
            x
            for tmp_ in range(1, len(zero_elements) + 1)
            for x in combinations(zero_elements, tmp_)
        ]

        sites_to_draw += [
            (idx, (int(0 in perm), int(1 in perm), int(2 in perm)))
            for perm in coord_permutations
        ]

        one_elements = [
            idx
            for idx, f in enumerate(site.frac_coords)
            if np.allclose(f, 1, atol=0.05)
        ]

        coord_permutations = [
            x
            for tmp_ in range(1, len(one_elements) + 1)
            for x in combinations(one_elements, tmp_)
        ]

        sites_to_draw += [
            (idx, (-int(0 in perm), -int(1 in perm), -int(2 in perm)))
            for perm in coord_permutations
        ]

    return set(sites_to_draw)


def get_structure_scene(
    self,
    origin: Sequence[float] | None = None,
    legend: Legend | None = None,
    draw_image_atoms: bool = True,
) -> Scene:
    """Create CTK objects for the lattice and sties
    Args:
        self:  Structure object
        origin: x,y,z fractional coordinates of the origin
        legend: Legend for the sites
        draw_image_atoms: If true draw image atoms that are just outside the
        periodic boundary.

    Returns:
        CTK scene object to be rendered
    """
    origin = origin or list(-self.lattice.get_cartesian_coords([0.5, 0.5, 0.5]))

    legend = legend or Legend(self)

    primitives = defaultdict(list)

    sites_to_draw = self._get_sites_to_draw(draw_image_atoms=draw_image_atoms)

    for idx, jimage in sites_to_draw:
        site = self[idx]
        if jimage != (0, 0, 0):
            site = PeriodicSite(
                site.species,
                np.add(site.frac_coords, jimage),
                site.lattice,
                properties=site.properties,
            )
        site_scene = site.get_scene(legend=legend)
        for scene in site_scene.contents:
            primitives[scene.name] += scene.contents

    primitives["unit_cell"].append(self.lattice.get_scene())

    lattice_vectors = self.lattice.matrix.tolist()

    return Scene(
        name="Structure",
        origin=origin,
        lattice=lattice_vectors,
        contents=[
            Scene(name=key, contents=val, origin=origin)
            for key, val in primitives.items()
        ],
    )


Structure._get_sites_to_draw = _get_sites_to_draw
Structure.get_scene = get_structure_scene
