import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.helpers.layouts import Label
from crystal_toolkit.helpers.inputs import *
from crystal_toolkit.components.transformations.core import TransformationComponent

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

    def options_layout(self, state=None):

        state = state or {}

        options = get_matrix_input(
            self,
            label="Scaling matrix",
            for_arg_kwarg_label="scaling_matrix",
            state=state,
        )

        return options

    #
    # def generate_callbacks(self, app, cache):
    #
    #     super().generate_callbacks(app, cache)
    #
    #     print("option", self.option_ids)
    #
    #     app.clientside_callback(
    #         """
    #         function (m11, m12, m13, m21, m22, m23, m31, m32, m33) {
    #
    #             const scaling_matrix = [
    #                 [parseInt(m11), parseInt(m12), parseInt(m13)],
    #                 [parseInt(m21), parseInt(m22), parseInt(m23)],
    #                 [parseInt(m31), parseInt(m32), parseInt(m33)]
    #             ]
    #
    #             return {args: [], kwargs: {scaling_matrix: scaling_matrix}}
    #         }
    #         """,
    #         Output(self.id("transformation_args_kwargs"), "data"),
    #         [Input(option_id, "value") for option_id in self.option_ids],
    #     )
