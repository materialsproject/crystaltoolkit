from collections import defaultdict
from itertools import combinations

import numpy as np
from pymatgen import PeriodicSite
from pymatgen.analysis.graphs import MoleculeGraph

from crystal_toolkit.core.scene import Scene


def get_molecule_graph_scene(
    self,
    origin=(0, 0, 0),
    explicitly_calculate_polyhedra_hull=False,
    draw_polyhedra=True,
    **kwargs
) -> Scene:

    primitives = defaultdict(list)

    for idx, site in enumerate(self.molecule):

        connected_sites = self.get_connected_sites(idx)

        site_scene = site.get_scene(
            connected_sites=connected_sites,
            all_connected_sites_present=draw_polyhedra,
            origin=origin,
            explicitly_calculate_polyhedra_hull=explicitly_calculate_polyhedra_hull,
        )
        for scene in site_scene.contents:
            primitives[scene.name] += scene.contents

    return Scene(
        name=self.molecule.composition.reduced_formula,
        contents=[Scene(name=k, contents=v) for k, v in primitives.items()],
    )


MoleculeGraph.get_scene = get_molecule_graph_scene
