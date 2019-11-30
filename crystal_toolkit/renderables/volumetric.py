import numpy as np

from crystal_toolkit.core.scene import Scene, Surface

from pymatgen.io.vasp import VolumetricData
from skimage import measure


def get_volumetric_scene(
    self, data_key="total", isolvl=2.0, step_size=3, origin=None ** kwargs
):
    vertices, faces, normals, values = measure.marching_cubes_lewiner(
        self.data[data_key], level=isolvl, step_size=step_size
    )
    vertices = (
        vertices / self.data[data_key].shape
    )  # transform to fractional coordinates
    vertices = np.dot(vertices, self.structure.lattice.matrix)  # transform to cartesian
    return Scene(
        "volumetric-data",
        contents=[Surface(vertices, normals, **kwargs)],
        origin=origin,
    )


# TODO: re-think origin, shift globally at end (scene.origin)
VolumetricData.get_scene = get_volumetric_scene
