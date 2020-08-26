import numpy as np
from pymatgen.io.vasp import VolumetricData
from skimage import measure

from crystal_toolkit.core.scene import Scene, Surface

_ANGS2_TO_BOHR3 = 1.88973 ** 3


def get_isosurface_scene(
    self, data_key="total", isolvl=0.05, step_size=4, origin=None, **kwargs
):
    """Get the isosurface from a VolumetricData object

    Args:
        data_key (str, optional): Use the volumetric data from self.data[data_key]. Defaults to 'total'.
        isolvl (float, optional): The cutoff for the isosurface to using the same units as VESTA so
        e/bhor and kept grid size independent
        step_size (int, optional): step_size parameter for marching_cubes_lewiner. Defaults to 3.

    Returns:
        [type]: [description]
    """
    origin = origin or list(
        -self.structure.lattice.get_cartesian_coords([0.5, 0.5, 0.5])
    )
    vol_data = np.copy(self.data[data_key])
    vol = self.structure.volume
    vol_data = vol_data / vol / _ANGS2_TO_BOHR3

    padded_data = np.pad(vol_data, (0, 1), "wrap")
    vertices, faces, normals, values = measure.marching_cubes_lewiner(
        padded_data, level=isolvl, step_size=step_size
    )
    # transform to fractional coordinates
    vertices = vertices / (vol_data.shape[0], vol_data.shape[1], vol_data.shape[2])
    vertices = np.dot(vertices, self.structure.lattice.matrix)  # transform to cartesian
    pos = [vert for triangle in vertices[faces].tolist() for vert in triangle]
    return Scene(
        "isosurface", origin=origin, contents=[Surface(pos, show_edges=False, **kwargs)]
    )


def get_volumetric_scene(self, data_key="total", isolvl=0.5, step_size=3, **kwargs):
    """Get the Scene object which contains a structure and a isosurface components

    Args:
        data_key (str, optional): Use the volumetric data from self.data[data_key]. Defaults to 'total'.
        isolvl (float, optional): The cuoff for the isosurface to using the same units as VESTA so e/bhor
        and kept grid size independent
        step_size (int, optional): step_size parameter for marching_cubes_lewiner. Defaults to 3.
        **kwargs: kwargs for the Structure.get_scene function

    Returns:
        [type]: [description]
    """

    struct_scene = self.structure.get_scene(**kwargs)
    iso_scene = self.get_isosurface_scene(
        data_key=data_key,
        isolvl=isolvl,
        step_size=step_size,
        origin=struct_scene.origin,
    )
    struct_scene.contents.append(iso_scene)
    return struct_scene


# todo: re-think origin, shift globally at end (scene.origin)
VolumetricData.get_isosurface_scene = get_isosurface_scene
VolumetricData.get_scene = get_volumetric_scene
