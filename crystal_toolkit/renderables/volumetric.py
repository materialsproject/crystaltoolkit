import numpy as np

from crystal_toolkit.core.scene import Scene, Surface

from pymatgen.io.vasp import VolumetricData
from skimage import measure
import crystal_toolkit.renderables.structure

angs2bhor3 = 1.88973**3


def get_isosurface_scene(self,
                         data_key='total',
                         isolvl=0.5,
                         step_size=3,
                         origin=(0.0, 0.0, 0.0),
                         **kwargs):
    """Get the isosurface from a VolumetricData object

    Args:
        data_key (str, optional): Use the volumetric data from self.data[data_key]. Defaults to 'total'.
        isolvl (float, optional): The cuoff for the isosurface to using the same units as VESTA so e/bhor and kept grid size independent
        step_size (int, optional): step_size parameter for marching_cubes_lewiner. Defaults to 3.

    Returns:
        [type]: [description]
    """
    vol_data = np.copy(self.data[data_key])
    vol = self.structure.volume
    vol_data = vol_data / vol / angs2bhor3

    padded_data = np.pad(vol_data, (0, 1), "wrap")
    vertices, faces, normals, values = measure.marching_cubes_lewiner(
        padded_data, level=isolvl, step_size=step_size)
    # transform to fractional coordinates
    vertices = vertices / \
        (vol_data.shape[0], vol_data.shape[1], vol_data.shape[2])
    vertices = np.dot(vertices,
                      self.structure.lattice.matrix)  # transform to cartesian
    pos = [vert for triangle in vertices[faces].tolist() for vert in triangle]
    return Scene("isosurface",
                 origin=origin,
                 contents=[
                     Surface(pos,
                             show_edges=False,
                             **kwargs)
                 ])


# TODO: re-think origin, shift globally at end (scene.origin)
def get_volumetric_scene(self,
                         data_key='total',
                         isolvl=0.5,
                         step_size=3,
                         iso_kwargs_dict=None,
                         **struct_kwargs):
    """Get the Scene object which contains a structure and a isosurface components

    Args:
        data_key (str, optional): Use the volumetric data from self.data[data_key]. Defaults to 'total'.
        isolvl (float, optional): The cuoff for the isosurface to using the same units as VESTA so e/bhor and kept grid size independent
        step_size (int, optional): step_size parameter for marching_cubes_lewiner. Defaults to 3.
        iso_kwargs_dict ([type], optional): additional kwargs to pass to the get_isosurface_scene. Defaults to None.
        struct_kwargs: kwarges for the Structure.get_scene function

    Returns:
        [type]: [description]
    """

    iso_kwags = iso_kwargs_dict or {}
    struct_scene = self.structure.get_scene(**struct_kwargs)
    iso_scene = self.get_isosurface_scene(data_key='total',
                                          isolvl=isolvl,
                                          step_size=step_size,
                                          origin=struct_scene.origin,
                                          **iso_kwags)
    return Scene(name=self.structure.composition.reduced_formula,
                 origin=struct_scene.origin,
                 contents=[struct_scene, iso_scene])


# todo: re-think origin, shift globally at end (scene.origin)
VolumetricData.get_isosurface_scene = get_isosurface_scene
VolumetricData.get_scene = get_volumetric_scene
