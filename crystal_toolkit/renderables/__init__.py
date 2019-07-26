from crystal_toolkit.core.renderable import Renderer
from crystal_toolkit.renderables.lattice import get_lattice_scene
from crystal_toolkit.renderables.site import get_site_scene
from crystal_toolkit.renderables.moleculegraph import get_molecule_graph_scene
from crystal_toolkit.renderables.structuregraph import get_structure_graph_scene

from pymatgen import Lattice, Site
from pymatgen.analysis.graphs import MoleculeGraph
from pymatgen.analysis.graphs import StructureGraph


Renderer.register(Lattice,get_lattice_scene)
Renderer.register(Site,get_site_scene)
Renderer.register(MoleculeGraph,get_molecule_graph_scene)
Renderer.register(StructureGraph,get_structure_graph_scene)
