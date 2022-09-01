from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure

from crystal_toolkit.components.structure import StructureMoleculeComponent
from crystal_toolkit.helpers.asymptote_renderer import write_asy_file

example_struct = Structure.from_spacegroup(
    "P6_3mc",
    Lattice.hexagonal(3.22, 5.24),
    ["Ga", "N"],
    [[1 / 3, 2 / 3, 0], [1 / 3, 2 / 3, 3 / 8]],
)

smc = StructureMoleculeComponent(example_struct, hide_incomplete_bonds=True)
file_name = "./asy_test/single/GaN.asy"
write_asy_file(smc, file_name)
write_asy_file(smc, "./asy_test/multi/GaN.asy")

example_struct = Structure.from_spacegroup(
    "P6_3mc",
    Lattice.hexagonal(3.22, 5.24),
    ["In", "N"],
    [[1 / 3, 2 / 3, 0], [1 / 3, 2 / 3, 3 / 8]],
)
smc = StructureMoleculeComponent(example_struct, hide_incomplete_bonds=True)
write_asy_file(smc, "./asy_test/multi/InN.asy")
example_struct = Structure.from_spacegroup(
    "P6_3mc",
    Lattice.hexagonal(3.22, 5.24),
    ["Al", "N"],
    [[1 / 3, 2 / 3, 0], [1 / 3, 2 / 3, 3 / 8]],
)
smc = StructureMoleculeComponent(example_struct, hide_incomplete_bonds=True)
write_asy_file(smc, "./asy_test/multi/AlN.asy")
