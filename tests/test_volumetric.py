import pytest
from pymatgen.io.vasp import Chgcar


def test_volumetric(test_files):
    chgcar = Chgcar.from_file(test_files / "chgcar.vasp")
    max_val = chgcar.data["total"].max()

    scene = chgcar.get_scene(isolvl=10, normalization=None)
    assert scene is not None

    # out of range
    with pytest.raises(ValueError, match="Isosurface level is not within data range"):
        scene = chgcar.get_scene(isolvl=max_val * 2, normalization=None)

    # cannot be computed
    with pytest.raises(RuntimeError):
        scene = chgcar.get_scene(isolvl=max_val / 2, normalization=None)

    # vesta units
    scene = chgcar.get_scene(isolvl=0.001, normalization="vesta")
