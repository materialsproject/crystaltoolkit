from crystal_toolkit.core.scene import Scene
from crystal_toolkit.core.renderable import Renderer
import crystal_toolkit.renderables

from pymatgen import Lattice, Site, Structure
from pymatgen.analysis.graphs import MoleculeGraph
from pymatgen.analysis.graphs import StructureGraph



def test_Lattice():
	latt = Lattice([[1.0,0,0],[0,1.0,0],[0,0,1.0]])
	latt_scene = Renderer.render(latt)
	assert type(latt_scene) == Scene


def test_Site():

	# TODO: Move display_color and display_radius into something else
	# TODO: What are the formats for display_color and display_radius?
	site = Site("Fe", [0.25, 0.35, 0.45],properties={"display_color": "ff0000", "display_radius": 1})
	site_scene = Renderer.render(site)
	assert type(site_scene) == Scene


def test_StructureGraph():
	structure = Structure(Lattice.tetragonal(5.0, 50.0), ["H"], [[0, 0, 0]])
	structure.add_site_property("display_color",["ff0000"])
	structure.add_site_property("display_radius",[1])
	struc_graph = StructureGraph.with_empty_graph(
            structure, edge_weight_name="", edge_weight_units=""
        )

	struc_graph_scene = Renderer.render(struc_graph)
	assert type(struc_graph_scene) == Scene
