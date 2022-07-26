from __future__ import annotations

from collections import defaultdict

from pymatgen.core.structure import Molecule

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.scene import Scene


def get_scene_from_molecule(self, origin=None, legend: Legend | None = None):
    """
    Create CTK objects for the lattice and sties
    Args:
        self:  Structure object
        origin: fractional coordinate of the origin
        legend: Legend for the sites

    Returns:
        CTK scene object to be rendered
    """

    origin = origin if origin else (0, 0, 0)

    legend = legend or Legend(self)

    primitives = defaultdict(list)

    for site in self:
        site_scene = site.get_scene(origin=origin, legend=legend)

        for scene in site_scene.contents:
            primitives[scene.name] += scene.contents

    return Scene(
        name=self.composition.reduced_formula,
        contents=[Scene(name=k, contents=v) for k, v in primitives.items()],
        origin=origin,
    )


Molecule.get_scene = get_scene_from_molecule
