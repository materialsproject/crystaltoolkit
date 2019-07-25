import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from ast import literal_eval

from crystal_toolkit.helpers.layouts import Label
from crystal_toolkit.components.transformations.core import TransformationComponent

from pymatgen.transformations.advanced_transformations import (
    GrainBoundaryTransformation,
    GrainBoundaryGenerator,
)

import json


class GrainBoundaryTransformationComponent(TransformationComponent):
    @property
    def title(self):
        return "Make a grain boundary"

    @property
    def description(self):
        return """Create a grain boundary within a periodic supercell from a 
        body-centered cubic or face-centered cubic crystal structure."""

    @property
    def transformation(self):
        return GrainBoundaryTransformation

    @property
    def default_transformation(self):
        return self.transformation([1, 0, 0], 0)

    def options_layout(self, inital_args_kwargs):

        options = html.Div(
            [
                html.Div(
                    [
                        Label("Rotation axis"),
                        dcc.Input(
                            value="[1, 0, 0]",
                            id=self.id("gb_rotation_axis"),
                            type="text",
                            className="input",
                        ),
                    ]
                ),
                html.Br(),
                html.Div(
                    [
                        Label("Choose Σ"),
                        dcc.Dropdown(
                            id=self.id("gb_sigma_options"),
                            options=[],
                            placeholder="...",
                        ),
                    ]
                ),
                html.Br(),
                html.Div(
                    [
                        Label("Choose rotation angle"),
                        dcc.Dropdown(
                            id=self.id("gb_rotation_options"),
                            options=[],
                            placeholder="...",
                        ),
                    ]
                ),
                html.Br(),
                html.Div(
                    [
                        Label("Grain width"),
                        dcc.Slider(
                            id=self.id("gb_expand_times"),
                            min=1,
                            max=6,
                            step=1,
                            value=2,
                            marks={2: "2", 4: "4", 6: "6"},
                        ),
                    ]
                ),
                html.Br(),
                html.Div(
                    [
                        Label("Distance between grains in Å"),
                        dcc.Input(
                            value="0.0",
                            id=self.id("gb_vacuum_thickness"),
                            type="text",
                            className="input",
                        ),
                    ]
                ),
                html.Br(),
                html.Div(
                    [
                        Label("Plane"),
                        dcc.Input(
                            value="None",
                            id=self.id("gb_plane"),
                            type="text",
                            className="input",
                        ),
                    ]
                ),
            ]
        )

        return options

    def generate_callbacks(self, app, cache):

        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("transformation_args_kwargs"), "data"),
            [
                Input(self.id("gb_rotation_axis"), "value"),
                Input(self.id("gb_rotation_options"), "value"),
                Input(self.id("gb_vacuum_thickness"), "value"),
                Input(self.id("gb_expand_times"), "value"),
            ],
        )
        def update_transformation_kwargs(
            rotation_axis, rotation_angle, vacuum_thickness, expand_times
        ):

            rotation_angle = float(rotation_angle)
            rotation_axis = literal_eval(rotation_axis)
            vacuum_thickness = float(vacuum_thickness)
            expand_times = float(expand_times)

            return {
                "args": [rotation_axis, rotation_angle],
                "kwargs": {
                    "vacuum_thickness": vacuum_thickness,
                    "expand_times": expand_times,
                },
            }

        @app.callback(
            Output(self.id("gb_sigma_options"), "options"),
            [Input(self.id("gb_rotation_axis"), "value")],
            [State(self.id("gb_sigma_options"), "options")],
        )
        def calculate_sigma(rotation_axis, current_options):
            try:
                rotation_axis = json.loads(rotation_axis)
            except:
                return current_options
            else:
                sigmas = GrainBoundaryGenerator.enum_sigma_cubic(100, rotation_axis)
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

                return options

        @app.callback(
            Output(self.id("gb_rotation_options"), "options"),
            [
                Input(self.id("gb_rotation_axis"), "value"),
                Input(self.id("gb_sigma_options"), "value"),
            ],
            [State(self.id("gb_rotation_options"), "options")],
        )
        def calculate_sigma(rotation_axis, sigma, current_options):
            try:
                rotation_axis = json.loads(rotation_axis)
                sigma = int(sigma)
            except:
                return current_options
            else:
                sigmas = GrainBoundaryGenerator.enum_sigma_cubic(100, rotation_axis)
                rotation_angles = sigmas[sigma]
                options = []
                for rotation_angle in sorted(rotation_angles):
                    options.append(
                        {
                            "label": "{:.2f}º".format(rotation_angle),
                            "value": rotation_angle,
                        }
                    )

                return options

        @app.callback(
            Output(self.id("gb_sigma_options"), "value"),
            [Input(self.id("gb_sigma_options"), "options")],
            [State(self.id("gb_sigma_options"), "value")],
        )
        def update_default_value(options, current_value):
            if len(options) > 0:
                return options[0]["value"]
            else:
                return current_value

        @app.callback(
            Output(self.id("gb_rotation_options"), "value"),
            [Input(self.id("gb_rotation_options"), "options")],
            [State(self.id("gb_rotation_options"), "value")],
        )
        def update_default_value(options, current_value):
            if len(options) > 0:
                return options[0]["value"]
            else:
                return current_value
