from crystal_toolkit.core.renderable import Renderer
from crystal_toolkit.renderables.lattice import LatticeRenderer
from crystal_toolkit.renderables.site import DefaultSiteRenderer
from crystal_toolkit.renderables.moleculegraph import get_molecule_graph_scene
from crystal_toolkit.renderables.structuregraph import get_structure_graph_scene

from pymatgen import Lattice, Site
from pymatgen.core.structure import SiteCollection
from pymatgen.analysis.graphs import MoleculeGraph
from pymatgen.analysis.graphs import StructureGraph


lattice_renderer = LatticeRenderer()
site_renderer = DefaultSiteRenderer()

Renderer.register_interface(Lattice,lattice_renderer.to_scene)
Renderer.register_interface(Site,site_renderer.to_scene)
Renderer.register_interface(MoleculeGraph,get_molecule_graph_scene)
Renderer.register_interface(StructureGraph,get_structure_graph_scene)
