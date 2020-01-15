from crystal_toolkit.core.scene import Scene
from crystal_toolkit.components.structure import StructureMoleculeComponent as SMC
from pymatgen import Structure
import crystal_toolkit.renderables.structuregraph


def get_scene_from_structure(self,
                             bonding_strategy="CrystalNN",
                             bonding_strategy_kwargs=None,
                             **kwargs):
    sgraph = SMC._preprocess_input_to_graph(self,
                                            bonding_strategy=bonding_strategy,
                                            bonding_strategy_kwargs=bonding_strategy_kwargs,
                                            )
    return sgraph.get_scene(origin=None, **kwargs)


Structure.get_scene = get_scene_from_structure
