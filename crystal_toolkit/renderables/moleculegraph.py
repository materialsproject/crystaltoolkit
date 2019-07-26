from collections import defaultdict
from itertools import combinations
import numpy as np

from crystal_toolkit.core.scene import Scene


def get_molecule_graph_scene(
    molecule_graph,
    origin=(0, 0, 0),
    explicitly_calculate_polyhedra_hull=False,
    draw_polyhedra=True,
    **kwargs
) -> Scene:

    primitives = defaultdict(list)

    for idx, site in enumerate(molecule_graph.molecule):

        connected_sites = molecule_graph.get_connected_sites(idx)

        site_scene = site.get_scene(
            connected_sites=connected_sites,
            origin=origin,
            explicitly_calculate_polyhedra_hull=explicitly_calculate_polyhedra_hull,
        )
        for scene in site_scene.contents:
            primitives[scene.name] += scene.contents

    return Scene(
        name=molecule_graph.molecule.composition.reduced_formula,
        contents=[Scene(name=k, contents=v) for k, v in primitives.items()],
    )
