import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.helpers.layouts import Label
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

    @property
    def options_layout(self):

        def _m(element, value=0):
            return dcc.Input(id=self.id(f"m{element}"), inputmode="numeric",
                             min=0, max=9, step=1, size=1, className="input",
                             maxlength=1,
                             style={"text-align": "center", "width": "1rem",
                                    "margin-right": "0.2rem", "margin-bottom": "0.2rem"},
                             value=value)

        scaling_matrix = html.Div([
            html.Div([_m(11, value=1), _m(12), _m(13)]),
            html.Div([_m(21), _m(22, value=1), _m(23)]),
            html.Div([_m(31), _m(32), _m(33, value=1)])
        ])

        options = html.Div([Label("Scaling matrix:"), scaling_matrix])

        return options

    def _generate_callbacks(self, app, cache):

        super()._generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("transformation_args_kwargs"), "data"),
            [Input(self.id(f"m{e1}{e2}"), "value") for e1 in range(1,4) for e2 in range(1,4)]
        )
        def update_transformation_kwargs(*args):

            scaling_matrix = [args[0:3], args[3:6], args[6:9]]

            return {'args': [], 'kwargs': {'scaling_matrix': scaling_matrix}}
