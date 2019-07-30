from crystal_toolkit.core.scene import Scene
from crystal_toolkit.core.renderable import Renderer
import crystal_toolkit.renderables

from pymatgen import Lattice, Site, Structure
from pymatgen.core.structure import SiteCollection
#from pymatgen.analysis.graphs import MoleculeGraph
#from pymatgen.analysis.graphs import StructureGraph



def test_Lattice():
	latt = Lattice([[1.0,0,0],[0,1.0,0],[0,0,1.0]])
	latt_scene = Renderer.to_scene(latt)
	assert type(latt_scene) == Scene


def test_Site():
	site = Site("Fe", [0.25, 0.35, 0.45])
	site_scene = Renderer.to_scene(site)
	assert type(site_scene) == Scene

	# TODO: Test more complex cases with changing default schemes




# def test_StructureGraph():
# 	structure = Structure(Lattice.tetragonal(5.0, 50.0), ["H"], [[0, 0, 0]])
# 	structure.add_site_property("display_color",[["ff0000"]])
# 	structure.add_site_property("display_radius",[[1.0]])
# 	struc_graph = StructureGraph.with_empty_graph(
#             structure, edge_weight_name="", edge_weight_units=""
#         )

# 	struc_graph_scene = Renderer.to_scene(struc_graph)
# 	assert type(struc_graph_scene) == Scene
