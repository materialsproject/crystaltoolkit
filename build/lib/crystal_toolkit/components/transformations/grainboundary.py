import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.transformations.advanced_transformations import (
    GrainBoundaryGenerator,
    GrainBoundaryTransformation,
)

from crystal_toolkit.components.transformations.core import TransformationComponent
from crystal_toolkit.helpers.layouts import add_label_help


class GrainBoundaryTransformationComponent(TransformationComponent):
    @property
    def title(self):
        return "Make a grain boundary"

    @property
    def description(self):
        return """Create a grain boundary within a periodic supercell. This transformation 
requires sensible inputs, and will be slow to run in certain cases.

When using this transformation a new site property is added which can be used 
to colour-code the top and bottom grains."""

    @property
    def transformation(self):
        return GrainBoundaryTransformation

    def options_layouts(self, state=None, structure=None):

        state = state or {
            "rotation_axis": [0, 0, 1],
            "rotation_angle": None,
            "expand_times": 2,
            "vacuum_thickness": 0,
            "ab_shift": [0, 0],
            "normal": False,
            "ratio": None,
            "plane": None,
            "max_search": 20,
            "tol_coi": 1e-8,
            "rm_ratio": 0.7,
            "quick_gen": False,
        }

        rotation_axis = self.get_numerical_input(
            label="Rotation axis",
            kwarg_label="rotation_axis",
            state=state,
            help_str="""Maximum number of atoms allowed in the supercell.""",
            shape=(3,),
        )

        rotation_angle = self.get_choice_input(
            label="Rotation angle",
            kwarg_label="rotation_angle",
            state=state,
            help_str="""Rotation angle to generate grain boundary. Options determined by 
            your choice of Σ.""",
        )

        # sigma isn't a direct input into the transformation, but has
        # to be calculated from the rotation_axis and structure
        _, sigma_options, _ = self._get_sigmas_options_and_ratio(
            structure, state.get("rotation_axis")
        )
        sigma = dcc.Dropdown(
            id=self.id("sigma"),
            style={"width": "5rem"},
            options=sigma_options,
            value=sigma_options[0]["value"] if sigma_options else None,
        )
        sigma = add_label_help(
            sigma,
            "Sigma",
            "The unit cell volume of the coincidence site lattice relative to "
            "input unit cell is denoted by sigma.",
        )

        expand_times = self.get_numerical_input(
            label="Expand times",
            kwarg_label="expand_times",
            state=state,
            help_str="""The multiple number of times to expand one unit grain into a larger grain. This is 
            useful to avoid self-interaction issues when using the grain boundary as an input to further simulations.""",
            is_int=True,
            shape=(),
            min=1,
            max=6,
        )

        vacuum_thickness = self.get_numerical_input(
            label="Vacuum thickness /Å",
            kwarg_label="vacuum_thickness",
            state=state,
            help_str="""The thickness of vacuum that you want to insert between the two grains.""",
            shape=(),
        )

        ab_shift = self.get_numerical_input(
            label="In-plane shift",
            kwarg_label="ab_shift",
            state=state,
            help_str="""In-plane shift of the two grains given in units of the **a** 
            and **b** vectors of the grain boundary.""",
            shape=(2,),
        )

        normal = self.get_bool_input(
            label="Set normal direction",
            kwarg_label="normal",
            state=state,
            help_str="Enable to require the **c** axis of the top grain to be perpendicular to the surface.",
        )

        plane = self.get_numerical_input(
            label="Grain boundary plane",
            kwarg_label="plane",
            state=state,
            help_str="""Grain boundary plane in the form of a list of integers. 
            If not set, grain boundary will be a twist grain boundary. 
            The plane will be perpendicular to the rotation axis.""",
            shape=(3,),
        )

        tol_coi = self.get_numerical_input(
            label="Coincidence Site Tolerance",
            kwarg_label="tol_coi",
            state=state,
            help_str="""Tolerance to find the coincidence sites. To check the number of coincidence
                sites are correct or not, you can compare the generated grain boundary's sigma with 
                expected number.""",
            shape=(),
        )

        rm_ratio = self.get_numerical_input(
            label="Site Merging Tolerance",
            kwarg_label="rm_ratio",
            state=state,
            help_str="""The criteria to remove the atoms which are too close with each other relative to 
            the bond length in the bulk system.""",
            shape=(),
        )

        return [
            rotation_axis,
            sigma,
            rotation_angle,
            expand_times,
            vacuum_thickness,
            ab_shift,
            normal,
            plane,
            tol_coi,
            rm_ratio,
        ]

    @staticmethod
    def _get_sigmas_options_and_ratio(structure, rotation_axis):

        rotation_axis = [int(i) for i in rotation_axis]

        lat_type = (
            "c"  # assume cubic if no structure specified, just to set initial choices
        )
        ratio = None
        if structure:
            sga = SpacegroupAnalyzer(structure)
            lat_type = sga.get_lattice_type()[0]  # this should be fixed in pymatgen
            try:
                ratio = GrainBoundaryGenerator(structure).get_ratio()
            except Exception:
                ratio = None

        cutoff = 10

        if lat_type.lower() == "c":
            sigmas = GrainBoundaryGenerator.enum_sigma_cubic(
                cutoff=cutoff, r_axis=rotation_axis
            )
        elif lat_type.lower() == "t":
            sigmas = GrainBoundaryGenerator.enum_sigma_tet(
                cutoff=cutoff, r_axis=rotation_axis, c2_a2_ratio=ratio
            )
        elif lat_type.lower() == "o":
            sigmas = GrainBoundaryGenerator.enum_sigma_ort(
                cutoff=cutoff, r_axis=rotation_axis, c2_b2_a2_ratio=ratio
            )
        elif lat_type.lower() == "h":
            sigmas = GrainBoundaryGenerator.enum_sigma_hex(
                cutoff=cutoff, r_axis=rotation_axis, c2_a2_ratio=ratio
            )
        elif lat_type.lower() == "r":
            sigmas = GrainBoundaryGenerator.enum_sigma_rho(
                cutoff=cutoff, r_axis=rotation_axis, ratio_alpha=ratio
            )
        else:
            return [], None

        options = []
        subscript_unicode_map = {
            0: "₀",
            1: "₁",
            2: "₂",
            3: "₃",
            4: "₄",
            5: "₅",
            6: "₆",
            7: "₇",
            8: "₈",
            9: "₉",
        }
        for sigma in sorted(sigmas.keys()):
            sigma_label = "Σ{}".format(sigma)
            for k, v in subscript_unicode_map.items():
                sigma_label = sigma_label.replace(str(k), v)
            options.append({"label": sigma_label, "value": sigma})

        return sigmas, options, ratio

    def generate_callbacks(self, app, cache):

        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("sigma"), "options"),
            [Input(self.get_kwarg_id("rotation_axis"), "value")],
            [State(self.id("input_structure"), "data")],
        )
        def update_sigma_options(rotation_axis, structure):

            rotation_axis = self.reconstruct_kwarg_from_state(
                dash.callback_context.inputs, "rotation_axis"
            )
            if (rotation_axis is None) or (not structure):
                raise PreventUpdate
            structure = self.from_data(structure)

            _, sigma_options, _ = self._get_sigmas_options_and_ratio(
                structure=structure, rotation_axis=rotation_axis
            )

            # TODO: add some sort of error handling here when sigmas is empty

            return sigma_options

        @app.callback(
            Output(self.id("rotation_angle", is_kwarg=True), "options"),
            [
                Input(self.id("sigma"), "value"),
                Input(self.get_kwarg_id("rotation_axis"), "value"),
            ],
            [State(self.id("input_structure"), "data")],
        )
        def update_rotation_angle_options(sigma, rotation_axis, structure):

            if not sigma:
                raise PreventUpdate

            rotation_axis = self.reconstruct_kwarg_from_state(
                dash.callback_context.inputs, "rotation_axis"
            )

            if (rotation_axis is None) or (not structure):
                raise PreventUpdate
            structure = self.from_data(structure)

            sigmas, _, _ = self._get_sigmas_options_and_ratio(
                structure=structure, rotation_axis=rotation_axis
            )

            rotation_angles = sigmas[sigma]
            options = []
            for rotation_angle in sorted(rotation_angles):
                options.append(
                    {"label": "{:.2f}º".format(rotation_angle), "value": rotation_angle}
                )

            return options

        # TODO: make client-side callback
        @app.callback(
            [Output(self.id("sigma"), "value"), Output(self.id("sigma"), "disabled")],
            [
                Input(self.id("sigma"), "options"),
                Input(self.id("enable_transformation"), "on"),
            ],
        )
        def update_default_value(options, enabled):
            if options is None:
                raise PreventUpdate
            return options[0]["value"], enabled

        # TODO: make client-side callback, or just combine all callbacks here
        @app.callback(
            Output(self.id("rotation_angle", is_kwarg=True), "value"),
            [Input(self.id("rotation_angle", is_kwarg=True), "options")],
        )
        def update_default_value(options):
            if options is None:
                raise PreventUpdate
            return options[0]["value"]
