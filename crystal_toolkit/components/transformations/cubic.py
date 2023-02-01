from __future__ import annotations

from pymatgen.transformations.advanced_transformations import (
    CubicSupercellTransformation,
)

from crystal_toolkit.components.transformations.core import TransformationComponent


class CubicSupercellTransformationComponent(TransformationComponent):
    @property
    def title(self) -> str:
        return "Make nearly cubic supercell"

    @property
    def description(self) -> str:
        return """A transformation that aims to generate a nearly cubic supercell structure
from a structure.

The algorithm solves for a transformation matrix that makes the supercell
cubic. The matrix must have integer entries, so entries are rounded in such
a way that forces the matrix to be nonsingular. From the supercell
resulting from this transformation matrix, vector projections are used to
determine the side length of the largest cube that can fit inside the
supercell. The algorithm will iteratively increase the size of the supercell
until the largest inscribed cube's side length is at least the minimum length
and the number of atoms in the supercell falls in the range specified.
        """

    @property
    def transformation(self):
        return CubicSupercellTransformation

    def options_layouts(self, state=None, structure=None):
        state = state or {
            "max_atoms": 100,
            "min_atoms": len(structure) if structure else 50,
            "min_length": 10,
            "force_diagonal": False,
        }

        max_atoms = self.get_numerical_input(
            label="Maximum number of atoms",
            kwarg_label="max_atoms",
            state=state,
            help_str="""Maximum number of atoms allowed in the supercell.""",
            shape=(),
        )

        min_atoms = self.get_numerical_input(
            label="Minimum number of atoms",
            kwarg_label="min_atoms",
            state=state,
            help_str="""Minimum number of atoms allowed in the supercell.""",
            shape=(),
        )

        min_length = self.get_numerical_input(
            label="Minimum length /Å",
            kwarg_label="min_length",
            state=state,
            help_str="""Minimum length of the smallest supercell lattice vector.""",
            shape=(),
        )

        force_diagonal = self.get_bool_input(
            label="Force diagonal",
            kwarg_label="force_diagonal",
            state=state,
            help_str="""If enabled, return a transformation with a diagonal transformation matrix.""",
        )

        return max_atoms, min_atoms, min_length, force_diagonal
