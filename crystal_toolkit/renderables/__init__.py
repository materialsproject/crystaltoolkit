from crystal_toolkit.renderables.lattice import Lattice
from crystal_toolkit.renderables.moleculegraph import MoleculeGraph
from crystal_toolkit.renderables.site import Site
from crystal_toolkit.renderables.structuregraph import StructureGraph
from crystal_toolkit.renderables.structure import Structure
from crystal_toolkit.renderables.volumetric import VolumetricData
from crystal_toolkit.renderables.sitecollection import PeriodicSite


def _repr_mimebundle_(self, include=None, exclude=None):
    """
    Render Scenes using crystaltoolkit-extension for Jupyter Lab.
    """
    return {
        "application/vnd.mp.v1+json": self.get_scene().to_json(),
        "text/plain": self.__repr__(),
    }


for cls in (
    Lattice,
    MoleculeGraph,
    Site,
    StructureGraph,
    Structure,
    VolumetricData,
    PeriodicSite,
):
    cls._repr_mimebundle_ = _repr_mimebundle_
