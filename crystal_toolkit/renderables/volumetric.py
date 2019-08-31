import numpy as np

from crystal_toolkit.core.scene import Scene, Surface

from pymatgen.io.vasp import VolumetricData
from skimage import measure
import crystal_toolkit.renderables.structure


def get_isosurface_scene(self,
                         data_key='total',
                         isolvl=10.0,
                         step_size=3,
                         origin_frac = (0.5,0.5,0.5),
                         **kwargs):
    o = -np.array(origin_frac)
    padded_data = np.pad(self.data[data_key], (0,1),"wrap")
    vertices, faces, normals, values = measure.marching_cubes_lewiner(
        padded_data, level=isolvl, step_size=step_size)
    vertices = vertices/self.data[data_key].shape  # transform to fractional coordinates
    vertices = np.dot(o + vertices, self.structure.lattice.matrix) # transform to cartesian
    pos = [vert for triangle in vertices[faces].tolist() for vert in triangle]
    return Scene("isosurface", contents=[Surface(pos, show_edges=False, color='cornflowerblue', **kwargs)])

# TODO: re-think origin, shift globally at end (scene.origin)
def get_volumetric_scene(self,
                         data_key='total',
                         isolvl=10.0,
                         step_size=3,
                         iso_kwargs_dict=None, 
                         origin_frac = (0.5,0.5,0.5),
                         **struct_kwargs):
    iso_kwags = iso_kwargs_dict or {}
    struct_scene = self.structure.get_scene(**struct_kwargs)
    iso_scene = self.get_isosurface_scene(data_key='total',
                                          isolvl=isolvl,
                                          step_size=step_size,
                                          origin_frac=origin_frac,
                                          **iso_kwags)
    return Scene("volumetric-data", contents=[struct_scene, iso_scene])

# todo: re-think origin, shift globally at end (scene.origin)
VolumetricData.get_isosurface_scene  = get_isosurface_scene
VolumetricData.get_scene = get_volumetric_scene
