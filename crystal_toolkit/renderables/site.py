from __future__ import annotations

from itertools import chain

import numpy as np
from pymatgen.analysis.graphs import ConnectedSite
from pymatgen.core.periodic_table import DummySpecie
from pymatgen.core.sites import Site
from pymatgen.electronic_structure.core import Magmom
from scipy.spatial.qhull import Delaunay

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.scene import (
    Arrows,
    Convex,
    Cubes,
    Cylinders,
    Scene,
    Spheres,
    Surface,
)


def get_site_scene(
    self,
    connected_sites: list[ConnectedSite] = None,
    # connected_site_metadata: None,
    # connected_sites_to_draw,
    connected_sites_not_drawn: list[ConnectedSite] = None,
    hide_incomplete_edges: bool = False,
    incomplete_edge_length_scale: float | None = 1.0,
    connected_sites_colors: list[str] | None = None,
    connected_sites_not_drawn_colors: list[str] | None = None,
    origin: list[float] | None = None,
    draw_polyhedra: bool = True,
    explicitly_calculate_polyhedra_hull: bool = False,
    bond_radius: float = 0.1,
    draw_magmoms: bool = True,
    magmom_scale: float = 1.0,
    legend: Legend | None = None,
) -> Scene:
    """

    Args:
        connected_sites:
        connected_sites_not_drawn:
        hide_incomplete_edges:
        incomplete_edge_length_scale:
        connected_sites_colors:
        connected_sites_not_drawn_colors:
        origin:
        explicitly_calculate_polyhedra_hull:
        legend:

    Returns:

    """

    atoms = []
    bonds = []
    polyhedron = []
    magmoms = []

    legend = legend or Legend(self)

    # for disordered structures
    is_ordered = self.is_ordered
    phiStart, phiEnd = None, None
    occu_start = 0.0

    position = self.coords.tolist()

    radii = [legend.get_radius(sp, site=self) for sp in self.species.keys()]
    max_radius = float(min(radii))

    for sp, occu in self.species.items():

        if isinstance(sp, DummySpecie):

            cube = Cubes(
                positions=[position], color=legend.get_color(sp, site=self), width=0.4
            )
            atoms.append(cube)

        else:

            color = legend.get_color(sp, site=self)
            radius = legend.get_radius(sp, site=self)

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

            name = str(sp)
            if occu != 1.0:
                name += f" ({occu}% occupancy)"
            name += f" ({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f})"

            if self.properties:
                for k, v in self.properties.items():
                    name += f" ({k} = {v})"

            sphere = Spheres(
                positions=[position],
                color=color,
                radius=radius,
                phiStart=phiStart,
                phiEnd=phiEnd,
                clickable=True,
                tooltip=name,
            )
            atoms.append(sphere)

        # Add magmoms
        if draw_magmoms:
            if magmom := self.properties.get("magmom"):
                # enforce type
                magmom = np.array(Magmom(magmom).get_moment())
                magmom = 2 * magmom_scale * max_radius * magmom
                tail = np.array(position) - 0.5 * np.array(magmom)
                head = np.array(position) + 0.5 * np.array(magmom)

                arrow = Arrows(
                    positionPairs=[[tail, head]],
                    color="red",
                    radius=0.20,
                    headLength=0.5,
                    headWidth=0.4,
                    clickable=True,
                )
                magmoms.append(arrow)

    if not is_ordered and not np.isclose(phiEnd, np.pi * 2):
        # if site occupancy doesn't sum to 100%, cap sphere
        sphere = Spheres(
            positions=[position],
            color="#ffffff",
            radius=max_radius,
            phiStart=phiEnd,
            phiEnd=np.pi * 2,
        )
        atoms.append(sphere)

    if connected_sites:

        # TODO: more graceful solution here
        # if ambiguous (disordered), re-use last color used
        site_color = color

        # TODO: can cause a bug if all vertices almost co-planar
        # necessary to include center site in case it's outside polyhedra
        all_positions = [self.coords]

        for idx, connected_site in enumerate(connected_sites):

            connected_position = connected_site.site.coords
            bond_midpoint = np.add(position, connected_position) / 2

            if connected_sites_colors:
                color = connected_sites_colors[idx]
            else:
                color = site_color

            cylinder = Cylinders(
                positionPairs=[[position, bond_midpoint.tolist()]],
                color=color,
                radius=bond_radius,
            )
            bonds.append(cylinder)
            all_positions.append(connected_position.tolist())

        if connected_sites_not_drawn and not hide_incomplete_edges:

            for idx, connected_site in enumerate(connected_sites_not_drawn):

                connected_position = connected_site.site.coords
                bond_midpoint = (
                    incomplete_edge_length_scale
                    * np.add(position, connected_position)
                    / 2
                )

                if connected_sites_not_drawn_colors:
                    color = connected_sites_not_drawn_colors[idx]
                else:
                    color = site_color

                cylinder = Cylinders(
                    positionPairs=[[position, bond_midpoint.tolist()]],
                    color=color,
                    radius=bond_radius,
                )
                bonds.append(cylinder)
                all_positions.append(connected_position.tolist())

        # ensure intersecting polyhedra are not shown, defaults to choose by electronegativity
        not_most_electro_negative = map(
            lambda x: (x.site.specie < self.specie) or (x.site.specie == self.specie),
            connected_sites,
        )

        all_positions = [list(p) for p in all_positions]

        if (
            draw_polyhedra
            and len(connected_sites) > 3
            and not connected_sites_not_drawn
            and not any(not_most_electro_negative)
        ):
            if explicitly_calculate_polyhedra_hull:

                try:

                    # all_positions = [[0, 0, 0], [0, 0, 10], [0, 10, 0], [10, 0, 0]]
                    # gives...
                    # .convex_hull = [[2, 3, 0], [1, 3, 0], [1, 2, 0], [1, 2, 3]]
                    # .vertex_neighbor_vertices = [1, 2, 3, 2, 3, 0, 1, 3, 0, 1, 2, 0]

                    vertices_indices = Delaunay(all_positions).convex_hull
                except Exception:
                    vertices_indices = []

                vertices = [
                    all_positions[idx] for idx in chain.from_iterable(vertices_indices)
                ]

                polyhedron = [Surface(positions=vertices, color=site_color)]

            else:

                polyhedron = [Convex(positions=all_positions, color=site_color)]

    return Scene(
        self.species_string,
        [
            Scene("atoms", contents=atoms),
            Scene("bonds", contents=bonds),
            Scene("polyhedra", contents=polyhedron),
            Scene("magmoms", contents=magmoms),
        ],
        origin=origin,
    )


Site.get_scene = get_site_scene
