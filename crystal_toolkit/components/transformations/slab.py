import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.helpers.layouts import Label
from crystal_toolkit.components.transformations.core import TransformationComponent

from pymatgen.transformations.advanced_transformations import SlabTransformation


class SlabTransformationComponent(TransformationComponent):

    @property
    def title(self):
        return "Make a slab"

    @property
    def description(self):
        return """Create a slab from a structure, where a "slab" is a crystal 
surface that is still periodic in all three dimensions but has a large artificial
vacuum inserted so that the properties of the crystal surface can be studied.
"""

    @property
    def transformation(self):
        return SlabTransformation

    @property
    def options_layout(self):

        def _m(element, value=0):
            return dcc.Input(id=self.id(f"m{element}"), inputmode="numeric",
                             min=0, max=9, step=1, size=1, className="input",
                             maxlength=1,
                             style={"text-align": "center", "width": "1rem",
                                    "margin-right": "0.2rem", "margin-bottom": "0.2rem"},
                             value=value)

        miller_index = html.Div([
            html.Div([_m(1, value=1), _m(2), _m(3)])
        ])

        min_slab_size = dcc.Input(id=self.id("min_slab_size"), value=6)
        min_vacuum_size = dcc.Input(id=self.id("min_vacuum_size"), value=10)

        options = html.Div([Label("Miller index:"), miller_index,
                            Label("Min slab size:"), min_slab_size,
                            Label("Min vacuum size:"), min_vacuum_size])

        return options

    def _generate_callbacks(self, app, cache):

        super()._generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("transformation_args_kwargs"), "data"),
            [Input(self.id(f"m{e}"), "value") for e in range(1,4)]
            + [Input(self.id("min_slab_size"), "value"), Input(self.id("min_vacuum_size"), "value")]
        )
        def update_transformation_kwargs(m1, m2, m3, min_slab_size, min_vacuum_size):

            miller_index = list(map(int, [m1, m2, m3]))
            min_slab_size = float(min_slab_size)
            min_vacuum_size = float(min_vacuum_size)

            return {'args': [miller_index, min_slab_size, min_vacuum_size], 'kwargs': {}}
