from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from pymatgen.io.vasp import VolumetricData

from crystal_toolkit.core.scene import Scene, Surface

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

_ANGS2_TO_BOHR3 = 1.88973**3


def get_isosurface_scene(
    self,
    data_key: str = "total",
    isolvl: float = 0.05,
    step_size: int = 4,
    origin: ArrayLike | None = None,
    **kwargs: Any,
) -> Scene:
    """Get the isosurface from a VolumetricData object.

    Args:
        data_key (str, optional): Use the volumetric data from self.data[data_key]. Defaults to 'total'.
        isolvl (float, optional): The cutoff for the isosurface to using the same units as VESTA so
            e/bohr and kept grid size independent
        step_size (int, optional): step_size parameter for marching_cubes_lewiner. Defaults to 3.
        origin (ArrayLike, optional): The origin of the isosurface. Defaults to None.
        **kwargs: Passed to the Surface object.

    Returns:
        Scene: object containing the isosurface component
    """
    import skimage.measure

    origin = origin or list(
        -self.structure.lattice.get_cartesian_coords([0.5, 0.5, 0.5])
    )
    vol_data = np.copy(self.data[data_key])
    vol = self.structure.volume
    vol_data = vol_data / vol / _ANGS2_TO_BOHR3

    padded_data = np.pad(vol_data, (0, 1), "wrap")
    vertices, faces, normals, values = skimage.measure.marching_cubes(
        padded_data, level=isolvl, step_size=step_size, method="lewiner"
    )
    # transform to fractional coordinates
    vertices = vertices / (vol_data.shape[0], vol_data.shape[1], vol_data.shape[2])
    vertices = np.dot(vertices, self.structure.lattice.matrix)  # transform to Cartesian
    pos = [vert for triangle in vertices[faces].tolist() for vert in triangle]
    return Scene(
        "isosurface", origin=origin, contents=[Surface(pos, show_edges=False, **kwargs)]
    )


def get_volumetric_scene(self, data_key="total", isolvl=0.02, step_size=3, **kwargs):
    """Get the Scene object which contains a structure and a isosurface components.

    Args:
        data_key (str, optional): Use the volumetric data from self.data[data_key]. Defaults to 'total'.
        isolvl (float, optional): The cutoff for the isosurface to using the same units as VESTA so e/bhor
        and kept grid size independent
        step_size (int, optional): step_size parameter for marching_cubes_lewiner. Defaults to 3.
        **kwargs: Passed to the Structure.get_scene() function.

    Returns:
        Scene: object containing the structure and isosurface components
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
