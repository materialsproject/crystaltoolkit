import numpy as np
from pymatgen import DummySpecie

from crystal_toolkit.core.scene import Scene, Cubes, Spheres, Cylinders, Surface, Convex

from pymatgen import Site
from pymatgen.vis.structure_vtk import EL_COLORS
from palettable.colorbrewer.qualitative import Set1_9, Set2_8
from pymatgen.analysis.molecule_structure_comparator import CovalentRadius

from typing import List, Optional


def get_color_hex(x):
    return "#{:02x}{:02x}{:02x}".format(*x)


class SiteRenderable:

    default_color_scheme = None
    default_radii_strategy = None

    color_map = {}

    @classmethod
    def set_default_color_scheme(cls, scheme="VESTA"):
        """
        Sets the default color scheme using VESTA if
        not specified
        """
        allowed_color_schemes = ["VESTA", "Jmol", "colorblind_friendly"]
        if scheme not in allowed_color_schemes:
            raise Exception(f"Color Scheme {scheme} has not been implemented")

        SiteRenderable.color_map = {}
        SiteRenderable.default_color_scheme = scheme

    @classmethod
    def set_default_radii_strategy(cls, strategy="atomic"):
        """
        Sets the default radii scheme using atomic radii
        if not specified
        """
        available_radius_strategies = (
            "atomic",
            "specified_or_average_ionic",
            "covalent",
            "van_der_waals",
            "atomic_calculated",
            "uniform",
        )
        if strategy not in available_radius_strategies:
            raise Exception(f"Radius scheme {scheme} has not been implemented")

        SiteRenderable.default_radii_strategy = strategy

    @classmethod
    def color(cls, specie):

        if SiteRenderable.default_color_scheme == None:
            SiteRenderable.set_default_color_scheme()

        color_scheme = SiteRenderable.default_color_scheme

        if specie in SiteRenderable.color_map:
            return SiteRenderable.color_map[specie]
        elif color_scheme in ("VESTA", "Jmol"):
            color = get_color_hex(EL_COLORS[color_scheme].get(str(specie), [0, 0, 0]))
            SiteRenderable.color_map[specie] = color
        elif color_scheme == "colorblind_friendly":
            # thanks to https://doi.org/10.1038/nmeth.1618
            palette = {
                0: (0, 0, 0),  # 0, black
                1: (230, 159, 0),  # 1, orange
                2: (86, 180, 233),  # 2, sky blue
                3: (0, 158, 115),  #  3, bluish green
                4: (240, 228, 66),  # 4, yellow
                5: (0, 114, 178),  # 5, blue
                6: (213, 94, 0),  # 6, vermillion
                7: (204, 121, 167),  # 7, reddish purple
                8: (255, 255, 255),  #  8, white
            }

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

            remaining_palette = {
                idx: c
                for idx, c in palette.items()
                if c not in SiteRenderable.color_map.values()
            }
            if (
                str(specie) in preferred_colors
                and preferred_colors[str(specie)] in remaining_palette
            ):
                # Choose a prefereed color if available
                pref_color_index = preferred_colors[str(specie)]

                SiteRenderable.color_map[specie] = get_color_hex(
                    remaining_palette[pref_color_index]
                )
            else:
                # else choose next available color
                SiteRenderable.color_map[specie] = get_color_hex(
                    next(remaining_palette.values())
                )

        return SiteRenderable.color_map[specie]

    @classmethod
    def radius(cls, specie):

        if SiteRenderable.default_radii_strategy == None:
            SiteRenderable.set_default_radii_strategy()

        radius_strategy = SiteRenderable.default_radii_strategy

        if radius_strategy == "uniform":
            return 0.5
        elif radius_strategy == "atomic":
            return specie.atomic_radius
        elif (
            radius_strategy == "specified_or_average_ionic"
            and isinstance(specie, Specie)
            and specie.oxi_state
        ):
            return specie.ionic_radius
        elif radius_strategy == "specified_or_average_ionic":
            return specie.average_ionic_radius
        elif radius_strategy == "covalent":
            el = str(getattr(specie, "element", specie))
            return CovalentRadius.radius[el]
        elif radius_strategy == "van_der_waals":
            return specie.van_der_waals_radius
        elif radius_strategy == "atomic_calculated":
            return specie.atomic_radius_calculated

        raise Exception(f"Could not determine radius for {specie}")

    @staticmethod
    def get_site_scene(site, origin: List[float] = (0, 0, 0)) -> Scene:
        """

        Args:
            site:
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
        position = np.subtract(site.coords, origin).tolist()
        species = list(site.species.keys())

        if len(species) == 1 and any(isinstance(sp, DummySpecie) for sp in species):
            # If we have on Dummy Species, make it a cube
            color = SiteRenderable.color(species[0])
            cube = Cubes(positions=[position], color=color, width=0.4)
            atoms = [cube]
        else:
            # Build PhiStart PhiEnd pairs for sphere coloring
            occupancies = list(site.species.values())
            phiList = np.cumsum([0] + occupancies).tolist()
            phiStarts = np.array(phiList[:-1]) * np.pi * 2
            phiEnds = np.array(phiList[1:]) * np.pi * 2

            display_colors = site.properties.get("display_color") or [
                SiteRenderable.color(sp) for sp in species
            ]

            display_radii = site.properties.get("display_radius") or [
                SiteRenderable.radius(sp) for sp in species
            ]

            # Itterate over all species and build sphere
            for (specie, phiStart, phiEnd, color, radius) in zip(
                species, phiStarts, phiEnds, display_colors, display_radii
            ):

                sphere = Spheres(
                    positions=[position],
                    color=color,
                    radius=radius,
                    phiStart=phiStart,
                    phiEnd=phiEnd,
                )
                atoms.append(sphere)

            if not np.isclose(phiEnds[-1], np.pi * 2):
                # if site occupancy doesn't sum to 100%, cap sphere
                sphere = Spheres(
                    positions=[position],
                    color="#ffffff",
                    radius=display_radii[0],
                    phiStart=phiEnd[-1],
                    phiEnd=np.pi * 2,
                )
                atoms.append(sphere)

        return Scene(site.species_string, contents=atoms)
