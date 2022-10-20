from __future__ import annotations

import numpy as np
import plotly.graph_objs as go
from dash import callback_context, dcc, html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.diffraction.tem import TEMCalculator
from pymatgen.analysis.diffraction.core import AbstractDiffractionPatternCalculator
from scipy.special import wofz
import py4DSTEM

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import Box, Column, Columns, Loading, Reveal

# Author: Steven Zeltmann
# Contact: steven.zeltmann@lbl.gov


class TEMDiffractionComponent(MPComponent):
    def __init__(self, *args, initial_structure=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("structure", initial_data=initial_structure)
        self.calculator = TEMDiffractionCalculator()

    def layout(self) -> Columns:

        voltage = self.get_numerical_input(
            kwarg_label="voltage",
            default=200,
            step=50.,
            label="Voltage / kV",
            help_str="Accelerating voltage for electron beam.",
        )

        beam_direction = self.get_numerical_input(
            kwarg_label="beam_direction",
            default=[0, 0, 1],
            label="Beam Direction",
            help_str="The direction of the electron beam fired onto the sample.",
            shape=(3,),
            is_int=True,
        )

        k_max = self.get_numerical_input(
            kwarg_label="k_max",
            default=1.5,
            step=0.25,
            label="Maximum Scattering Angle [Å<sup>-1</sup>]",
            help_str="Maximum scattering angle to compute reciprocal lattice.",
        )

        use_dynamical = self.get_bool_input(
            kwarg_label="use_dynamical",
            default=False,
            label="Use Bloch Wave Dynamical Calculator",
            help_str="The Bloch wave calculator gives accurate diffraction "
            "intensities for thick crystals by including multiple scattering"
            " of the electron beam, but requires substantially more computation time.",
        )

        thickness = self.get_numerical_input(
            kwarg_label="thickness",
            default=500.,
            step=10.,
            label="Thickness [Å]",
            help_str="Sample thickness in Ångströms, for dynamical simulation.")

        # Advanced options

        excitation_tol = self.get_numerical_input(
            kwarg_label="sigma_excitation_error",
            default=0.02,
            label="Excitation error tolerance [Å-1]",
            help_str="Standard deviation of Gaussian function for damping")

        Fhkl_tol = self.get_numerical_input(
            kwarg_label="tol_intensity",
            default=0.,
            step=0.001,
            label="|Fkhl| tolerance",
            help_str="Minimum structure factor intensity to include a reflection.",
        )

        absorption_method_names = {
                "Lobato (Elastic)":"Lobato",
                "Lobato (Hashimoto absoprtive)": "Lobato-absorptive",
                "Weickenmeier-Kohl (Elastic)": "WK",
                "Weickenmeier-Kohl (Core only)": "WK-C",
                "Weickenmeier-Kohl (Phonon only)": "WK-P",
                "Weickenmeier-Kohl (Core + Phonon)": "WK-CP"
            }

        absorption_methods = self.get_choice_input(
            kwarg_label="dynamical_method",
            label="Scattering Factor Parameterization",
            default="WK-CP",
            help_str="Parameterization of absoprtive scattering factors, used only"
                    " for dynamical calculations. Kinematic calculations always use Lobato",
            options=[
                {
                    "label":name,
                    "value":shortname,
                }
                for name, shortname in absorption_method_names.items()
            ]
        )

        DWF = self.get_numerical_input(
            kwarg_label="DWF",
            label="RMS Atomic Displacements [Å]",
            default=0.08,
            step=0.01,
            help_str="RMS atomic displacements used to include thermal smearing of"
                    "the electrostatic potential when a Weickenmeier-Kohl scattering factor is chosen",
        )

        gamma = self.get_numerical_input(
            kwarg_label="gamma",
            label="Display Gamma",
            default=1.0,
            step=0.1,
            help_str="Power for scaling intensities in the displayed pattern",
        )

        advanced_options = Reveal(
            title="Advanced Options",
            children=[excitation_tol, html.Br(), 
                      Fhkl_tol, html.Br(),
                      absorption_methods, html.Br(),
                      DWF, html.Br(),
                      gamma],
            id="tem-advanced-options",
        )

        return Columns(
            [
                Column([Box(Loading(id=self.id("tem-plot")))], size=8),
                Column(
                    [
                        voltage, html.Br(), 
                        beam_direction, html.Br(),
                        k_max, html.Br(),
                        use_dynamical, html.Br(),
                        thickness, html.Br(),
                        advanced_options,
                    ],
                    size=4,
                ),
            ],
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("tem-plot"), "children"),
            [
                Input(self.id("structure"), "data"),
                Input(self.get_all_kwargs_id(), "value"),
            ],
        )
        def generate_diffraction_pattern(structure, *args):

            structure = self.from_data(structure)
            kwargs = self.reconstruct_kwargs_from_state()

            # calculator = TEMCalculator(**kwargs)

            print("kwargs", kwargs)

            return dcc.Graph(
                figure=self.calculator.get_plot_2d(structure,**kwargs),
                responsive=False,
                config=dict(displayModeBar=False, displaylogo=False),
            )


class TEMDiffractionCalculator:
    """
    Docstring
    """

    def __init__(self) -> None:
        self.crystal = None

    def get_plot_2d(
        self,
        structure,
        beam_direction,
        voltage: float,
        k_max: float,
        thickness: float,
        sigma_excitation_error: float = None,
        use_dynamical: bool = False,
        dynamical_method=None,
        DWF: float = None,
        **kwargs,
    ) -> go:
        """
        generate diffraction pattern and return as a plotly graph object
        """

        # check if cached structure factors are valid, recompute if needed
        # (and check if dynamical factors are needed)
        self.update_structure_factors(
            structure, k_max, sigma_excitation_error, use_dynamical, DWF
        )

        # generate diffraction pattern
        pattern = self.crystal.generate_diffraction_pattern(
            zone_axis_lattice=beam_direction
        )

        # perform dynamical simulation, if Bloch is selected
        if use_dynamical:
            pattern = self.crystal.generate_dynamical_diffraction_pattern(
                pattern, thickness=thickness, zone_axis_lattice=beam_direction
            )

        # generate plotly spots for each reflection
        spots = self.pointlist_to_spots(pattern)

        # wrap everything up into a figure

        pass

    def update_structure_factors(
        self, new_structure, k_max, sigma_excitation_error, use_dynamical, DWF
    ):
        pass

    def pointlist_to_spots(
        self,
        pattern,
    ):
        pass
