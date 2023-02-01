from __future__ import annotations

from pymatgen.transformations.advanced_transformations import (
    MonteCarloRattleTransformation,
)

from crystal_toolkit.components.transformations.core import TransformationComponent


class MonteCarloRattleTransformationComponent(TransformationComponent):
    @property
    def title(self) -> str:
        return "Rattle a supercell"

    @property
    def description(self) -> str:
        return """Uses a Monte Carlo rattle procedure to randomly perturb the sites in a
    structure using the [hiPhive](https://hiphive.materialsmodeling.org) code.

Rattling atom \\` i \\` is carried out as a Monte Carlo move that is accepted with
a probability determined from the minimum interatomic distance
\\` d\\_{ij} \\`.  If \\` \\\\min(d\\_{ij}) \\` is smaller than \\` d\\_{min} \\`
the move is only accepted with a low probability.

This process is repeated for each atom a number of times meaning
the magnitude of the final displacements is not *directly*
connected to the rattle amplitude.
"""

    @property
    def transformation(self):
        return MonteCarloRattleTransformation

    def options_layouts(self, state=None, structure=None):
        state = state or {
            "rattle_std": 0.2,
            "min_distance": 0.1,
            "seed": None,
        }

        rattle_std = self.get_numerical_input(
            label="Rattle amplitude",
            kwarg_label="rattle_std",
            state=state,
            help_str="""Rattle amplitude (standard deviation in normal distribution).
Note: this value is not *directly* connected to the
final average displacement for the structures""",
            shape=(),
        )

        min_distance = self.get_numerical_input(
            label="Minimum distance /Å",
            kwarg_label="min_distance",
            state=state,
            help_str="""Interatomic distance used for computing the probability
for each rattle move.""",
            shape=(),
        )

        seed = self.get_numerical_input(
            label="Random seed",
            kwarg_label="seed",
            state=state,
            help_str="""Seed for setting up NumPy random state from which random numbers
are generated. If not set, a random seed will be generated
(default). This option allows the output of this transformation
to be deterministic.""",
            shape=(),
            is_int=True,
        )

        return rattle_std, min_distance, seed
