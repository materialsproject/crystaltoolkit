from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import skimage.measure
from pymatgen.io.vasp import VolumetricData

from crystal_toolkit.core.scene import Scene, Surface

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray
    from pymatgen.core.structure import Lattice

_ANGS2_TO_BOHR3 = 1.88973**3


def get_isosurface_scene(
    data: NDArray,
    lattice: Lattice,
    isolvl: float | None = None,
    step_size: int = 4,
    origin: ArrayLike | None = None,
    **kwargs: Any,
) -> Scene:
    """Get the isosurface from a VolumetricData object.

    Args:
        data (NDArray): The volumetric data array.
        lattice (Lattice): The lattice.
        isolvl (float, optional): The cutoff to compute the isosurface
        step_size (int, optional): step_size parameter for marching_cubes_lewiner. Defaults to 3.
        origin (ArrayLike, optional): The origin of the isosurface. Defaults to None.
        **kwargs: Passed to the Surface object.

    Returns:
        Scene: object containing the isosurface component
    """
    origin = origin or list(-lattice.get_cartesian_coords([0.5, 0.5, 0.5]))
    if isolvl is None:
        # get the value such that 20% of the weight is enclosed
        isolvl = np.percentile(data, 20)

    padded_data = np.pad(data, (0, 1), "wrap")
    try:
        vertices, faces, _, _ = skimage.measure.marching_cubes(
            padded_data, level=isolvl, step_size=step_size, method="lewiner"
        )
    except (ValueError, RuntimeError) as err:
        if "Surface level" in str(err):
            raise ValueError(
                f"Isosurface level is not within data range. min: {data.min()}, max: {data.max()}"
            ) from err
        raise err
    # transform to fractional coordinates
    vertices = vertices / (data.shape[0], data.shape[1], data.shape[2])
    vertices = np.dot(vertices, lattice.matrix)  # transform to Cartesian
    pos = [vert for triangle in vertices[faces].tolist() for vert in triangle]
    return Scene(
        "isosurface", origin=origin, contents=[Surface(pos, show_edges=False, **kwargs)]
    )


def get_volumetric_scene(
    self,
    data_key: str = "total",
    isolvl: float | None = None,
    step_size: int = 3,
    normalization: Literal["vol", "vesta"] | None = "vol",
    **kwargs,
):
    """Get the Scene object which contains a structure and a isosurface components.

    Args:
        data_key (str, optional): Use the volumetric data from self.data[data_key]. Defaults to 'total'.
        isolvl (float, optional): The cutoff for the isosurface if none is provided we default to
            a surface that encloses 20% of the weight.
        step_size (int, optional): step_size parameter for marching_cubes_lewiner. Defaults to 3.
        normalization (str, optional): Normalize the volumetric data by the volume of the unit cell.
            Default is 'vol', which divides the data by the volume of the unit cell, this is required
            for all VASP volumetric data formats.  If normalization is 'vesta' we also change
            the units from Angstroms to Bohr.
        **kwargs: Passed to the Structure.get_scene() function.

    Returns:
        Scene: object containing the structure and isosurface components
    """
    struct_scene = self.structure.get_scene(**kwargs)
    vol_data = self.data[data_key]
    if normalization in ("vol", "vesta"):
        vol_data = vol_data / self.structure.volume
    if normalization == "vesta":
        vol_data = vol_data / _ANGS2_TO_BOHR3

    iso_scene = get_isosurface_scene(
        data=vol_data,
        lattice=self.structure.lattice,
        isolvl=isolvl,
        step_size=step_size,
        origin=struct_scene.origin,
    )
    struct_scene.contents.append(iso_scene)
    return struct_scene


# todo: re-think origin, shift globally at end (scene.origin)
VolumetricData.get_scene = get_volumetric_scene
