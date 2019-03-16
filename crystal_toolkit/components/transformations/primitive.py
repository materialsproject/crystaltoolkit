import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.helpers.layouts import Label
from crystal_toolkit.components.transformations.core import TransformationComponent

from pymatgen.transformations.standard_transformations import PrimitiveCellTransformation


class PrimitiveCellTransformationComponent(TransformationComponent):

    @property
    def title(self):
        return "Convert crystal to a primitive setting"

    @property
    def description(self):
        return """Annotate the crystal structure with likely oxidation states 
using a bond valence approach. This transformation can fail if it cannot find 
a satisfactory combination of oxidation states, and might be slow for large 
structures. 
"""

    @property
    def transformation(self):
        return PrimitiveCellTransformation

    @property
    def options_layout(self):
        return html.Div()

    def _generate_callbacks(self, app, cache):
        super()._generate_callbacks(app, cache)


        # TODO: this is a bug, due to use of self.to_data and kwargs, this will be removed
        @app.callback(
            Output(self.id("transformation_args_kwargs"), "data"),
            [Input(self.id(f"m{e1}{e2}"), "value") for e1 in range(1,4) for e2 in range(1,4)]
        )
        def update_transformation_kwargs(*args):
            return {'args': [], 'kwargs': {}}
