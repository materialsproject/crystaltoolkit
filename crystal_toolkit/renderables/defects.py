from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from pymatgen.analysis.defects.core import DefectComplex

from crystal_toolkit.renderables.structure import get_structure_scene

if TYPE_CHECKING:
    from typing import Sequence

    from pymatgen.analysis.defects.core import Defect

    from crystal_toolkit.core.legend import Legend
    from crystal_toolkit.core.scene import Scene


def get_defect_scene_uc(
    defect: Defect,
    origin: Sequence[float] | None = None,
    legend: Legend | None = None,
    draw_image_atoms: bool = True,
    defect_site_radius: float = 0.7,
) -> Scene:
    """Get the Scene for a Defect object.

    Merge the host structure with a Scene for the defect sites.
    Defect sites should be highlighted.

    Args:
        defect: Defect object.
        origin: x,y,z fractional coordinates of the origin
        legend: Legend for the sites
        draw_image_atoms: If true draw image atoms that are just outside the
        periodic boundary.

    Returns:
        CTK scene object to be rendered.
    """
    host_structure_scene = get_structure_scene(
        defect.structure,
        origin=origin,
        legend=legend,
        draw_image_atoms=draw_image_atoms,
    )

    def get_site_scene(site, origin):
        """Make a site for display only."""
        cp_site = deepcopy(site)
        cp_site.properties["display_radius"] = defect_site_radius
        cp_site.properties["display_color"] = "red"
        return cp_site.get_scene(origin=origin)

    if isinstance(defect, DefectComplex):
        defect_site_scenes = [
            get_site_scene(d_.site, origin=host_structure_scene.origin)
            for d_ in defect.defects
        ]
    else:
        defect_site_scenes = [
            get_site_scene(defect.site, origin=host_structure_scene.origin)
        ]

    host_structure_scene.contents.extend(defect_site_scenes)
    return host_structure_scene


def get_defect_entry_scene_sc(
    defect_entry,
    origin: Sequence[float] | None = None,
    legend: Legend | None = None,
    draw_image_atoms: bool = True,
) -> Scene:
    """Get the Scene for the DefectEntry object.

    Since many defect entries are from supercells with selective dynamics,
    We need a consistent way to emphasize that many atoms are not participating
    in the relaxation calculation.

    Args:
        defect: Defect object.
        origin: x,y,z fractional coordinates of the origin
        legend: Legend for the sites
        draw_image_atoms: If true draw image atoms that are just outside the
        periodic boundary.

    Returns:
        CTK scene object to be rendered.
    """
    sc_struct = defect_entry.sc_entry.structure
    if "selective_dynamics" in sc_struct.site_properties:
        for i, site in enumerate(sc_struct):
            if not all(site.properties["selective_dynamics"]):
                sc_struct.sites[i].properties["display_radius"] = 0.1
    return get_structure_scene(
        sc_struct,
        origin=origin,
        legend=legend,
        draw_image_atoms=draw_image_atoms,
    )
