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
from crystal_toolkit.helpers.layouts import Box, Column, Columns, Loading

# Author: Steven Zeltmann
# Contact: steven.zeltmann@lbl.gov


class TEMDiffractionComponent(MPComponent):
    def __init__(self, *args, initial_structure=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("structure", initial_data=initial_structure)

    def layout(self) -> Columns:

        voltage = self.get_numerical_input(
            kwarg_label="voltage",
            default=200,
            label="Voltage / kV",
            help_str="Accelerating voltage for electron beam."
        )

        beam_direction = self.get_numerical_input(
            kwarg_label="beam_direction",
            default=[0, 0, 1],
            label="Beam Direction",
            help_str="The direction of the electron beam fired onto the sample.",
            shape=(3,),
            is_int=True,
        )

        # TODO: add additional kwargs for TemCalculator, or switch to an alternative solution

        return Columns(
            [
                Column([Box(Loading(id=self.id("tem-plot")))], size=8),
                Column(
                    [voltage, html.Br(), beam_direction],
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

            calculator = TEMCalculator(**kwargs)

            print("kwargs", kwargs)

            return dcc.Graph(
                figure=calculator.get_plot_2d(structure),
                responsive=False,
                config=dict(displayModeBar=False, displaylogo=False),
            )


class TEMDiffractionCalculator(AbstractDiffractionPatternCalculator):
    """
    Docstring
    """

    def __init__(self)->None:
        self.crystal = None

    def get_plot_2d(
        self,
        structure,
        beam_direction,
        voltage:float,
        k_max:float,
        thickness:float,
        structure_factor_tol:float=None,
        use_dynamical:bool=False,
        dynamical_method=None,
        DWF:float=None
        **kwargs)->go:
        """
        generate diffraction pattern and return as a plotly graph object
        """

        # check if cached structure factors are valid, recompute if needed
        # (and check if dynamical factors are needed)
        self.update_structure_factors(
            structure,
            k_max,
            structure_factor_tol,
            use_dynamical,
            DWF)

        # generate diffraction pattern
        pattern = self.crystal.generate_diffraction_pattern(
            zone_axis_lattice=beam_direction)

        # perform dynamical simulation, if Bloch is selected
        if use_dynamical:
            pattern = self.crystal.generate_dynamical_diffraction_pattern(
                pattern,
                thickness=thickness,
                zone_axis_lattice=beam_direction)

        # generate plotly spots for each reflection
        spots = self.pointlist_to_spots(pattern)

        # wrap everything up into a figure


        pass

    def update_structure_factors(
        self,
        new_structure,
        k_max,
        structure_factor_tol,
        use_dynamical,
        DWF
        ):
        pass

    def pointlist_to_spots(
        self,
        pattern,
        ):
        pass

