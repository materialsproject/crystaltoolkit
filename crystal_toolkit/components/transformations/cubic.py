import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from crystal_toolkit.helpers.layouts import Label
from crystal_toolkit.components.transformations.core import TransformationComponent

from pymatgen.transformations.advanced_transformations import (
    CubicSupercellTransformation,
)


class CubicTransformationComponent(TransformationComponent):
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

    def options_layout(self, inital_args_kwargs):
        return html.Div()

    def generate_callbacks(self, app, cache):
        super().generate_callbacks(app, cache)

        # TODO: this is a bug, should be removed
        @app.callback(
            Output(self.id("transformation_args_kwargs"), "data"),
            [Input(self.id("doesntexist"), "value")],
        )
        def update_transformation_kwargs(*args):
            return {"args": [], "kwargs": {}}
