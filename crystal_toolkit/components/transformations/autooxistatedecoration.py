from crystal_toolkit.components.transformations.core import TransformationComponent

from pymatgen.transformations.standard_transformations import (
    AutoOxiStateDecorationTransformation,
)


class AutoOxiStateDecorationTransformationComponent(TransformationComponent):
    @property
    def title(self):
        return "Detect likely oxidation states"

    @property
    def description(self):
        return """Annotate the crystal structure with likely oxidation states 
using a bond valence approach. This transformation can fail if it cannot find 
a satisfactory combination of oxidation states, and might be slow for large 
structures. 
"""

    @property
    def transformation(self):
        return AutoOxiStateDecorationTransformation
