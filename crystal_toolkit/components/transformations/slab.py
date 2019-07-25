import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.helpers.layouts import Label
from crystal_toolkit.helpers.inputs import *
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

    def options_layout(self, inital_args_kwargs):

        miller_index = get_matrix_input(
            self.id(),
            label="Miller index",
            default=((1, 0, 0),),
            help="The surface plane defined by its Miller index (h, k, l)",
        )

        min_slab_size = dcc.Input(id=self.id("min_slab_size"), value=6)
        min_vacuum_size = dcc.Input(id=self.id("min_vacuum_size"), value=10)
        lll_reduce = dcc.Checklist(
            id=self.id("lll_reduce"),
            options=[{"label": " ", "value": "lll_reduce"}],
            value=["lll_reduce"],
        )
        center_slab = dcc.Checklist(
            id=self.id("center_slab"),
            options=[{"label": " ", "value": "center_slab"}],
            value=["center_slab"],
        )
        # in_unit_planes = ...
        # primitive = ...
        # max_normal_search = ...
        # shift = ...
        # tol = ...

        # get_layout(name, display_name, type)
        # get_inputs(name, type)
        # get_value(type, inputs)

        options = html.Div(
            [
                miller_index,
                Label("Min slab size:"),
                min_slab_size,
                Label("Min vacuum size:"),
                min_vacuum_size,
                Label("Center slab:"),
                center_slab,
                Label("Reduce slab (LLL):"),
                lll_reduce,
            ]
        )

        return options

    def generate_callbacks(self, app, cache):

        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("transformation_args_kwargs"), "data"),
            [Input(self.id(f"m0{e}"), "value") for e in range(3)]
            + [
                Input(self.id("min_slab_size"), "value"),
                Input(self.id("min_vacuum_size"), "value"),
                Input(self.id("center_slab"), "value"),
                Input(self.id("lll_reduce"), "value"),
            ],
        )
        def update_transformation_kwargs(
            m1, m2, m3, min_slab_size, min_vacuum_size, center_slab, lll_reduce
        ):

            miller_index = list(map(int, [m1, m2, m3]))
            min_slab_size = float(min_slab_size)
            min_vacuum_size = float(min_vacuum_size)
            center_slab = "center_slab" in center_slab
            lll_reduce = "lll_reduce" in lll_reduce

            return {
                "args": [miller_index, min_slab_size, min_vacuum_size],
                "kwargs": {"center_slab": center_slab, "lll_reduce": lll_reduce},
            }
