import numpy as np

from crystal_toolkit.core.scene import Scene, Surface

from pymatgen.io.vasp import VolumetricData
from skimage import measure


def get_volumetric_scene(self,
                         origin=(0, 0, 0),
                         data_key='total',
                         isolvl=2.0,
                         step_size=3,
                         **kwargs):
    o = -np.array(origin)
    print(self.data)
    vertices, faces, normals, values = measure.marching_cubes_lewiner(
        self.data[data_key], level=isolvl, step_size=step_size)
    vertices = vertices/self.data[data_key].shape  # transform to fractional coordinates
    vertices = np.dot(o + vertices, self.structure.lattice.matrix) # transform to cartesian
    return Scene("volumetric-data", contents=[Surface(vertices, normals, **kwargs)])

# todo: re-think origin, shift globally at end (scene.origin)
VolumetricData.get_scene = get_volumetric_scene