from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import plotly.graph_objects as go
from dash import callback_context, dcc, html
from dash.dependencies import Component, Input, Output
from dash.exceptions import PreventUpdate
from frozendict import frozendict
from pymatgen.analysis.diffraction.xrd import WAVELENGTHS, XRDCalculator
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from scipy.special import wofz

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import (
    Box,
    Column,
    Columns,
    Loading,
    MessageBody,
    MessageContainer,
)

if TYPE_CHECKING:
    from pymatgen.core import Structure


# Scherrer equation: Langford, J. Il, and A. J. C. Wilson. "Scherrer after sixty years:
# a survey and some new results in the determination of crystallite size." Journal of
# applied crystallography 11.2 (1978): 102-113.
# https://doi.org/10.1107/S0021889878012844


#    def __init__(self, symprec: float = None, voltage: float = 200,
#                beam_direction: Tuple[int, int, int] = (0, 0, 1), camera_length: int = 160,
#                debye_waller_factors: Dict[str, float] = None, cs: float = 1) -> None:


# Author: Matthew McDermott
# Contact: mcdermott@lbl.gov

SITES_LIMIT = 25


class XRayDiffractionComponent(MPComponent):
    # TODO: add pole figures for a given single peak for help quantifying texture

    def __init__(
        self, *args, initial_structure: Structure | None = None, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.create_store("structure", initial_data=initial_structure)

    # Default XRD plot style settings
    default_xrd_plot_style = frozendict(
        xaxis={
            "title": "2𝜃 / º",
            "anchor": "y",
            "nticks": 8,
            "showgrid": True,
            "showline": True,
            "side": "bottom",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"size": 16.0},
            "type": "linear",
            "zeroline": False,
        },
        yaxis={
            "title": "Intensity / arb. units",
            "anchor": "x",
            "nticks": 7,
            "showgrid": True,
            "showline": True,
            "side": "left",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"size": 16.0},
            "type": "linear",
            "zeroline": False,
        },
        autosize=True,
        hovermode="x",
        height=225,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, b=50, t=50, pad=0, r=30),
        title="X-ray Diffraction Pattern",
        template="simple_white",
    )

    empty_plot_style = frozendict(
        xaxis={"visible": False},
        yaxis={"visible": False},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    @staticmethod
    def G(x, c, alpha):
        """Return c-centered Gaussian line shape at x with HWHM alpha."""
        return (
            np.sqrt(np.log(2) / np.pi)
            / alpha
            * np.exp(-(((x - c) / alpha) ** 2) * np.log(2))
        )

    @staticmethod
    def L(x, c, gamma):
        """Return c-centered Lorentzian line shape at x with HWHM gamma."""
        return gamma / (np.pi * ((x - c) ** 2 + gamma**2))

    @staticmethod
    def V(x, c, alphagamma):
        """Return the c-centered Voigt line shape at x, scaled to match HWHM of Gaussian and
        Lorentzian profiles.
        """
        alpha = 0.61065 * alphagamma
        gamma = 0.61065 * alphagamma
        sigma = alpha / np.sqrt(2 * np.log(2))
        return np.real(wofz(((x - c) + 1j * gamma) / (sigma * np.sqrt(2)))) / (
            sigma * np.sqrt(2 * np.pi)
        )

    @staticmethod
    def two_theta_to_q(two_theta: float, xray_wavelength: float) -> float:
        """Angular conversion from 2*theta to q in small-angle scattering (SAS).

        Args:
            two_theta (float): in degrees
            xray_wavelength (float): in Ångstroms

        Returns:
            float: Q in Ångstroms^-1
        """
        # thanks @rwoodsrobinson
        return (4 * np.pi / xray_wavelength) * np.sin(np.deg2rad(two_theta) / 2)

    @staticmethod
    def grain_to_hwhm(
        tau: float, two_theta: float, K: float = 0.9, wavelength: float | str = "CuKa"
    ) -> float:
        """Calculate the half-width half-max (alpha or gamma) for a given grain size and
        angle.

        Args:
            tau (float): grain size in nm
            two_theta (float): angle (in 2-theta)
            K (float, optional): shape factor (default 0.9). Defaults to 0.9.
            wavelength (float | str, optional): wavelength radiation in nm. Defaults to "CuKa".

        Returns:
            float: half-width half-max (alpha or gamma), for line profile
        """
        if isinstance(wavelength, str):
            wavelength = WAVELENGTHS[wavelength]
        # Scherrer equation for half-width half max
        # factor of 0.1 to convert wavelength to nm
        return 0.5 * K * 0.1 * wavelength / (tau * abs(np.cos(two_theta / 2)))

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        state = {
            "peak_profile": "G",
            "shape_factor": 0.94,
            "rad_source": "CuKa",
            "x_axis": "two_theta",
            "crystallite_size": 0.1,
        }

        # Main plot
        graph = Loading(
            [
                dcc.Graph(
                    figure=go.Figure(
                        layout={**XRayDiffractionComponent.empty_plot_style}
                    ),
                    id=self.id("xrd-plot"),
                    config={
                        "displayModeBar": False,  # or "hover",
                        "plotGlPixelRatio": 2,
                        "displaylogo": False,
                        # "modeBarButtons": [["toImage"]],  # to only add an image download button
                        "toImageButtonOptions": {
                            "format": "png",
                            "filename": "xrd",
                            "scale": 4,
                            "width": 600,
                            "height": 400,
                        },
                        "editable": True,
                    },
                    responsive=True,
                    animate=False,
                )
            ]
        )

        # Radiation source selector
        rad_source = self.get_choice_input(
            kwarg_label="rad_source",
            state=state,
            label="Radiation source",
            help_str="This defines the wavelength of the incident X-ray radiation.",
            options=[
                {
                    "label": f'{name.replace("a", "α").replace("b", "β")} ({wavelength:.3f} Å)',  # noqa: RUF001
                    "value": name,
                }
                for name, wavelength in WAVELENGTHS.items()
            ],
            style={"width": "10rem"},
        )

        # Shape factor input
        shape_factor = self.get_numerical_input(
            kwarg_label="shape_factor",
            state=state,
            label="Shape Factor",
            help_str="""The peak profile determines what distribute characterizes the broadening of
an XRD pattern. Two extremes are Gaussian distributions, which are useful for peaks with more rounded tops
(typically due to strain broadening) and Lorentzian distributions, which are useful for peaks with
sharper top (typically due to size distributions and dislocations). In reality, peak shapes usually
follow a Voigt distribution, which is a convolution of Gaussian and Lorentzian peak shapes, with the
contribution to both Gaussian and Lorentzian components sample and instrument dependent. Here, both
contributions are equally weighted if Voigt is chosen.""",
        )

        # Peak profile selector (Gaussian, Lorentzian, Voigt)
        peak_profile = self.get_choice_input(
            kwarg_label="peak_profile",
            state=state,
            label="Peak Profile",
            help_str="""The shape factor K, also known as the “Scherrer constant” is a
dimensionless quantity to obtain an actual particle size from an apparent particle size
determined from XRD. The discrepancy is because the shape of an individual crystallite
will change the resulting diffraction broadening. Commonly, a value of 0.94 for isotropic
crystals in a spherical shape is used. However, in practice K can vary from 0.62 to 2.08.""",
            options=[
                {"label": "Gaussian", "value": "G"},
                {"label": "Lorentzian", "value": "L"},
                {"label": "Voigt", "value": "V"},
            ],
            style={"width": "10rem"},
        )

        # 2Theta or Q for x-axis
        x_axis_choice = html.Div(
            [
                self.get_choice_input(
                    kwarg_label="x_axis",
                    state=state,
                    label="Choice of x axis",
                    help_str="Can choose between 2𝜃 or Q, where Q is the magnitude of the reciprocal lattice and "
                    "independent of radiation source.",  # TODO: improve
                    options=[
                        {"label": "2𝜃", "value": "two_theta"},
                        {"label": "Q", "value": "Q"},
                    ],
                )
            ],
            style={
                "display": "none"
            },  # TODO: this is buggy! let's fix it before we share
        )

        # Crystallite size selector (via Scherrer Equation)
        crystallite_size = self.get_slider_input(
            kwarg_label="crystallite_size",
            label="Scherrer crystallite size / nm",
            state=state,
            help_str="Simulate a real diffraction pattern by applying Scherrer broadening, which estimates the "
            "full width at half maximum (FWHM) resulting from a finite, rather than infinite, crystallite "
            "size.",
            domain=[-1, 2],
            step=0.01,
            isLogScale=True,
        )

        static_image = self.get_figure_placeholder("xrd-plot")

        return {
            "x_axis": x_axis_choice,
            "graph": graph,
            "rad_source": rad_source,
            "peak_profile": peak_profile,
            "shape_factor": shape_factor,
            "crystallite_size": crystallite_size,
            "static_image": static_image,
        }

    def layout(self, static_image: bool = False) -> Columns:
        """Get the standard XRD diffraction pattern layout.

        Args:
            static_image (bool, optional): If True, will show a static image instead of an interactive graph.
                Defaults to False.

        Returns:
            Columns: from crystal_toolkit.helpers.layouts
        """
        sub_layouts = self._sub_layouts
        inner = sub_layouts["static_image"] if static_image else sub_layouts["graph"]

        return Columns(
            [
                Column(
                    [Box([inner], style={"height": "480px"})],
                    size=8,
                    style={"height": "600px"},
                ),
                Column(
                    [
                        sub_layouts["x_axis"],
                        sub_layouts["rad_source"],
                        sub_layouts["shape_factor"],
                        sub_layouts["peak_profile"],
                        sub_layouts["crystallite_size"],
                        html.Div(
                            id=self.id("large_cell_note"),
                            style={
                                "marginTop": "20px",
                                "marginRight": "10px",
                            },
                        ),
                    ],
                    size=4,
                ),
            ]
        )

    @staticmethod
    def get_figure(
        peak_profile,
        K,
        rad_source,
        grain_size,
        x_peak,
        y_peak,
        d_hkls,
        hkls,
        x_axis,
        broadening=True,
    ) -> go.Figure:
        hkl_list = [hkl[0]["hkl"] for hkl in hkls]
        # convert to (h k l) format
        hkls = [f"hkl: ({' '.join(map(str, hkl))})" for hkl in hkl_list]

        annotations = [
            f"2𝜃: {round(peak_x, 3)}<br>Intensity: {round(peak_y, 3)}<br>{hkl} <br>d: {round(d, 3)}"
            for peak_x, peak_y, hkl, d in zip(x_peak, y_peak, hkls, d_hkls)
        ]  # text boxes

        first = x_peak[0]
        last = x_peak[-1]
        domain = last - first  # find total domain of angles in pattern
        length = len(x_peak)

        num_sigma = {"G": 5, "L": 12, "V": 12}[peak_profile]

        # optimal number of points per degree determined through usage experiments
        # scaled to log size to the 4th power
        N_density = 150 * (math.log10(grain_size) ** 4) if grain_size > 10 else 150

        N = int(N_density * domain)  # num total points

        x = np.linspace(first, last, N).tolist()
        y = np.zeros(len(x)).tolist()

        if broadening:
            for xp, yp in zip(x_peak, y_peak):
                alpha = XRayDiffractionComponent.grain_to_hwhm(
                    grain_size, math.radians(xp / 2), K=float(K), wavelength=rad_source
                )
                sigma = (alpha / np.sqrt(2 * np.log(2))).item()

                center_idx = int(round((xp - first) * N_density))
                # total broadening window of 2 * num_sigma
                half_window = int(round(num_sigma * sigma * N_density))

                lb = max(0, (center_idx - half_window))
                ub = min(N, (center_idx + half_window))

                G0 = getattr(XRayDiffractionComponent, peak_profile)(0, 0, alpha)
                for ii, jj in zip(range(lb, ub), range(lb, ub)):
                    Gi = getattr(XRayDiffractionComponent, peak_profile)(
                        x[ii], xp, alpha
                    )
                    y[jj] += yp * Gi / G0

        layout = {**XRayDiffractionComponent.default_xrd_plot_style}

        if x_axis == "Q":
            x_peak = XRayDiffractionComponent.two_theta_to_q(
                x_peak, WAVELENGTHS[rad_source]
            )
            x = XRayDiffractionComponent.two_theta_to_q(x, WAVELENGTHS[rad_source])
            layout["xaxis"]["title"] = "Q / Å⁻¹"
        else:
            layout["xaxis"]["title"] = "2𝜃 / º"
        layout["xaxis"]["range"] = [min(x), max(x)]
        bar_width = 0.003 * (max(x) - min(x))  # set width of bars to 0.5% of the domain

        plot_data = [
            go.Bar(
                x=x_peak,
                y=y_peak,
                width=[bar_width] * length,
                hoverinfo="text",
                text=annotations,
                opacity=0.8,
                marker={"color": "black"},
            )
        ]
        if broadening:
            plot_data.append(go.Scatter(x=x, y=y, hoverinfo="none"))

        return go.Figure(data=plot_data, layout=layout)

    def generate_callbacks(self, app, cache) -> None:
        @app.callback(
            Output(self.id("xrd-plot"), "figure"),
            [
                Input(self.id(), "data"),
                Input(self.get_kwarg_id("crystallite_size"), "value"),
                Input(self.get_kwarg_id("rad_source"), "value"),
                Input(self.get_kwarg_id("peak_profile"), "value"),
                Input(self.get_kwarg_id("shape_factor"), "value"),
                Input(self.get_kwarg_id("x_axis"), "value"),
                Input(self.id("structure"), "data"),
            ],
        )
        def update_graph(
            data, log_size, rad_source, peak_profile, K, x_axis, structure
        ):
            if not data:
                raise PreventUpdate

            kwargs = self.reconstruct_kwargs_from_state(callback_context.inputs)

            if not kwargs:
                raise PreventUpdate

            peak_profile = kwargs["peak_profile"]
            K = kwargs["shape_factor"]
            rad_source = kwargs["rad_source"]
            log_size = float(kwargs["crystallite_size"])
            x_axis = kwargs["x_axis"]

            grain_size = 10**log_size
            x_peak = data["x"]
            y_peak = data["y"]
            d_hkls = data["d_hkls"]
            hkls = data["hkls"]
            # suppress broadening for larger cell
            broadening = len(self.from_data(structure).sites) < SITES_LIMIT

            return self.get_figure(
                peak_profile,
                K,
                rad_source,
                grain_size,
                x_peak,
                y_peak,
                d_hkls,
                hkls,
                x_axis,
                broadening,
            )

        @app.callback(
            Output(self.id(), "data"),
            [
                Input(self.id("structure"), "data"),
                Input(self.get_kwarg_id("rad_source"), "value"),
            ],
        )
        def pattern_from_struct(struct, rad_source):
            if struct is None or not rad_source:
                raise PreventUpdate

            struct = self.from_data(struct)

            rad_source = self.reconstruct_kwarg_from_state(
                callback_context.inputs, "rad_source"
            )

            sga = SpacegroupAnalyzer(struct)
            # always get conventional structure
            struct = sga.get_conventional_standard_structure()

            xrd_calc = XRDCalculator(
                wavelength=WAVELENGTHS[rad_source], symprec=0, debye_waller_factors=None
            )
            data = xrd_calc.get_pattern(struct, two_theta_range=None)

            return data.as_dict()

        @app.callback(
            Output(self.id("large_cell_note"), "children"),
            Input(self.id("structure"), "data"),
        )
        def update_message(structure):
            if len(self.from_data(structure).sites) < SITES_LIMIT:
                return html.Div([])
            return MessageContainer(
                MessageBody(
                    "Peak broadening is currently disabled for materials with "
                    f"more than {SITES_LIMIT} sites due to long compute time. Please contact "
                    "feedback@materialsproject.org if you need assistance with the graph."
                )
            )

        # @app.callback(
        #     Output(self.id("static-image"), "src"), Input(self.id("xrd-plot"), "figure")
        # )
        # def update_static_image(data):
        #     scope = PlotlyScope()
        #     output = scope.transform(data, format="png", width=600, height=400, scale=4)
        #     image = b64encode(output).decode("ascii")

        #     return f"data:image/png;base64,{image}"
