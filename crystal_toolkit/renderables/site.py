import numpy as np
from pymatgen import DummySpecie
from scipy.spatial.qhull import Delaunay

from crystal_toolkit.core.scene import Scene, Cubes, Spheres, Cylinders, Surface, Convex
from itertools import chain
from pymatgen import Site
from pymatgen.analysis.graphs import ConnectedSite

from typing import List, Optional


def get_site_scene(
    self,
    connected_sites: List[ConnectedSite] = None,
    connected_sites_not_drawn: List[ConnectedSite] = None,
    hide_incomplete_edges: bool = False,
    incomplete_edge_length_scale: Optional[float] = 1.0,
    connected_sites_colors: Optional[List[str]] = None,
    connected_sites_not_drawn_colors: Optional[List[str]] = None,
    origin: List[float] = (0, 0, 0),
    ellipsoid_site_prop: str = None,
    draw_polyhedra: bool = True,
    explicitly_calculate_polyhedra_hull: bool = False,
) -> Scene:
    """

    Args:
        self:
        connected_sites:
        connected_sites_not_drawn:
        hide_incomplete_edges:
        incomplete_edge_length_scale:
        connected_sites_colors:
        connected_sites_not_drawn_colors:
        origin:
        ellipsoid_site_prop:
        explicitly_calculate_polyhedra_hull:

    Returns:

    """

    atoms = []
    bonds = []
    polyhedron = []

    # for disordered structures
    is_ordered = self.is_ordered
    phiStart, phiEnd = None, None
    occu_start = 0.0

    # for thermal ellipsoids etc.
    def _get_ellipsoids_from_matrix(matrix):
        raise NotImplementedError
        # matrix = np.array(matrix)
        # eigenvalues, eigenvectors = np.linalg.eig(matrix)

    if ellipsoid_site_prop:
        matrix = self.properties[ellipsoid_site_prop]
        ellipsoids = _get_ellipsoids_from_matrix(matrix)
    else:
        ellipsoids = None

    position = np.subtract(self.coords, origin).tolist()

    # site_color is used for bonds and polyhedra, if multiple colors are
    # defined for site (e.g. a disordered site), then we use grey
    all_colors = set(self.properties["display_color"])
    if len(all_colors) > 1:
        site_color = "#555555"
    else:
        site_color = list(all_colors)[0]

    for idx, (sp, occu) in enumerate(self.species.items()):

        if isinstance(sp, DummySpecie):

            cube = Cubes(
                positions=[position],
                color=self.properties["display_color"][idx],
                width=0.4,
            )
            atoms.append(cube)

        else:

            color = self.properties["display_color"][idx]
            radius = self.properties["display_radius"][idx]

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
            )
            atoms.append(sphere)

    if not is_ordered and not np.isclose(phiEnd, np.pi * 2):
        # if site occupancy doesn't sum to 100%, cap sphere
        sphere = Spheres(
            positions=[position],
            color="#ffffff",
            radius=self.properties["display_radius"][0],
            phiStart=phiEnd,
            phiEnd=np.pi * 2,
        )
        atoms.append(sphere)

    if connected_sites:

        all_positions = []
        for idx, connected_site in enumerate(connected_sites):

            connected_position = np.subtract(connected_site.site.coords, origin)
            bond_midpoint = np.add(position, connected_position) / 2

            if connected_sites_colors:
                color = connected_sites_colors[idx]
            else:
                color = site_color

            cylinder = Cylinders(
                positionPairs=[[position, bond_midpoint.tolist()]], color=color
            )
            bonds.append(cylinder)
            all_positions.append(connected_position.tolist())

        if connected_sites_not_drawn and not hide_incomplete_edges:

            for idx, connected_site in enumerate(connected_sites_not_drawn):

                connected_position = np.subtract(connected_site.site.coords, origin)
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
                    positionPairs=[[position, bond_midpoint.tolist()]], color=color
                )
                bonds.append(cylinder)
                all_positions.append(connected_position.tolist())
        not_most_electro_neg = map(lambda x : x.site.specie < self.specie, connected_sites)
        if (
            draw_polyhedra
            and len(connected_sites) > 3
            and not connected_sites_not_drawn
            and not any(not_most_electro_neg)
        ):
            if explicitly_calculate_polyhedra_hull:

                try:

                    # all_positions = [[0, 0, 0], [0, 0, 10], [0, 10, 0], [10, 0, 0]]
                    # gives...
                    # .convex_hull = [[2, 3, 0], [1, 3, 0], [1, 2, 0], [1, 2, 3]]
                    # .vertex_neighbor_vertices = [1, 2, 3, 2, 3, 0, 1, 3, 0, 1, 2, 0]

                    vertices_indices = Delaunay(all_positions).convex_hull
                except Exception as e:
                    vertices_indices=[]

                vertices = [all_positions[idx] for idx in chain.from_iterable(vertices_indices)]

                polyhedron = [
                    Surface(
                        positions=vertices,
                        color=self.properties["display_color"][0],
                    )
                ]

            else:

                polyhedron = [Convex(positions=all_positions, color=site_color)]

    return Scene(
        self.species_string,
        [
            Scene("atoms", contents=atoms),
            Scene("bonds", contents=bonds),
            Scene("polyhedra", contents=polyhedron),
        ],
    )


Site.get_scene = get_site_scene
