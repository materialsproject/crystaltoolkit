from itertools import combinations

import numpy as np

from pymatgen import PeriodicSite

from crystal_toolkit.core.scene import Scene
from crystal_toolkit.renderables.site import DefaultSiteRenderer
from crystal_toolkit.renderables.lattice import LatticeRenderer


class StructureRenderer:
    def __init__(
        self, site_renderer=None, lattice_renderer=None, draw_boundary_images=True
    ):
        self.site_renderer = site_renderer or DefaultSiteRenderer()
        self.lattice_renderer = lattice_renderer or LatticeRenderer()
        self.draw_boundary_images = draw_boundary_images

    def to_scene(self, structure, origin=(0, 0, 0)):

        scenes = [self.lattice_renderer.to_scene(lattice, origin)]
        scenes.append(
            Scene(
                name="atoms",
                contents=list(
                    chain.from_iterable(
                        [
                            self.site_renderer.to_scene(s, origin).contents
                            for s in structure
                        ]
                    )
                ),
            )
        )

        if self.draw_boundary_images:
            boundary_images = set(self.find_boundary_images(structure))

            boundary_atoms = [
                PeriodicSite(
                    structure[idx].species,
                    np.add(structure[idx].frac_coords, jimage),
                    structure[idx].lattice,
                    properties=structure[idx].properties,
                )
                for idx, jimage in boundary_images
            ]

            scenes.append(
                Scene(
                    name="boundary_atoms",
                    contents=list(
                        chain.from_iterable(
                            [
                                self.site_renderer.to_scene(s, origin).contents
                                for s in boundary_atoms
                            ]
                        )
                    ),
                )
            )

        return Scene(contents=scenes)

    def find_boundary_images(self, structure, tol=0.05):
        sites_to_draw = []

        site_coords = np.abs([site.frac_coords for site in structure])

        # Hyper optimizerd numpy calls to
        # 1. Find all fractional coordinates close to 0 or 1.0 within tol
        # 2. identify the sites corresponding to these
        # 3. mask the necessary indicies for sites and position in coordinate vector
        zero_mask = np.sum(np.floor(site_coords / tol) == False, axis=1) > 0
        zero_boundary_site_indicies = np.arange(len(structure))[zero_mask]
        zero_coord_indicies = np.outer(np.ones(len(structure)), np.arange(3))[zero_mask]

        ones_mask = (
            np.sum(
                np.floor(site_coords / tol) - np.ones(site_coords.shape) == False,
                axis=1,
            )
            > 0
        )
        ones_boundary_site_indicies = np.arange(len(structure))[ones_mask]
        ones_coord_indicies = np.outer(np.ones(len(structure)), np.arange(3))[ones_mask]

        # For each permutation of 0's or 1's
        # Add images
        for idx, zero_elements in zip(zero_boundary_site_indicies, zero_coord_indicies):

            coord_permutations = [
                x
                for l in range(1, len(zero_elements) + 1)
                for x in combinations(zero_elements, l)
            ]

            for perm in coord_permutations:
                sites_to_draw.append(
                    (idx, (int(0 in perm), int(1 in perm), int(2 in perm)))
                )

        for idx, ones_elements in zip(ones_boundary_site_indicies, ones_coord_indicies):

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
