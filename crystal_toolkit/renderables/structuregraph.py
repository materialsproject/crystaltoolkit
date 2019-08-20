import numpy as np
from itertools import combinations

from pymatgen import PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from crystal_toolkit.core.scene import Scene
from crystal_toolkit.renderables.site import StructureRenderer


class StructureGraphRenderer(StructureRenderer):
    def __init__(
        self,
        draw_bonds=True,
        draw_polyhedra=True,
        draw_connected_atoms=True,
        color_edges_by_edge_weight=True,
        edge_weight_color_scale="coolwarm",
        explicitly_calculate_polyhedra_hull=False,
        **kwargs
    ):

        self.draw_bonds = draw_bonds
        self.draw_polyhedra = draw_polyhedra
        self.draw_connected_atoms = draw_connected_atoms
        self.color_edges_by_edge_weight = color_edges_by_edge_weight
        self.edge_weight_color_scale = edge_weight_color_scale
        self.explicitly_calculate_polyhedra_hull = explicitly_calculate_polyhedra_hull

        super().__init__(**kwargs)

    def to_scene(self, structure_graph, origin=(0, 0, 0)):

        scenes = []
        scenes.extend(super().to_scene(structure_graph.structure, origin).contents)

        boundary_images = (
            set(self.find_boundary_images(structure))
            if self.draw_boundary_images
            else {}
        )

        images = (
            self.find_connected_atoms(structure_graph, boundary_images)
            if self.draw_connected_atoms
            else {}
        )
        base_atoms = [(idx, (0, 0, 0)) for idx in range(len(structure_graph.structure))]

        # All drawn atoms
        all_drawn_atoms = set(base_atoms) + set(boundary_images) + set(images)

        if self.draw_connected_atoms:

            image_atoms = [
                PeriodicSite(
                    structure_graph.structure[idx].species,
                    np.add(structure_graph.structure[idx].frac_coords, jimage),
                    structure_graph.structure[idx].lattice,
                    properties=structure_graph.structure[idx].properties,
                )
                for idx, jimage in images
            ]

            image_atoms_scene = Scene(
                name="image_atoms",
                contents=list(
                    chain.from_iterable(
                        [
                            self.site_renderer.to_scene(s, origin).contents
                            for s in image_atoms
                        ]
                    )
                ),
            )
            scenes.append(image_atoms_scene)

        if self.draw_bonds:
            bonds = []
            image_bonds = []

            # Set of all atoms we have drawn
            all_drawn_atoms = set(base_atoms) + set(boundary_images) + set(images)

            for idx, jimage in all_drawn_atoms:

                site = structure_graph.structure[idx]
                position = site.coords

                for connected_site in structure_graph.get_connected_sites(
                    idx, jimage=jimage
                ):

                    bond_midpoint = np.add(position, connected_position) / 2

                    if len(site.species) > 1:
                        color = "#555555"
                    else:
                        color = connected_site.properties.get("display_color", [None])[
                            0
                        ] or self.site_renderer.color(list(site.species.keys())[0])

                    connected_position = np.subtract(connected_site.site.coords, origin)

                    bond_cylinder = Cylinders(
                        positionPairs=[[position, bond_midpoint.tolist()]], color=color
                    )
                    # If the connected site is also being drawn
                    if (connected_site.index, connected_site.jimage) in all_drawn_atoms:
                        bonds.append(bond_cylinder)
                    else:
                        image_bonds.append(bond_cylinder)

            scenes.append(Scene(name="bonds", contents=bonds))
            scenes.append(Scene(name="image_bonds", contents=image_bonds))

        if self.draw_polyhedra:

            polyhedra = []
            # Only draw polyhedra for atoms where we include all connected sites
            for idx, jimage in all_drawn_atoms:

                site = structure_graph.structure[idx]
                position = site.coords
                connected_sites = structure_graph.get_connected_sites(
                    idx, jimage=jimage
                )
                # Make a polyhedra if all connected sites are visible
                if all(c in all_drawn_atoms for c in connected_sites):
                    connected_positions = [
                        np.subtract(connected_site.site.coords, origin).tolist()
                        for connected_site in connected_sites
                    ]
                    try:

                        # connected_positions = [[0, 0, 0], [0, 0, 10], [0, 10, 0], [10, 0, 0]]
                        # gives...
                        # .convex_hull = [[2, 3, 0], [1, 3, 0], [1, 2, 0], [1, 2, 3]]
                        # .vertex_neighbor_vertices = [1, 2, 3, 2, 3, 0, 1, 3, 0, 1, 2, 0]

                        vertices_indices = Delaunay(
                            connected_positions
                        ).vertex_neighbor_vertices
                        vertices = [
                            connected_positions[idx] for idx in vertices_indices
                        ]

                        if len(site.species) > 1:
                            color = "#555555"
                        else:
                            color = connected_site.properties.get(
                                "display_color", [None]
                            )[0] or self.site_renderer.color(
                                list(site.species.keys())[0]
                            )

                        polyhedra.append(Surface(positions=vertices, color=color))

                    except Exception as e:
                        pass
                scenes.append(Scene(name="polyhedra", contents=polyhedra))

        return Scene(contents=scenes)

    def find_connected_atoms(self, structure_graph, images=None):
        """
        Finds all connected atoms one connection out from the structure.
        Will work out one connection out from any given image atoms as well
        """

        images = images or []

        base_connections = [
            (connected_site.index, connected_site.jimage)
            for n, _ in enumerate(structure_graph.structure)
            for connected_site in structure_graph.get_connected_sites(
                n, jimage=(0, 0, 0)
            )
        ]

        image_connections = [
            (connected_site.index, connected_site.jimage)
            for n, jimage in images
            for connected_site in structure_graph.get_connected_sites(n, jimage)
        ]

        sites_to_append = {
            (n, jimage)
            for n, jimage in chain(base_connections, image_connections)
            if jimage != (0, 0, 0)
        }

        return sites_to_append - images
