import dash
import dash_core_components as dcc
import dash_html_components as html
import math
import numpy as np
from scipy.special import wofz
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from pymatgen import MPRester
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from pymatgen.analysis.diffraction.xrd import XRDCalculator, WAVELENGTHS

from crystal_toolkit.helpers.layouts import *
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent


# Author: Matthew McDermott
# Contact: mcdermott@lbl.gov


class XRayDiffractionComponent(MPComponent):
    def __init__(self, *args, initial_structure=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("struct", initial_data=initial_structure)

        self.initial_xrdcalculator_kwargs = {
            "wavelength": "CuKa",
            "symprec": 0,
            "debye_waller_factors": None,
        }
        self.create_store(
            "xrdcalculator_kwargs", initial_data=self.initial_xrdcalculator_kwargs
        )

    # Default XRD plot style settings
    default_xrd_plot_style = dict(
        xaxis={
            "title": "2θ (deg)",
            "anchor": "y",
            "mirror": "ticks",
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
            "title": "Intensity (a.u.)",
            "anchor": "x",
            "mirror": "ticks",
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
    )

    empty_plot_style = {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }

    @staticmethod
    def G(x, c, alpha):
        """ Return c-centered Gaussian line shape at x with HWHM alpha """
        return (
            np.sqrt(np.log(2) / np.pi)
            / alpha
            * np.exp(-(((x - c) / alpha) ** 2) * np.log(2))
        )

    @staticmethod
    def L(x, c, gamma):
        """ Return c-centered Lorentzian line shape at x with HWHM gamma """
        return gamma / (np.pi * ((x - c) ** 2 + gamma ** 2))

    @staticmethod
    def V(x, c, alphagamma):
        """ Return the c-centered Voigt line shape at x, scaled to match HWHM of Gaussian and Lorentzian profiles."""
        alpha = 0.61065 * alphagamma
        gamma = 0.61065 * alphagamma
        sigma = alpha / np.sqrt(2 * np.log(2))
        return np.real(wofz(((x - c) + 1j * gamma) / (sigma * np.sqrt(2)))) / (
            sigma * np.sqrt(2 * np.pi)
        )

    def grain_to_hwhm(self, tau, two_theta, K=0.9, wavelength="CuKa"):
        """
        :param tau: grain size in nm
        :param theta: angle (in 2-theta)
        :param K: shape factor (default 0.9)
        :param wavelength: wavelength radiation in nm
        :return: half-width half-max (alpha or gamma), for line profile
        """
        wavelength = WAVELENGTHS[wavelength]
        return (
            0.5 * K * 0.1 * wavelength / (tau * abs(np.cos(two_theta / 2)))
        )  # Scherrer equation for half-width half max

    @property
    def _sub_layouts(self):

        # Main plot
        graph = Loading(
            [
                dcc.Graph(
                    figure=go.Figure(layout=XRayDiffractionComponent.empty_plot_style),
                    id=self.id("xrd-plot"),
                    config={"displayModeBar": False},
                    responsive=True,
                )
            ]
        )

        # Radiation source selector
        rad_source = html.Div(
            [
                html.P("Radiation Source"),
                dcc.Dropdown(
                    id=self.id("rad-source"),
                    options=[{"label": i, "value": i} for i in WAVELENGTHS.keys()],
                    value=self.initial_xrdcalculator_kwargs["wavelength"],
                    placeholder="Select a source...",
                    clearable=False,
                ),
            ],
            style={"max-width": "200"},
        )

        # Shape factor input
        shape_factor = html.Div(
            [
                html.P("Shape Factor, K "),
                dcc.Input(
                    id=self.id("shape-factor"),
                    placeholder="0.94",
                    type="text",
                    value="0.94",
                ),
            ],
            style={"max-width": "200"},
        )
        # Peak profile selector (Gaussian, Lorentzian, Voigt)
        peak_profile = html.Div(
            [
                html.P("Peak Profile"),
                dcc.Dropdown(
                    id=self.id("peak-profile"),
                    options=[
                        {"label": "Gaussian", "value": "G"},
                        {"label": "Lorentzian", "value": "L"},
                        {"label": "Voigt", "value": "V"},
                    ],
                    value="G",
                    clearable=False,
                ),
            ],
            style={"max-width": "200"},
        )

        # Crystallite size selector (via Scherrer Equation)
        crystallite_size = html.Div(
            [
                html.P("Scherrer Crystallite Size (nm)"),
                html.Div(
                    [
                        dcc.Slider(
                            id=self.id("crystallite-slider"),
                            marks={i: "{}".format(10 ** i) for i in range(-1, 3)},
                            min=-1,
                            max=2,
                            value=0,
                            step=0.01,
                        )
                    ],
                    style={"max-width": "500"},
                ),
                html.Div(
                    [], id=self.id("crystallite-input"), style={"padding-top": "20px"}
                ),
            ]
        )

        return {
            "graph": graph,
            "rad_source": rad_source,
            "peak_profile": peak_profile,
            "shape_factor": shape_factor,
            "crystallite_size": crystallite_size,
        }

    def layout(self):
        return html.Div(
            [
                Columns(
                    [
                        Column([self._sub_layouts["graph"]], size=8),
                        Column(
                            [
                                self._sub_layouts["rad_source"],
                                self._sub_layouts["shape_factor"],
                                self._sub_layouts["peak_profile"],
                                self._sub_layouts["crystallite_size"],
                            ],
                            size=4,
                        ),
                    ]
                )
            ]
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("xrd-plot"), "figure"),
            [
                Input(self.id(), "data"),
                Input(self.id("crystallite-slider"), "value"),
                Input(self.id("rad-source"), "value"),
                Input(self.id("peak-profile"), "value"),
                Input(self.id("shape-factor"), "value"),
            ],
        )
        def update_graph(data, logsize, rad_source, peak_profile, K):

            if not data:
                raise PreventUpdate

            x_peak = data["x"]
            y_peak = data["y"]
            d_hkls = data["d_hkls"]
            grain_size = 10 ** logsize

            hkl_list = [hkl[0]["hkl"] for hkl in data["hkls"]]
            hkls = [
                "hkl: (" + " ".join([str(i) for i in hkl]) + ")" for hkl in hkl_list
            ]  # convert to (h k l) format

            annotations = [
                f"2Θ: {round(peak_x,3)}<br>Intensity: {round(peak_y,3)}<br>{hkl} <br>d: {round(d, 3)}"
                for peak_x, peak_y, hkl, d in zip(x_peak, y_peak, hkls, d_hkls)
            ]  # text boxes

            first = x_peak[0]
            last = x_peak[-1]
            domain = last - first  # find total domain of angles in pattern
            bar_width = 0.003 * domain  # set width of bars to 0.5% of the domain
            length = len(x_peak)

            num_sigma = {"G": 5, "L": 12, "V": 12}[peak_profile]

            # optimal number of points per degree determined through usage experiments
            if logsize > 1:
                N_density = 150 * (logsize ** 4)  # scaled to log size to the 4th power
            else:
                N_density = 150

            N = int(N_density * domain)  # num total points
            x = np.linspace(first, last, N).tolist()
            y = np.zeros(len(x)).tolist()

            for xp, yp in zip(x_peak, y_peak):
                alpha = self.grain_to_hwhm(
                    grain_size, math.radians(xp / 2), K=float(K), wavelength=rad_source
                )
                sigma = (alpha / np.sqrt(2 * np.log(2))).item()

                center_idx = int(round((xp - first) * N_density))
                half_window = int(
                    round(num_sigma * sigma * N_density)
                )  # i.e. total window of 2 * num_sigma

                lb = max([0, (center_idx - half_window)])
                ub = min([N, (center_idx + half_window)])

                G0 = getattr(self, peak_profile)(0, 0, alpha)
                for i, j in zip(range(lb, ub), range(lb, ub)):
                    y[j] += yp * getattr(self, peak_profile)(x[i], xp, alpha) / G0

            plotdata = [
                go.Bar(
                    x=x_peak,
                    y=y_peak,
                    width=[bar_width] * length,
                    hoverinfo="text",
                    text=annotations,
                    opacity=0.2,
                ),
                go.Scatter(x=x, y=y, hoverinfo="none"),
            ]
            plot = go.Figure(data=plotdata, layout=self.default_xrd_plot_style)

            return plot

        @app.callback(
            Output(self.id(), "data"),
            [
                Input(self.id("struct"), "data"),
                Input(self.id("xrdcalculator_kwargs"), "data"),
            ],
        )
        def pattern_from_struct(struct, xrdcalculator_kwargs):

            if struct is None:
                raise PreventUpdate

            struct = self.from_data(struct)
            xrdcalculator_kwargs = self.from_data(xrdcalculator_kwargs)

            sga = SpacegroupAnalyzer(struct)
            struct = (
                sga.get_conventional_standard_structure()
            )  # always get conventional structure

            xrdc = XRDCalculator(**xrdcalculator_kwargs)
            data = xrdc.get_pattern(struct, two_theta_range=None)

            return data.as_dict()

        @app.callback(
            Output(self.id("xrdcalculator_kwargs"), "data"),
            [Input(self.id("rad-source"), "value")],
            [State(self.id("xrdcalculator_kwargs"), "data")],
        )
        def update_kwargs(rad_source, xrdcalculator_kwargs):
            xrdcalculator_kwargs = self.from_data(xrdcalculator_kwargs)
            xrdcalculator_kwargs["wavelength"] = rad_source
            return xrdcalculator_kwargs

        @app.callback(
            Output(self.id("crystallite-input"), "children"),
            [Input(self.id("crystallite-slider"), "value")],
        )
        def update_slider_output(value):
            return html.P("Selected: {} nm".format(round(10 ** value, 3)))


class XRayDiffractionPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xrd = XRayDiffractionComponent(links={"struct": self.id()})

    @property
    def title(self):
        return "Diffraction Pattern"

    @property
    def description(self):
        return "Display the powder X-ray diffraction pattern for this structure."

    def contents_layout(self) -> html.Div:
        return self.xrd.layout()
