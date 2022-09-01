from collections import defaultdict
from itertools import combinations

import numpy as np
from pymatgen.analysis.graphs import MoleculeGraph

from crystal_toolkit.core.scene import Scene
from crystal_toolkit.core.legend import Legend


# TODO: fix Sam's bug (reorder)


def get_molecule_graph_scene(
    self,
    origin=None,
    explicitly_calculate_polyhedra_hull=False,
    legend=None,
    draw_polyhedra=False,
) -> Scene:

    legend = legend or Legend(self.molecule)

    primitives = defaultdict(list)

    for idx, site in enumerate(self.molecule):

        connected_sites = self.get_connected_sites(idx)

        site_scene = site.get_scene(
            connected_sites=connected_sites,
            origin=origin,
            explicitly_calculate_polyhedra_hull=explicitly_calculate_polyhedra_hull,
            legend=legend,
            draw_polyhedra=draw_polyhedra,
        )
        for scene in site_scene.contents:
            primitives[scene.name] += scene.contents

    return Scene(
        name=self.molecule.composition.reduced_formula,
        contents=[Scene(name=k, contents=v) for k, v in primitives.items()],
        origin=origin if origin else (0, 0, 0),
    )


MoleculeGraph.get_scene = get_molecule_graph_scene
