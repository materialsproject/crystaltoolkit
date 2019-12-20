from crystal_toolkit.core.scene import Scene
from crystal_toolkit.components.structure import StructureMoleculeComponent as SMC
from pymatgen import Structure
import crystal_toolkit.renderables.structuregraph


def get_scene_from_structure(self,
                             bonding_strategy= "CrystalNN",
                             bonding_strategy_kwargs= None,
                             **kwargs):
    radii = SMC._get_display_radii_for_sites(self, radius_strategy='uniform')
    colors, legend = SMC._get_display_colors_and_legend_for_sites(
        self, {}, color_scheme="VESTA")
    origin = SMC._get_origin(self)
    self.add_site_property("display_radius", radii)
    self.add_site_property("display_color", colors)
    sgraph = SMC._preprocess_input_to_graph(self,
                                            bonding_strategy=bonding_strategy,
                                            bonding_strategy_kwargs=bonding_strategy_kwargs,
                                            )
    return sgraph.get_scene(origin=origin, **kwargs)

Structure.get_scene = get_scene_from_structure