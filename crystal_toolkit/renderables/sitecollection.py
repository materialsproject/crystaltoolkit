# SiteCollection.set_display_options()
# SiteCollection.set_display_radii()
# SiteCollection.set_display_colors()


def get_display_colors_and_legend_for_sites(
    struct_or_mol, site_prop_types, color_scheme="Jmol", color_scale=None
) -> Tuple[List[List[str]], Dict]:
    """
    Note this returns a list of lists of strings since each
    site might have multiple colors defined if the site is
    disordered.

    The legend is a dictionary whose keys are colors and values
    are corresponding element names or values, depending on the color
    scheme chosen.
    """

    # TODO: check to see if there is a bug here due to Composition being unordered(?)

    legend = {"composition": struct_or_mol.composition.as_dict(), "colors": {}}

    # don't calculate color if one is explicitly supplied
    if "display_color" in struct_or_mol.site_properties:
        # don't know what the color legend (meaning) is, so return empty legend
        return (struct_or_mol.site_properties["display_color"], legend)

    def get_color_hex(x):
        return "#{:02x}{:02x}{:02x}".format(*x)

    allowed_schemes = (
        ["VESTA", "Jmol", "colorblind_friendly"]
        + site_prop_types.get("scalar", [])
        + site_prop_types.get("categorical", [])
    )
    default_scheme = "Jmol"
    if color_scheme not in allowed_schemes:
        warnings.warn(
            f"Color scheme {color_scheme} not available, falling back to {default_scheme}."
        )
        color_scheme = default_scheme

    if color_scheme not in ("VESTA", "Jmol", "colorblind_friendly"):

        if not struct_or_mol.is_ordered:
            raise ValueError(
                "Can only use VESTA, Jmol or colorblind_friendly color "
                "schemes for disordered structures or molecules, color "
                "schemes based on site properties are ill-defined."
            )

        if (color_scheme not in site_prop_types.get("scalar", [])) and (
            color_scheme not in site_prop_types.get("categorical", [])
        ):

            raise ValueError(
                "Unsupported color scheme. Should be VESTA, Jmol, "
                "colorblind_friendly or a scalar (float) or categorical "
                "(string) site property."
            )

    if color_scheme in ("VESTA", "Jmol"):

        #  TODO: define fallback color as global variable
        # TODO: maybe fallback categorical based on letter, for DummySpecie?

        colors = []
        for site in struct_or_mol:
            elements = [sp.as_dict()["element"] for sp, _ in site.species.items()]
            colors.append(
                [
                    get_color_hex(EL_COLORS[color_scheme].get(element, [0, 0, 0]))
                    for element in elements
                ]
            )
            # construct legend
            for element in elements:
                color = get_color_hex(EL_COLORS[color_scheme].get(element, [0, 0, 0]))
                label = unicodeify_species(site.species_string)
                if color in legend["colors"] and legend["colors"][color] != label:
                    legend["colors"][
                        color
                    ] = f"{element}ˣ"  # TODO: mixed valence, improve this
                else:
                    legend["colors"][color] = label

    elif color_scheme == "colorblind_friendly":

        labels = [site.species_string for site in struct_or_mol]

        # thanks to https://doi.org/10.1038/nmeth.1618
        palette = [
            [0, 0, 0],  # 0, black
            [230, 159, 0],  # 1, orange
            [86, 180, 233],  # 2, sky blue
            [0, 158, 115],  #  3, bluish green
            [240, 228, 66],  # 4, yellow
            [0, 114, 178],  # 5, blue
            [213, 94, 0],  # 6, vermillion
            [204, 121, 167],  # 7, reddish purple
            [255, 255, 255],  #  8, white
        ]

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

        if len(set(labels)) > len(palette):
            warnings.warn(
                "Too many distinct types of site to use a color-blind friendly color scheme."
            )

    # colors = [......]
    # present_specie = sorted(struct_or_mol.types_of_specie)
    # if len(struct_or_mol.types_of_specie) > len(colors):
    #
    #    colors.append([DEFAULT_COLOR]*(len(struct_or_mol.types_of_specie)-len(colors))
    # # test for disordered structures too!
    # # try to prefer certain colors of certain elements for historical consistency
    # preferred_colors = {"O": 1}  # idx of colors
    # for el, idx in preferred_colors.items():
    #   if el in present_specie:
    #       want (idx of el in present_specie) to match idx
    #       colors.swap(idx to present_specie_idx)
    # color_scheme = {el:colors[idx] for idx, el in enumerate(sorted(struct_or_mol.types_of_specie))}

    elif color_scheme in site_prop_types.get("scalar", []):

        props = np.array(struct_or_mol.site_properties[color_scheme])

        # by default, use blue-grey-red color scheme,
        # so that zero is ~ grey, and positive/negative
        # are red/blue
        color_scale = color_scale or "coolwarm"
        # try to keep color scheme symmetric around 0
        prop_max = max([abs(min(props)), max(props)])
        prop_min = -prop_max

        cmap = get_cmap(color_scale)
        # normalize in [0, 1] range, as expected by cmap
        props_normed = (props - prop_min) / (prop_max - prop_min)

        def get_color_cmap(x):
            return [int(c * 255) for c in cmap(x)[0:3]]

        colors = [[get_color_hex(get_color_cmap(x))] for x in props_normed]

        # construct legend
        rounded_props = sorted(list(set([np.around(p, decimals=1) for p in props])))
        for prop in rounded_props:
            prop_normed = (prop - prop_min) / (prop_max - prop_min)
            c = get_color_hex(get_color_cmap(prop_normed))
            legend["colors"][c] = "{:.1f}".format(prop)

    elif color_scheme in site_prop_types.get("categorical", []):

        props = np.array(struct_or_mol.site_properties[color_scheme])

        palette = [get_color_hex(c) for c in Set1_9.colors]

        le = LabelEncoder()
        le.fit(props)
        transformed_props = le.transform(props)

        # if we have more categories than availiable colors,
        # arbitrarily group some categories together
        warnings.warn("Too many categories for a complete categorical " "color scheme.")
        transformed_props = [p if p < len(palette) else -1 for p in transformed_props]

        colors = [[palette[p]] for p in transformed_props]

        for category, p in zip(props, transformed_props):
            legend["colors"][palette[p]] = category

    return colors, legend


def set_display_options(
    struct_or_mol,
    radius_strategy=None,
    color=None,
    ellipsoids=None,
    connected_sites_color_by_weight=False,
    connected_sites_color_scheme=...,
):
    """
    Sets several special site properties for displaying
    a site. These are:

    * "display_colors"
    * "display_radii"
    * "display_ellipsoid"
    * "display_vector"



    Args:
        radius_strategy:
        color:
        ellipsoids:
        connected_sites_color_by_weight:
        connected_sites_color_scheme:

    Returns: legend dictionary

    """

    get_display_colors_and_legend_for_sites(struct_or_mol)
