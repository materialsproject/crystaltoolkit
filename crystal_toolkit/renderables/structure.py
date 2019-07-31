import numpy as np

from crystal_toolkit.core.scene import Scene
from crystal_toolkit.renderables.site import DefaultSiteRenderer
from crystal_toolkit.renderables.lattice import LatticeRenderer



class StructureRenderer:
    def __init__(self, site_renderer=None, lattice_renderer=None):
        self.site_renderer = site_renderer or DefaultSiteRenderer()
        self.lattice_renderer = lattice_renderer or LatticeRenderer()

    def to_scene(self, structure, origin=(0, 0, 0)):

        lattice_scene = self.lattice_renderer.to_scene(lattice, origin)
        sites = Scene(
            name="atoms",
            contents=list(
                chain.from_iterable(
                    [self.site_renderer.to_scene(s, origin).contents for s in structure]
                )
            ),
        )
        return Scene(contents=[lattice_scene] + sites_scenes)
