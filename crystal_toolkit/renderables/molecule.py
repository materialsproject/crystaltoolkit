from collections import defaultdict
from crystal_toolkit.components.structure import StructureMoleculeComponent as SMC
from pymatgen import Molecule
from typing import Optional
import crystal_toolkit.renderables.structuregraph
from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.scene import Scene


def get_scene_from_molecule(self,
                            origin=None,
                            legend: Optional[Legend] = None):

    origin = origin if origin else (0, 0, 0)

    legend = legend or Legend(self)

    primitives = defaultdict(list)

    for idx, site in enumerate(self):
        site_scene = site.get_scene(
            origin=origin,
            legend=legend,
        )

        for scene in site_scene.contents:
            primitives[scene.name] += scene.contents

    return Scene(
        name=self.composition.reduced_formula,
        contents=[Scene(name=k, contents=v) for k, v in primitives.items()],
        origin=origin,
    )


Molecule.get_scene = get_scene_from_molecule
