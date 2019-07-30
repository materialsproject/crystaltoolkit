import numpy as np
from pymatgen import DummySpecie

from crystal_toolkit.core.scene import Scene, Cubes, Spheres, Cylinders, Surface, Convex

from pymatgen import Site
from pymatgen.vis.structure_vtk import EL_COLORS
from pymatgen.analysis.molecule_structure_comparator import CovalentRadius

from typing import List, Optional

from palettable.colorbrewer.qualitative import Set1_9
from matplotlib.cm import get_cmap


def get_color_hex(x):
    return "#{:02x}{:02x}{:02x}".format(*x)

class DefaultSiteRenderer:
    def __init__(self, color_scheme="VESTA", radii_strategy="atomic", scale=1.0):

        available_radius_strategies = (
            "atomic",
            "specified_or_average_ionic",
            "covalent",
            "van_der_waals",
            "atomic_calculated",
            "uniform",
        )
        allowed_color_schemes = ["VESTA", "Jmol", "colorblind_friendly"]

        if radii_strategy not in available_radius_strategies:
            raise Exception(f"Radius scheme {scheme} has not been implemented")

        if color_scheme not in allowed_color_schemes:
            raise Exception(f"Color Scheme {scheme} has not been implemented")

        self.color_scheme = color_scheme
        self.radii_strategy = radii_strategy
        self.color_map = {}

    def reset_color_map(self):
        self.color_map = {}

    def color(self, specie):

        color_scheme = self.color_scheme

        if specie in self.color_map:
            return self.color_map[specie]
        elif color_scheme in ("VESTA", "Jmol"):
            color = get_color_hex(EL_COLORS[color_scheme].get(str(specie), [0, 0, 0]))
            self.color_map[specie] = color
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
                idx: c for idx, c in palette.items() if c not in self.color_map.values()
            }
            if (
                str(specie) in preferred_colors
                and preferred_colors[str(specie)] in remaining_palette
            ):
                # Choose a prefereed color if available
                pref_color_index = preferred_colors[str(specie)]

                self.color_map[specie] = get_color_hex(
                    remaining_palette[pref_color_index]
                )
            else:
                # else choose next available color
                self.color_map[specie] = get_color_hex(next(remaining_palette.values()))

        return self.color_map[specie]

    def radius(self, specie):
        radii_strategy = self.radii_strategy

        if radii_strategy == "uniform":
            return 0.5
        elif radii_strategy == "atomic":
            return specie.atomic_radius
        elif (
            radii_strategy == "specified_or_average_ionic"
            and isinstance(specie, Specie)
            and specie.oxi_state
        ):
            return specie.ionic_radius
        elif radii_strategy == "specified_or_average_ionic":
            return specie.average_ionic_radius
        elif radii_strategy == "covalent":
            el = str(getattr(specie, "element", specie))
            return CovalentRadius.radius[el]
        elif radii_strategy == "van_der_waals":
            return specie.van_der_waals_radius
        elif radii_strategy == "atomic_calculated":
            return specie.atomic_radius_calculated

        raise Exception(f"Could not determine radius for {specie}")

    def to_scene(self, site, origin: List[float] = (0, 0, 0)) -> Scene:
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
            color = self.color(species[0])
            cube = Cubes(positions=[position], color=color, width=0.4)
            atoms = [cube]
        else:
            # Build PhiStart PhiEnd pairs for sphere coloring
            occupancies = list(site.species.values())
            phiList = np.cumsum([0] + occupancies).tolist()
            phiStarts = np.array(phiList[:-1]) * np.pi * 2
            phiEnds = np.array(phiList[1:]) * np.pi * 2

            display_colors = site.properties.get("display_color") or [
                self.color(sp) for sp in species
            ]

            display_radii = site.properties.get("display_radius") or [
                self.radius(sp) for sp in species
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


class VectorSiteRenderer(DefaultSiteRenderer):
    def __init__(
        self, site_property, color_scale="coolwarm", radii_strategy="atomic", scale=1.0
    ):
        # by default, use blue-grey-red color scheme,
        # so that zero is ~ grey, and positive/negative
        # are red/blue
        self.site_property = site_property
        self.color_scale = color_scale
        self.cmap = get_cmap(color_scale)

        if radii_strategy not in available_radius_strategies:
            raise Exception(f"Radius scheme {scheme} has not been implemented")

        self.radii_strategy = radii_strategy
        self.color_map = {}

    def set_prop_scale(self, sites):
        props = np.array([s.properties[self.site_property] for s in sites])
        # try to keep color scheme symmetric around 0
        self.prop_max = max([abs(min(props)), max(props)])
        self.prop_min = -prop_max

    def to_scene(self, site, origin: List[float] = (0, 0, 0)) -> Scene:

        # normalize in [0, 1] range, as expected by cmap
        prop_normed = (site.properties[self.site_property] - self.prop_min) / (
            self.prop_max - self.prop_min
        )

        def get_color_cmap(x):
            return [int(c * 255) for c in cmap(x)[0:3]]

        color = [get_color_hex(get_color_cmap(prop_normed))]

        site.property["display_colors"] = colors
        self.color_map[site.properties[self.site_property]] = color

        return super().to_scene(site, origin)


class CategoricalSiteRenderer(DefaultSiteRenderer):
    def __init__(
        self, site_property, color_scale="coolwarm", radii_strategy="atomic", scale=1.0
    ):
        # by default, use blue-grey-red color scheme,
        # so that zero is ~ grey, and positive/negative
        # are red/blue
        self.site_property = site_property
        self.color_scale = color_scale
        self.cmap = get_cmap(color_scale)

        if radii_strategy not in available_radius_strategies:
            raise Exception(f"Radius scheme {scheme} has not been implemented")

        self.radii_strategy = radii_strategy
        self.color_map = {}

    def set_prop_scale(self, sites):
        props = np.array([s.properties[self.site_property] for s in sites])

        palette = [get_color_hex(c) for c in Set1_9.colors]

        le = LabelEncoder()
        le.fit(props)
        transformed_props = le.transform(props)
        unique_props = set(transformed_props)
        # if we have more categories than availiable colors,
        # arbitrarily group some categories together
        if len(unique_props) > len(palette):
            warnings.warn(
                "Too many categories for a complete categorical " "color scheme."
            )
            # Build recurring sequence to map overlapping property set to color map
            prop_multiplicity = np.ceil(len(unique_props) / len(palette))
            prop_table = list(range(len(palette))) * prop_multiplicity
            self.color_map = {category: palette[prop_table[p]] for category, p in zip(props,transformed_props)}
        else:
            self.color_map = {category: palette[p] for category, p in zip(props,transformed_props)}

    def to_scene(self, site, origin: List[float] = (0, 0, 0)) -> Scene:

        colors = [[palette[p]] for p in transformed_props]

        sites.add_site_property("display_colors", colors)

        for category, p in zip(props, transformed_props):
            SiteCollectionRenderable.legend[palette[p]] = category

        def get_color_cmap(x):
            return [int(c * 255) for c in cmap(x)[0:3]]

        color = [get_color_hex(get_color_cmap(prop_normed))]

        site.property["display_colors"] = colors

        return super().to_scene(site, origin)
