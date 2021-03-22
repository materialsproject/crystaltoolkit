from pymatgen.core.periodic_table import Specie, Element
from pymatgen.core.structure import Molecule
from pymatgen.core.structure import SiteCollection, Site
from pymatgen.analysis.molecule_structure_comparator import CovalentRadius
from pymatgen.util.string import unicodeify_species

from monty.json import MSONable
from monty.serialization import loadfn

from itertools import chain
from collections import defaultdict

from palettable.colorbrewer.qualitative import Set1_9, Set2_8
from sklearn.preprocessing import LabelEncoder
from matplotlib.cm import get_cmap
from webcolors import html5_parse_legacy_color, html5_serialize_simple_color

from typing import Union, Optional, Tuple, Dict, List, Any

import warnings
import numpy as np
import os

# element colors forked from pymatgen
module_dir = os.path.dirname(os.path.abspath(__file__))
EL_COLORS = loadfn(os.path.join(module_dir, "ElementColorSchemes.yaml"))


class Legend(MSONable):
    """
    Help generate a legend (colors and radii) for a Structure or Molecule
    such that colors and radii can be displayed for the appropriate species.

    Note that species themselves have a color (for example, Oxygen is typically
    red), but that we might also want to color-code by site properties (for example,
    magnetic moment), thus this class has to take into account both the species
    present and its context (the specific site the species is at) to correctly
    generate the legend.
    """

    default_color_scheme = "Jmol"
    default_color = [0, 0, 0]
    default_radius = 1.0
    fallback_radius = 0.5
    uniform_radius = 0.5

    def __init__(
        self,
        site_collection: Union[SiteCollection, Site],
        color_scheme: str = "Jmol",
        radius_scheme: str = "uniform",
        cmap: str = "coolwarm",
        cmap_range: Optional[Tuple[float, float]] = None,
    ):
        """
        Create a legend for a given SiteCollection to choose how to
        display colors and radii for the given sites and the species
        on those sites.

        If a site has a "display_color" or "display_radius" site
        property defined, this can be used to manually override the
        displayed colors and radii respectively.

        Args:
            site_collection: SiteCollection or, for convenience, a
            single site can be provided and this will be converted
            into a SiteCollection
            color_scheme: choose how to color-code species, one of
            "Jmol", "VESTA", "accessible" or a scalar site property
            (e.g. magnetic moment) or a categorical/string site
            property (e.g. Wyckoff label)
            radius_scheme: choose the radius for a species, one of
            "atomic", "specified_or_average_ionic", "covalent",
            "van_der_waals", "atomic_calculated", "uniform"
            cmap: only used if color_mode is set to a scalar site
            property, defines the matplotlib color map to use, by
            default is blue-white-red for negative to postive values
            cmap_range: only used if color_mode is set to a scalar site
            property, defines the minimum and maximum values of the
            color scape
        """

        if isinstance(site_collection, Site):
            site_collection = Molecule.from_sites([site_collection])

        site_prop_types = self.analyze_site_props(site_collection)

        self.allowed_color_schemes = (
            ["VESTA", "Jmol", "accessible"]
            + site_prop_types.get("scalar", [])
            + site_prop_types.get("categorical", [])
        )

        self.allowed_radius_schemes = (
            "atomic",
            "specified_or_average_ionic",
            "covalent",
            "van_der_waals",
            "atomic_calculated",
            "uniform",
        )

        if color_scheme not in self.allowed_color_schemes:
            warnings.warn(
                f"Color scheme {color_scheme} not available, "
                f"falling back to {self.default_color_scheme}."
            )
            color_scheme = self.default_color_scheme

        # if color-coding by a scalar site property, determine minimum and
        # maximum values for color scheme, will default to be symmetric
        # about zero
        if color_scheme in site_prop_types.get("scalar", []) and not cmap_range:
            props = np.array(
                [
                    p
                    for p in site_collection.site_properties[color_scheme]
                    if p is not None
                ]
            )
            prop_max = max([abs(min(props)), max(props)])
            prop_min = -prop_max
            cmap_range = (prop_min, prop_max)

        el_colors = EL_COLORS.copy()
        el_colors.update(
            self.generate_accessible_color_scheme_on_the_fly(site_collection)
        )

        self.categorical_colors = self.generate_categorical_color_scheme_on_the_fly(
            site_collection, site_prop_types
        )

        self.el_colors = el_colors
        self.site_prop_types = site_prop_types
        self.site_collection = site_collection
        self.color_scheme = color_scheme
        self.radius_scheme = radius_scheme
        self.cmap = cmap
        self.cmap_range = cmap_range

    @staticmethod
    def generate_accessible_color_scheme_on_the_fly(
        site_collection: SiteCollection,
    ) -> Dict[str, Dict[str, Tuple[int, int, int]]]:
        """
        e.g. for a color scheme more appropriate for people with color blindness

        Args:
            site_collection: SiteCollection

        Returns: A dictionary in similar format to EL_COLORS

        """

        color_scheme = {}

        all_species = set(
            chain.from_iterable(
                comp.keys() for comp in site_collection.species_and_occu
            )
        )
        all_elements = sorted([sp.as_dict()["element"] for sp in all_species])

        # thanks to https://doi.org/10.1038/nmeth.1618
        palette = [
            (0, 0, 0),  # 0, black
            (230, 159, 0),  # 1, orange
            (86, 180, 233),  # 2, sky blue
            (0, 158, 115),  #  3, bluish green
            (240, 228, 66),  # 4, yellow
            (0, 114, 178),  # 5, blue
            (213, 94, 0),  # 6, vermillion
            (204, 121, 167),  # 7, reddish purple
            (255, 255, 255),  #  8, white
        ]

        # similar to CPK, mapping element to palette index
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

        if len(set(all_elements)) > len(palette):
            warnings.warn(
                "Too many distinct types of site to use an accessible color scheme, "
                "some sites will be given the default color."
            )

        preferred_elements_present = [
            el for el in all_elements if el in preferred_colors.keys()
        ]

        colors_assigned = []
        for el in preferred_elements_present:
            if preferred_colors[el] not in colors_assigned:
                color_scheme[el] = palette[preferred_colors[el]]
                colors_assigned.append(preferred_colors[el])

        remaining_elements = [
            el for el in all_elements if el not in color_scheme.keys()
        ]
        remaining_palette = [
            c for idx, c in enumerate(palette) if idx not in colors_assigned
        ]

        for el in remaining_elements:
            if remaining_palette:
                color_scheme[el] = remaining_palette.pop()

        return {"accessible": color_scheme}

    @staticmethod
    def generate_categorical_color_scheme_on_the_fly(
        site_collection: SiteCollection, site_prop_types
    ) -> Dict[str, Dict[str, Tuple[int, int, int]]]:
        """
        e.g. for Wykcoff

        Args:
            site_collection: SiteCollection

        Returns: A dictionary in similar format to EL_COLORS

        """

        color_scheme = {}

        palette = Set1_9.colors

        for site_prop_name in site_prop_types.get("categorical", []):

            props = np.array(site_collection.site_properties[site_prop_name])
            props[props == None] = "None"

            le = LabelEncoder()
            le.fit(props)
            transformed_props = le.transform(props)

            # if we have more categories than availiable colors,
            # arbitrarily group some categories together
            if len(set(props)) > len(palette):
                warnings.warn(
                    "Too many categories for a complete categorical color scheme."
                )
            transformed_props = [
                p if p < len(palette) else -1 for p in transformed_props
            ]

            colors = {name: palette[p] for name, p in zip(props, transformed_props)}

            color_scheme[site_prop_name] = colors

        return color_scheme

    def get_color(self, sp: Union[Specie, Element], site: Optional[Site] = None) -> str:
        """
        Get a color to render a specific species. Optionally, you can provide
        a site for context, since ...

        Args:
            sp: Specie or Element
            site: Site

        Returns: Color

        """

        # allow manual override by user
        if site and "display_color" in site.properties:
            color = site.properties["display_color"]
            # TODO: next two lines due to change in API, will be removed
            if isinstance(color, list) and isinstance(color[0], str):
                color = color[0]
            if isinstance(color, list):
                return html5_serialize_simple_color(color)
            else:
                return html5_serialize_simple_color(html5_parse_legacy_color(color))

        if self.color_scheme in ("VESTA", "Jmol", "accessible"):
            el = sp.as_dict()["element"]
            color = self.el_colors[self.color_scheme].get(
                el, self.el_colors["Extras"].get(el, self.default_color)
            )

        elif self.color_scheme in self.site_prop_types.get("scalar", []):

            if not site:
                raise ValueError(
                    "Requires a site for context to get the "
                    "appropriate site property."
                )

            prop = site.properties[self.color_scheme]

            if prop:

                cmap = get_cmap(self.cmap)

                # normalize in [0, 1] range, as expected by cmap
                prop_min = self.cmap_range[0]
                prop_max = self.cmap_range[1]
                prop_normed = (prop - prop_min) / (prop_max - prop_min)

                color = [int(c * 255) for c in cmap(prop_normed)[0:3]]

            else:

                # fallback if site prop is None
                color = self.default_color

        elif self.color_scheme in self.site_prop_types.get("categorical", []):

            if not site:
                raise ValueError(
                    "Requires a site for context to get the "
                    "appropriate site property."
                )

            prop = site.properties[self.color_scheme]

            color = self.categorical_colors[self.color_scheme].get(
                prop, self.default_color
            )

        else:

            raise ValueError(
                f"Unknown color for {sp} and color scheme {self.color_scheme}."
            )

        return html5_serialize_simple_color(color)

    def get_radius(
        self, sp: Union[Specie, Element], site: Optional[Site] = None
    ) -> float:

        # allow manual override by user
        if site and "display_radius" in site.properties:
            return site.properties["display_radius"]

        if self.radius_scheme not in self.allowed_radius_schemes:
            raise ValueError(
                f"Unknown radius scheme {self.radius_scheme}, "
                f"choose from: {self.allowed_radius_schemes}."
            )

        radius = None
        if self.radius_scheme == "uniform":
            radius = self.uniform_radius
        elif self.radius_scheme == "atomic":
            radius = sp.atomic_radius
        elif (
            self.radius_scheme == "specified_or_average_ionic"
            and isinstance(sp, Specie)
            and sp.oxi_state
        ):
            radius = sp.ionic_radius
        elif self.radius_scheme == "specified_or_average_ionic":
            radius = sp.average_ionic_radius
        elif self.radius_scheme == "covalent":
            el = str(getattr(sp, "element", sp))
            radius = CovalentRadius.radius[el]
        elif self.radius_scheme == "van_der_waals":
            radius = sp.van_der_waals_radius
        elif self.radius_scheme == "atomic_calculated":
            radius = sp.atomic_radius_calculated

        if not radius:
            warnings.warn(
                "Radius unknown for {} and strategy {}, "
                "setting to 0.5.".format(sp, self.radius_scheme)
            )
            radius = self.fallback_radius

        return radius

    @staticmethod
    def analyze_site_props(site_collection: SiteCollection) -> Dict[str, List[str]]:
        """
        Returns: A dictionary with keys "scalar", "matrix", "vector", "categorical"
        and values of a list of site property names corresponding to each type
        """
        # (implicitly assumes all site props for a given key are same type)
        site_prop_names = defaultdict(list)
        for name, props in site_collection.site_properties.items():
            if isinstance(props[0], float) or isinstance(props[0], int):
                site_prop_names["scalar"].append(name)
            elif isinstance(props[0], list) and len(props[0]) == 3:
                if isinstance(props[0][0], list) and len(props[0][0]) == 3:
                    site_prop_names["matrix"].append(name)
                else:
                    site_prop_names["vector"].append(name)
            elif isinstance(props[0], str):
                site_prop_names["categorical"].append(name)
        return dict(site_prop_names)

    @staticmethod
    def get_species_str(sp: Union[Specie, Element]) -> str:
        """
        Args:
            sp: Specie or Element

        Returns: string representation
        """
        # TODO: add roman numerals for oxidation state for ease of readability
        # and then move this to pymatgen string utils ...
        return unicodeify_species(str(sp))

    def get_legend(self) -> Dict[str, Any]:

        # decide what we want the labels to be
        if self.color_scheme in ("Jmol", "VESTA", "accessible"):
            label = lambda site, sp: self.get_species_str(sp)
        elif self.color_scheme in self.site_prop_types.get("scalar", {}):
            label = lambda site, sp: f"{site.properties[self.color_scheme]:.2f}"
        elif self.color_scheme in self.site_prop_types.get("categorical", {}):
            label = lambda site, sp: f"{site.properties[self.color_scheme]}"
        else:
            raise ValueError(f"Color scheme {self.color_scheme} not known.")

        legend = defaultdict(list)

        # first get all our colors for different species
        for site in self.site_collection:
            for sp, occu in site.species.items():
                legend[self.get_color(sp, site)].append(label(site, sp))

        legend = {k: ", ".join(sorted(list(set(v)))) for k, v in legend.items()}

        color_options = []
        for site_prop_type in ("scalar", "categorical"):
            if site_prop_type in self.site_prop_types:
                for prop in self.site_prop_types[site_prop_type]:
                    color_options.append(prop)

        return {
            "composition": self.site_collection.composition.as_dict(),
            "colors": legend,
            "available_color_schemes": color_options,
        }
