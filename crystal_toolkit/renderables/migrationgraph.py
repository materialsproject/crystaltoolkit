import numpy as np
from pymatgen.analysis.diffusion.neb.full_path_mapper import MigrationGraph

from crystal_toolkit.core.scene import Cylinders, Scene


def _get_extras_cross_boundary(self, one_hop, only_wi_structure):
    extras = []
    working_struct = only_wi_structure.copy()
    wi = working_struct[0].specie.name
    ori_epos = working_struct[one_hop["eindex"]]

    # extra atoms
    working_struct.insert(0, wi, one_hop["epos"])
    shifted_ipos = one_hop["ipos"] - np.array(one_hop["to_jimage"])
    working_struct.insert(0, wi, shifted_ipos)
    sites_contents = [working_struct[0].get_scene(), working_struct[1].get_scene()]
    extras.extend(sites_contents)

    # extra cylinders
    extra_ipos = list(working_struct[0].coords)
    extra_epos = list(ori_epos.coords)
    extras.append(
        Cylinders(
            positionPairs=[[extra_ipos, extra_epos]],
            radius=0.25,
            clickable=True,
        )
    )

    return extras


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

    for k, one_hop in self.unique_hops.items():
        one_hop_contents = []
        hop_cyl = Cylinders(
            positionPairs=[[list(one_hop["ipos_cart"]), list(one_hop["epos_cart"])]],
            radius=0.25,
            clickable=True,
        )
        one_hop_contents.append(hop_cyl)

        if one_hop["to_jimage"] != (0, 0, 0):
            extras_cross_boundary = self._get_extras_cross_boundary(
                one_hop, self.only_sites
            )
            one_hop_contents.extend(extras_cross_boundary)

        one_hop_scene = Scene(name=f"hop_{k}", contents=one_hop_contents)
        hop_contents.append(one_hop_scene)

    result_scene.contents.append(
        Scene(
            name="hops", origin=result_scene.contents[0].origin, contents=hop_contents
        )
    )
    return result_scene


MigrationGraph._get_extras_cross_boundary = _get_extras_cross_boundary
MigrationGraph.get_scene = get_migrationgraph_scene
