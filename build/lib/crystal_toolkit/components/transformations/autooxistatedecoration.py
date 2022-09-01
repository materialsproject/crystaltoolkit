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

    def options_layouts(self, state=None, structure=None):

        state = state or {
            "symm_tol": 0.1,
            "max_radius": 4,
            "max_permutations": 10000,
            "distance_scale_factor": 1.015,
        }

        symm_tol = self.get_numerical_input(
            label="Symmetry tolerance",
            kwarg_label="symm_tol",
            state=state,
            help_str="""Symmetry tolerance used to determine which sites are 
            symmetrically equivalent. Set to 0 to turn off symmetry.""",
            shape=(),
        )

        max_radius = self.get_numerical_input(
            label="Maximum radius /Å",
            kwarg_label="max_radius",
            state=state,
            help_str="""Maximum radius in Ångstroms used to find nearest neighbors.""",
            shape=(),
        )

        max_permutations = self.get_numerical_input(
            label="Maximum number of permutations",
            kwarg_label="max_permutations",
            state=state,
            help_str="""Maximum number of permutations of oxidation states to test.""",
            shape=(),
        )

        distance_scale_factor = self.get_numerical_input(
            label="Distance scale factor",
            kwarg_label="distance_scale_factor",
            state=state,
            help_str="""A scale factor to be applied. This is 
            useful for scaling distances, esp in the case of 
            calculation-relaxed structures, which may tend to under (GGA) or 
            over bind (LDA). The default of 1.015 works for GGA. For 
            experimental structure, set this to 1.""",
            shape=(),
        )

        return [symm_tol, max_radius, max_permutations, distance_scale_factor]
