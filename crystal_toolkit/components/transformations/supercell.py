import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.helpers.layouts import Label
from crystal_toolkit.helpers.inputs import *
from crystal_toolkit.components.transformations.core import TransformationComponent
from crystal_toolkit import Simple3DSceneComponent

from crystal_toolkit.core.scene import Scene

from pymatgen.transformations.standard_transformations import SupercellTransformation


class SupercellTransformationComponent(TransformationComponent):
    @property
    def title(self):
        return "Make a supercell"

    @property
    def description(self):
        return """Create a supercell by providing a scaling matrix that transforms
input lattice vectors a, b and c into transformed lattice vectors a', b' and c'.
For example, to create a supercell with lattice vectors a'=2a, b'=2b, c'=2c enter a 
scaling matrix [[2, 0, 0], [0, 2, 0], [0, 0, 2]] or to create a supercell with 
lattice vectors a' = 2a+b, b' = 3b and c' = c enter a scaling matrix 
[[2, 1, 0], [0, 3, 0], [0, 0, 1]]. All elements of the scaling matrix must be 
integers.
"""

    @property
    def transformation(self):
        return SupercellTransformation

    def options_layout(self, state=None, stucture=None):

        state = state or {"scaling_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1))}

        options = get_matrix_input(
            self, label="Scaling matrix", kwarg_label="scaling_matrix", state=state
        )

        return options
