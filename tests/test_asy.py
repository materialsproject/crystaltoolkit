from pymatgen import Structure, Lattice
from crystal_toolkit.helpers.asymptote_export import write_asy_file
from crystal_toolkit.components.structure import StructureMoleculeComponent
import os

example_struct = Structure.from_spacegroup(
    "P6_3mc",
    Lattice.hexagonal(3.22, 5.24),
    ["Ga", "N"],
    [[1 / 3, 2 / 3, 0], [1 / 3, 2 / 3, 3 / 8]],
)

smc = StructureMoleculeComponent(example_struct, hide_incomplete_bonds=True)
file_name = "./asy_test/test_fig.asy"
write_asy_file(smc, file_name)
