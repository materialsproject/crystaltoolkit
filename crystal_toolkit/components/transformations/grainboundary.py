import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.helpers.layouts import Label
from crystal_toolkit.components.transformations.core import TransformationComponent

from pymatgen.transformations.advanced_transformations import (
    GrainBoundaryTransformation,
    GrainBoundaryGenerator,
)


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
    def options_layout(self):
        def _m(element, value=0):
            return dcc.Input(
                id=self.id(f"m{element}"),
                inputmode="numeric",
                min=0,
                max=9,
                step=1,
                size=1,
                className="input",
                maxlength=1,
                style={
                    "text-align": "center",
                    "width": "1rem",
                    "margin-right": "0.2rem",
                    "margin-bottom": "0.2rem",
                },
                value=value,
            )

        scaling_matrix = html.Div(
            [
                html.Div([_m(11, value=1), _m(12), _m(13)]),
                html.Div([_m(21), _m(22, value=1), _m(23)]),
                html.Div([_m(31), _m(32), _m(33, value=1)]),
            ]
        )

        options = html.Div([Label("Scaling matrix:"), scaling_matrix])

        # return options
        options = html.Div(
            [
                html.Div(
                    [
                        html.Label("Rotation axis"),
                        dcc.Input(
                            value="[1, 0, 0]",
                            id=self.id("gb_rotation_axis"),
                            type="text",
                            style={"width": "150px"},
                            className="input",
                        ),
                    ]
                ),
                html.Br(),
                html.Div(
                    [
                        html.Label("Choose Σ"),
                        dcc.Dropdown(
                            id=self.id("gb_sigma_options"),
                            options=[],
                            placeholder="...",
                        ),
                    ],
                    style={"width": "150px"},
                ),
                html.Br(),
                html.Div(
                    [
                        html.Label("Choose rotation angle"),
                        dcc.Dropdown(
                            id=self.id("gb_rotation_options"),
                            options=[],
                            placeholder="...",
                        ),
                    ],
                    style={"width": "150px"},
                ),
                html.Br(),
                html.Div(
                    [
                        html.Label("Grain width"),
                        dcc.Slider(
                            id=self.id("gb_expand_times"),
                            min=1,
                            max=6,
                            step=1,
                            value=2,
                            marks={2: "2", 4: "4", 6: "6"},
                        ),
                    ],
                    style={"width": "150px"},
                ),
                html.Br(),
                html.Div(
                    [
                        html.Label("Distance between grains in Å"),
                        dcc.Input(
                            value="0.0",
                            id=self.id("gb_vacuum_thickness"),
                            type="text",
                            style={"width": "150px"},
                            className="input",
                        ),
                    ]
                ),
                html.Br(),
                html.Div(
                    [
                        html.Label("Plane"),
                        dcc.Input(
                            value="None",
                            id=self.id("gb_plane"),
                            type="text",
                            style={"width": "150px"},
                            className="input",
                        ),
                    ]
                ),
            ]
        )

        return options

    def _generate_callbacks(self, app, cache):

        super()._generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("transformation_args_kwargs"), "data"),
            [
                Input(self.id(f"m{e1}{e2}"), "value")
                for e1 in range(1, 4)
                for e2 in range(1, 4)
            ],
        )
        def update_transformation_kwargs(*args):

            scaling_matrix = [args[0:3], args[3:6], args[6:9]]

            args = {"rotation_axis": None, "rotation_angle": None}

            kwargs = {
                "expand_times": 4,
                "vacuum_thickness": 0.0,
                "ab_shift": [0, 0],
                "normal": False,
                "plane": None,
                "max_search": 50,
                "tol_coi": 1e-3,
            }

            return {"args": list(args.values()), "kwargs": kwargs}


#    @app.callback(
#        Output(f"{structure_id_in}_gb_sigma_options", "options"),
#        [Input(f"{structure_id_in}_gb_rotation_axis", "value")],
#        [State(f"{structure_id_in}_gb_sigma_options", "options")],
#    )
#    def calculate_sigma(rotation_axis, current_options):
#        try:
#            rotation_axis = json.loads(rotation_axis)
#        except:
#            return current_options
#        else:
#            sigmas = GrainBoundaryGenerator.enum_sigma_cubic(100, rotation_axis)
#            options = []
#            subscript_unicode_map = {
#                0: "₀",
#                1: "₁",
#                2: "₂",
#                3: "₃",
#                4: "₄",
#                5: "₅",
#                6: "₆",
#                7: "₇",
#                8: "₈",
#                9: "₉",
#            }
#            for sigma in sorted(sigmas.keys()):
#                sigma_label = "Σ{}".format(sigma)
#                for k, v in subscript_unicode_map.items():
#                    sigma_label = sigma_label.replace(str(k), v)
#                options.append({"label": sigma_label, "value": sigma})
#
#            return options
#
#    @app.callback(
#        Output(f"{structure_id_in}_gb_rotation_options", "options"),
#        [
#            Input(f"{structure_id_in}_gb_rotation_axis", "value"),
#            Input(f"{structure_id_in}_gb_sigma_options", "value"),
#        ],
#        [State(f"{structure_id_in}_gb_rotation_options", "options")],
#    )
#    def calculate_sigma(rotation_axis, sigma, current_options):
#        try:
#            rotation_axis = json.loads(rotation_axis)
#            sigma = int(sigma)
#        except:
#            return current_options
#        else:
#            sigmas = GrainBoundaryGenerator.enum_sigma_cubic(100, rotation_axis)
#            rotation_angles = sigmas[sigma]
#            options = []
#            for rotation_angle in sorted(rotation_angles):
#                options.append(
#                    {
#                        "label": "{:.2f}º".format(rotation_angle),
#                        "value": rotation_angle,
#                    }
#                )
#
#            return options
#
#    @app.callback(
#        Output(f"{structure_id_in}_gb_sigma_options", "value"),
#        [Input(f"{structure_id_in}_gb_sigma_options", "options")],
#        [State(f"{structure_id_in}_gb_sigma_options", "value")],
#    )
#    def update_default_value(options, current_value):
#        if len(options) > 0:
#            return options[0]["value"]
#        else:
#            return current_value
#
#    @app.callback(
#        Output(f"{structure_id_in}_gb_rotation_options", "value"),
#        [Input(f"{structure_id_in}_gb_rotation_options", "options")],
#        [State(f"{structure_id_in}_gb_rotation_options", "value")],
#    )
#    def update_default_value(options, current_value):
#        if len(options) > 0:
#            return options[0]["value"]
#        else:
# #           return current_value


# @app.callback(
#     Output(self.id("transformation_args_kwargs"), "data"),
#     [
#
#     ],
# )
# def update_transformation_kwargs(*args):
#
#     scaling_matrix = [args[0:3], args[3:6], args[6:9]]
#
#     return {"args": [], "kwargs": {"scaling_matrix": scaling_matrix}}
#
