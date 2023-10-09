from __future__ import annotations

from time import time
from typing import TYPE_CHECKING
from warnings import warn

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import Box, Column, Columns, Loading, Reveal

if TYPE_CHECKING:
    from pymatgen.core import Structure

try:
    import py4DSTEM
except ImportError:
    no_py4dstem_msg = "requires the py4DSTEM package. Please pip install py4DSTEM."
    py4DSTEM = None

# Author: Steven Zeltmann
# Contact: steven.zeltmann@lbl.gov


class TEMDiffractionComponent(MPComponent):
    def __init__(
        self, *args, initial_structure: Structure | None = None, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.create_store("structure", initial_data=initial_structure)
        self.calculator = TEMDiffractionCalculator()

    def layout(self) -> Columns:
        if not py4DSTEM:
            warn(f"{type(self).__name__} {no_py4dstem_msg}")
            col = Column(
                "This feature will not work unless py4DSTEM is installed on the server."
            )
            return Columns([col])

        voltage = self.get_numerical_input(
            kwarg_label="voltage",
            default=200,
            step=10.0,
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
            label="Maximum Scattering Angle [Å⁻¹]",
            help_str="Maximum scattering angle to compute reciprocal lattice.",
            max=10,
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
            default=500.0,
            step=1.0,
            label="Thickness [Å]",
            help_str="Sample thickness in Ångströms, for dynamical simulation.",
        )

        # Advanced options

        excitation_tol = self.get_numerical_input(
            kwarg_label="sigma_excitation_error",
            default=0.02,
            step=0.001,
            label="Excitation error tolerance [Å⁻¹]",
            help_str="Standard deviation of Gaussian function for damping reciprocal lattice points.",
            max=0.2,
        )

        Fhkl_tol = self.get_numerical_input(
            kwarg_label="tol_structure_factor",
            default=0.0,
            step=0.001,
            label="|F<sub>khl</sub>| tolerance",
            help_str="Minimum structure factor intensity to include a reflection. Setting"
            " this value to zero allows kinematically forbidden reflections to be excited"
            " in Bloch wave calculations, but increases computation time.",
        )

        absorption_method_names = {
            "Lobato (Elastic)": "Lobato",
            "Lobato (Hashimoto absorptive)": "Lobato-absorptive",
            "Weickenmeier-Kohl (Elastic)": "WK",
            "Weickenmeier-Kohl (Core only)": "WK-C",
            "Weickenmeier-Kohl (Phonon only)": "WK-P",
            "Weickenmeier-Kohl (Core + Phonon)": "WK-CP",
        }

        absorption_methods = self.get_choice_input(
            kwarg_label="dynamical_method",
            label="Scattering Factor Parameterization",
            default="WK-CP",
            help_str="Parameterization of absorptive scattering factors, used only"
            " for dynamical calculations. Kinematic calculations always use Lobato.",
            options=[
                {
                    "label": name,
                    "value": shortname,
                }
                for name, shortname in absorption_method_names.items()
            ],
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
            default=0.5,
            step=0.1,
            help_str="Power for scaling intensities in the displayed pattern",
        )

        advanced_options = Reveal(
            title="Advanced Options",
            children=[
                excitation_tol,
                html.Br(),
                Fhkl_tol,
                html.Br(),
                absorption_methods,
                html.Br(),
                DWF,
                html.Br(),
                gamma,
            ],
            id="tem-advanced-options",
        )

        return Columns(
            [
                Column([Box(Loading(id=self.id("tem-plot")))], size=8),
                Column(
                    [
                        voltage,
                        html.Br(),
                        beam_direction,
                        html.Br(),
                        k_max,
                        html.Br(),
                        use_dynamical,
                        html.Br(),
                        thickness,
                        html.Br(),
                        advanced_options,
                    ],
                    size=4,
                ),
            ],
        )

    def generate_callbacks(self, app, cache) -> None:
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
                figure=self.calculator.get_plot_2d(structure, **kwargs),
                responsive=False,
                config=dict(displayModeBar=False, displaylogo=False),
            )


class TEMDiffractionCalculator:
    """Docstring."""

    def __init__(self) -> None:
        # Initialize parameter caches to invalid so that on the first run,
        # everything gets computed from scratch.
        self.crystal = None
        self.voltage = np.nan
        self.k_max = np.nan
        self.tol_structure_factor = np.nan
        self.sigma_excitation_error = np.nan
        self.DWF = np.nan
        self.dynamical_method = ""

    def get_plot_2d(
        self,
        structure,
        beam_direction,
        voltage: float,
        k_max: float,
        thickness: float,
        tol_structure_factor: float,
        sigma_excitation_error: float,
        use_dynamical: bool,
        dynamical_method: str,
        DWF: float,
        gamma,
        # **kwargs,
    ) -> go:
        """Generate diffraction pattern using py4DSTEM and return as a plotly Figure object."""
        if not py4DSTEM:
            raise ImportError(f"{type(self).__name__} {no_py4dstem_msg}")
        t0 = time()
        # figure out what needs to be recomputed:
        new_crystal = py4DSTEM.process.diffraction.Crystal.from_pymatgen_structure(
            structure
        )
        needs_structure = not self.crystal or not (
            self.crystal.positions.shape[0] == new_crystal.positions.shape[0]
            and np.allclose(self.crystal.numbers, new_crystal.numbers)
            and np.allclose(self.crystal.cell, new_crystal.cell)
            and np.allclose(self.crystal.positions, new_crystal.positions)
        )

        needs_kinematic_SFs = (
            needs_structure
            or (self.voltage != voltage)
            or (self.k_max != k_max)
            or (self.tol_structure_factor != tol_structure_factor)
        )

        needs_dynamic_SFs = use_dynamical and (
            needs_structure
            or self.DWF != DWF
            or self.dynamical_method != dynamical_method
        )

        # # Check if the cache logic is working
        # print(
        #     f"Needs structure?\t{needs_structure}\nNeeds SFs?:\t{needs_kinematic_SFs}\nNeeds Ug?:\t{needs_dynamic_SFs}"
        # )

        if needs_structure:
            self.crystal = py4DSTEM.process.diffraction.Crystal.from_pymatgen_structure(
                structure=structure,
            )

        if needs_kinematic_SFs:
            self.update_structure_factors(voltage, k_max, tol_structure_factor)

        if needs_dynamic_SFs:
            self.update_dynamic_structure_factors(dynamical_method, DWF)

        # generate diffraction pattern
        pattern = self.crystal.generate_diffraction_pattern(
            zone_axis_lattice=beam_direction, tol_intensity=0.0
        )

        # rescale intensities
        pattern.data["intensity"] /= pattern.data["intensity"].max()

        # perform dynamical simulation, if Bloch is selected
        if use_dynamical:
            pattern = self.crystal.generate_dynamical_diffraction_pattern(
                pattern, thickness=thickness, zone_axis_lattice=beam_direction
            )

        print(f"Generated pattern in {time()-t0:.3f} seconds")

        # generate plotly Figure
        return self.pointlist_to_spots(pattern, beam_direction, gamma)

    def update_structure_factors(
        self,
        voltage,
        k_max,
        tol_structure_factor,
    ):
        self.crystal.setup_diffraction(accelerating_voltage=voltage * 1e3)
        self.crystal.calculate_structure_factors(
            k_max=k_max, tol_structure_factor=tol_structure_factor
        )

        self.voltage = voltage
        self.k_max = k_max
        self.tol_structure_factor = tol_structure_factor

    def update_dynamic_structure_factors(
        self,
        dynamical_method,
        DWF,
    ):
        self.crystal.calculate_dynamical_structure_factors(
            accelerating_voltage=self.voltage * 1e3,
            method=dynamical_method,
            k_max=self.k_max,
            thermal_sigma=DWF,
            recompute_kinematic_structure_factors=False,
            verbose=False,
        )

        self.dynamical_method = dynamical_method
        self.DWF = DWF

    def pointlist_to_spots(self, pattern, beam_direction, gamma):
        hkl_strings = [
            f"({r['h']} {r['k']} {r['l']})<br>I: {r['intensity']:.3e}"
            for r in pattern.data
        ]

        scaled_intensity = pattern.data["intensity"] ** gamma
        scaled_intensity /= scaled_intensity.max()

        data = go.Scatter(
            x=np.round(pattern.data["qx"], 3),
            y=np.round(pattern.data["qy"], 3),
            hovertemplate="%{text}<br>q<sub>x</sub>: %{x:.2f} Å⁻¹<br>q<sub>y</sub>: %{y:.2f}Å⁻¹<extra></extra>",
            text=hkl_strings,
            mode="markers",
            marker=dict(
                size=12,
                cmax=1,
                cmin=0,
                color=scaled_intensity,
                colorscale="gray_r",
            ),
            showlegend=False,
        )

        plot_max = self.k_max * 1.2

        layout = go.Layout(
            title="2D Diffraction Pattern<br>Beam Direction: ("
            + "".join(str(int(e)) for e in beam_direction)
            + ")",
            font=dict(size=14, color="#7f7f7f"),
            hovermode="closest",
            xaxis=dict(
                title="q<sub>x</sub> [Å<sup>-1</sup>]",
                range=[-plot_max, plot_max],
                showgrid=False,
                zeroline=False,
                tickmode="linear",
                dtick=0.5,
                showticklabels=True,
                mirror=True,
                ticks="outside",
                showline=True,
                linecolor="#444",
            ),
            yaxis=dict(
                title="q<sub>y</sub> [Å<sup>-1</sup>]",
                range=[-plot_max, plot_max],
                showgrid=False,
                zeroline=False,
                tickmode="linear",
                dtick=0.5,
                showticklabels=True,
                mirror=True,
                ticks="outside",
                showline=True,
                linecolor="#444",
            ),
            width=550,
            height=550,
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        return go.Figure(data=data, layout=layout)
