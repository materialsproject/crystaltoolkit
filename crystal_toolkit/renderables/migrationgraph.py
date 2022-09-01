from turtle import pos
import numpy as np

from pymatgen.analysis.diffusion.neb.full_path_mapper import MigrationGraph
from crystal_toolkit.core.scene import Scene, Cylinders

def get_migrationgraph_scene(
    self,
) -> Scene:
    """
    Creates CTK object to display hops from a MigrationGraph object
    Args:
        mg: MigrationGraph object with hops to be visualized

    Returns:
        CTK scene object to be rendered
    """

    result_scene = self.structure.get_scene()
    hop_contents = []
    for one_hop in self.unique_hops.values():
        hop_cyl = Cylinders(positionPairs=[[list(one_hop["ipos_cart"]), list(one_hop["epos_cart"])]], radius=0.2, visible=True)
        hop_contents.append(hop_cyl)

    result_scene.contents.append(
        Scene(name="hops", origin=result_scene.contents[0].origin, contents=hop_contents)
    )
    print(result_scene.contents[-1])
    return result_scene

MigrationGraph.get_scene = get_migrationgraph_scene