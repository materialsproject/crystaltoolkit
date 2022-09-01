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

    def options_layouts(self, state=None, structure=None):

        state = state or {
            "miller_index": (0, 0, 1),
            "min_slab_size": 4,
            "min_vacuum_size": 10,
            "lll_reduce": True,
            "center_slab": True,
            "in_unit_planes": False,
            "primitive": True,
            "max_normal_search": None,
            "shift": 0,
            "tol": 0.1,
        }

        miller_index = self.get_numerical_input(
            label="Miller index",
            kwarg_label="miller_index",
            state=state,
            help_str="The surface plane defined by its Miller index (h, k, l)",
            shape=(3,),
        )

        min_slab_size = self.get_numerical_input(
            label="Minimum slab size /Å",
            kwarg_label="min_slab_size",
            state=state,
            help_str="Minimum slab size in Ångstroms (or number of planes of atoms if "
            '"Use plane units" enabled)',
            shape=(3,),
        )

        min_vacuum_size = self.get_numerical_input(
            label="Minimum vacuum size /Å",
            kwarg_label="min_vacuum_size",
            state=state,
            help_str="Minimum vacuum size in Ångstroms (or number of planes of atoms if "
            '"Use plane units" enabled)',
            shape=(),
        )

        lll_reduce = self.get_bool_input(
            label="Enable LLL reduction",
            kwarg_label="lll_reduce",
            state=state,
            help_str="Whether or not to apply an LLL lattice reduction",
        )

        in_unit_planes = self.get_bool_input(
            label="Use Plane Units",
            kwarg_label="in_unit_planes",
            state=state,
            help_str="Change units of vacuum size and slab size to be in terms of "
            "number of planes of atoms instead of Ångstroms.",
        )

        primitive = self.get_bool_input(
            label="Make primitive",
            kwarg_label="primitive",
            state=state,
            help_str="Reduce the slab to most primitive cell.",
        )

        max_normal_search = self.get_numerical_input(
            "max_normal_search",
            state=state,
            label="Maximum normal search index",
            help_str="Maximum index to include in linear combinations of indices "
            "to find **c** lattice vector orthogonal to slab surface.",
            is_int=True,
        )

        shift = self.get_numerical_input(
            label="Shift /Å",
            kwarg_label="shift",
            state=state,
            help_str="Shift to change termination.",
            shape=(),
        )

        tol = self.get_numerical_input(
            label="Tolerance",
            kwarg_label="tol",
            state=state,
            help_str="Tolerance to find primitive cell.",
            shape=(),
        )

        options = html.Div(
            [
                miller_index,
                min_slab_size,
                min_vacuum_size,
                lll_reduce,
                in_unit_planes,
                primitive,
                max_normal_search,
                shift,
                tol,
            ]
        )

        return options
