from crystal_toolkit.components.transformations.core import TransformationComponent

from pymatgen.transformations.advanced_transformations import (
    MonteCarloRattleTransformation,
)


class MonteCarloRattleTransformationComponent(TransformationComponent):
    @property
    def title(self):
        return "Rattle a supercell"

    @property
    def description(self):
        return """...
"""

    @property
    def transformation(self):
        return MonteCarloRattleTransformation
