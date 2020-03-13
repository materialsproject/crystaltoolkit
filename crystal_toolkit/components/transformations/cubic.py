from crystal_toolkit.components.transformations.core import TransformationComponent

from pymatgen.transformations.advanced_transformations import (
    CubicSupercellTransformation,
)


class CubicSupercellTransformationComponent(TransformationComponent):
    @property
    def title(self):
        return "Make nearly cubic supercell"

    @property
    def description(self):
        return """...
"""

    @property
    def transformation(self):
        return CubicSupercellTransformation
