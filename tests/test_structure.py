import pytest
from pymatgen.core import Lattice, Molecule, Structure

from crystal_toolkit.components.structure import StructureMoleculeComponent

NaK = Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])

water = Molecule(["O", "H", "H"], [[0, 0, 0], [0.7, 0.7, 0], [-0.7, 0.7, 0]])


@pytest.mark.parametrize(
    ("structure", "expected"),
    [
        (NaK, "StructureMoleculeComponent(formula='K1 Na1', atoms=2)"),
        (water, "StructureMoleculeComponent(formula='H2 O1', atoms=3)"),
    ],
)
def test_repr_with_struct_or_mol(structure, expected):
    component = StructureMoleculeComponent(structure)
    assert repr(component) == expected
    assert str(component) == expected


def test_repr_without_structure():
    component = StructureMoleculeComponent()
    expected = "StructureMoleculeComponent(formula=None, atoms=None)"
    assert repr(component) == expected
    assert str(component) == expected
