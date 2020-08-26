import dash
import dash_core_components as dcc
import dash_html_components as html
import math
import numpy as np
from dash import callback_context
from scipy.special import wofz
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from pymatgen import MPRester
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.diffraction.tem import TEMCalculator


# Scherrer equation:
# Langford, J. Il, and A. J. C. Wilson. "Scherrer after sixty years: a survey and some new results in the determination of crystallite size." Journal of applied crystallography 11.2 (1978): 102-113.
# https://doi.org/10.1107/S0021889878012844


#    def __init__(self, symprec: float = None, voltage: float = 200,
#                beam_direction: Tuple[int, int, int] = (0, 0, 1), camera_length: int = 160,
#                debye_waller_factors: Dict[str, float] = None, cs: float = 1) -> None:

from pymatgen.analysis.diffraction.xrd import XRDCalculator, WAVELENGTHS

from crystal_toolkit.helpers.layouts import *
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent


# Author: Matthew McDermott
# Contact: mcdermott@lbl.gov


class TEMDiffractionComponent(MPComponent):
    def layout(self):
        return Columns(
            [
                Column([self._sub_layouts["graph"]], size=8),
                Column(
                    [
                        self._sub_layouts["x_axis"],
                        self._sub_layouts["rad_source"],
                        self._sub_layouts["shape_factor"],
                        self._sub_layouts["peak_profile"],
                        self._sub_layouts["crystallite_size"],
                    ],
                    size=4,
                ),
            ],
            id=self.id("inner-contents"),
        )

    def generate_callbacks(self, app, cache):
        pass


class XRayDiffractionComponent(MPComponent):
    # TODO: add pole figures for a given single peak for help quantifying texture

    def __init__(self, *args, initial_structure=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("struct", initial_data=initial_structure)

    # Default XRD plot style settings
    default_xrd_plot_style = dict(
        xaxis={
            "title": "2𝜃 / º",
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
            "title": "Intensity / arb. units",
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
        title="X-ray Diffraction Pattern",
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

    @staticmethod
    def twotheta_to_q(twotheta, xray_wavelength):
        """
        Convert twotheta to Q.

        :param twotheta: in degrees
        :param xray_wavelength: in Ångstroms
        :return:
        """
        # thanks @rwoodsrobinson
        return (4 * np.pi / xray_wavelength) * np.sin(np.deg2rad(twotheta))

    def grain_to_hwhm(self, tau, two_theta, K=0.9, wavelength="CuKa"):
        """
        :param tau: grain size in nm
        :param two_theta: angle (in 2-theta)
        :param K: shape factor (default 0.9)
        :param wavelength: wavelength radiation in nm
        :return: half-width half-max (alpha or gamma), for line profile
        """
        wavelength = WAVELENGTHS[wavelength]
        # factor of 0.1 to convert wavelength to nm
        return (
            0.5 * K * 0.1 * wavelength / (tau * abs(np.cos(two_theta / 2)))
        )  # Scherrer equation for half-width half max

    @property
    def _sub_layouts(self):

        state = {
            "peak_profile": "G",
            "shape_factor": 0.94,
            "rad_source": "CuKa",
            "x_axis": "twotheta",
            "crystallite_size": 0.1,
        }

        # download

        # Main plot
        graph = Loading(
            [
                dcc.Graph(
                    figure=go.Figure(layout=XRayDiffractionComponent.empty_plot_style),
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

        # Broaden peaks
        broadening_toggle = ...

        # Radiation source selector
        rad_source = self.get_choice_input(
            kwarg_label="rad_source",
            state=state,
            label="Radiation source",
            help_str="...",
            options=[
                {"label": wav.replace("a", "α").replace("b", "β"), "value": wav}
                for wav in WAVELENGTHS.keys()
            ],
        )

        # Shape factor input
        shape_factor = self.get_numerical_input(
            kwarg_label="shape_factor",
            state=state,
            label="Shape Factor",
            help_str="""The peak profile determines what distribute characterizes the broadening of an XRD pattern. 
Two extremes are Gaussian distributions, which are useful for peaks with more rounded tops (typically due to strain 
broadening) and Lorentzian distributions, which are useful for peaks with sharper top (typically due to size 
distributions and dislocations). In reality, peak shapes usually follow a Voigt distribution, which is a convolution of 
Gaussian and Lorentzian peak shapes, with the contribution to both Gaussian and Lorentzian components sample and instrument 
dependent. Here, both contributions are equally weighted if Voigt is chosen.""",
        )

        # Peak profile selector (Gaussian, Lorentzian, Voigt)
        peak_profile = self.get_choice_input(
            kwarg_label="peak_profile",
            state=state,
            label="Peak Profile",
            help_str="""The shape factor K, also known as the “Scherrer constant” is a dimensionless 
        quantity to obtain an actual particle size from an apparent particle size determined from XRD. The discrepancy is 
        because the shape of an individual crystallite will change the resulting diffraction broadening. Commonly, a value 
        of 0.94 for isotropic crystals in a spherical shape is used. However, in practice K can vary from 0.62 to 2.08.""",
            options=[
                {"label": "Gaussian", "value": "G"},
                {"label": "Lorentzian", "value": "L"},
                {"label": "Voigt", "value": "V"},
            ],
        )

        # 2Theta or Q for x-axis
        x_axis_choice = self.get_choice_input(
            kwarg_label="x_axis",
            state=state,
            label="Choice of 𝑥 axis",
            help_str="Can choose between 2𝜃 or Q, where Q is the magnitude of the reciprocal lattice and "
            "independent of radiation source.",  # TODO: improve
            options=[
                {"label": "2𝜃", "value": "twotheta"},
                {"label": "Q", "value": "Q"},
            ],
        )

        # Crystallite size selector (via Scherrer Equation)
        crystallite_size = self.get_slider_input(
            kwarg_label="crystallite_size",
            label="Scherrer crystallite size / nm",
            state=state,
            help_str="...",
            marks={i: "{}".format(10 ** i) for i in range(-1, 3)},
            min=-1,
            max=2,
            step=0.01,
        )

        return {
            "x_axis": x_axis_choice,
            "graph": graph,
            "rad_source": rad_source,
            "peak_profile": peak_profile,
            "shape_factor": shape_factor,
            "crystallite_size": crystallite_size,
        }

    def layout(self):
        return Columns(
            [
                Column([self._sub_layouts["graph"]], size=8, style={"height": "600px"}),
                Column(
                    [
                        self._sub_layouts["x_axis"],
                        self._sub_layouts["rad_source"],
                        self._sub_layouts["shape_factor"],
                        self._sub_layouts["peak_profile"],
                        self._sub_layouts["crystallite_size"],
                    ],
                    size=4,
                ),
            ]
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("xrd-plot"), "figure"),
            [
                Input(self.id(), "data"),
                Input(self.get_kwarg_id("crystallite_size"), "value"),
                Input(self.get_kwarg_id("rad_source"), "value"),
                Input(self.get_kwarg_id("peak_profile"), "value"),
                Input(self.get_kwarg_id("shape_factor"), "value"),
                Input(self.get_kwarg_id("x_axis"), "value"),
            ],
        )
        def update_graph(data, logsize, rad_source, peak_profile, K, x_axis):

            if not data:
                raise PreventUpdate

            kwargs = self.reconstruct_kwargs_from_state(callback_context.inputs)

            if not kwargs:
                raise PreventUpdate

            peak_profile = kwargs["peak_profile"]
            K = kwargs["shape_factor"]
            rad_source = kwargs["rad_source"]
            logsize = kwargs["crystallite_size"]

            x_peak = data["x"]
            y_peak = data["y"]
            d_hkls = data["d_hkls"]
            grain_size = 10 ** logsize

            hkl_list = [hkl[0]["hkl"] for hkl in data["hkls"]]
            hkls = [
                "hkl: (" + " ".join([str(i) for i in hkl]) + ")" for hkl in hkl_list
            ]  # convert to (h k l) format

            annotations = [
                f"2𝜃: {round(peak_x,3)}<br>Intensity: {round(peak_y,3)}<br>{hkl} <br>d: {round(d, 3)}"
                for peak_x, peak_y, hkl, d in zip(x_peak, y_peak, hkls, d_hkls)
            ]  # text boxes

            first = x_peak[0]
            last = x_peak[-1]
            domain = last - first  # find total domain of angles in pattern
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

            layout = self.default_xrd_plot_style

            if kwargs["x_axis"] == "Q":
                x_peak = self.twotheta_to_q(x_peak, WAVELENGTHS[rad_source])
                x = self.twotheta_to_q(x, WAVELENGTHS[rad_source])
                layout["xaxis"]["title"] = "Q / Å⁻¹"
            else:
                layout["xaxis"]["title"] = "2𝜃 / º"
            layout["xaxis"]["range"] = [min(x), max(x)]
            bar_width = 0.003 * (
                max(x) - min(x)
            )  # set width of bars to 0.5% of the domain

            plotdata = [
                go.Bar(
                    x=x_peak,
                    y=y_peak,
                    width=[bar_width] * length,
                    hoverinfo="text",
                    text=annotations,
                    opacity=0.8,
                    marker={"color": "black"},
                ),
                go.Scatter(x=x, y=y, hoverinfo="none"),
            ]
            plot = go.Figure(data=plotdata, layout=layout)

            return plot

        @app.callback(
            Output(self.id(), "data"),
            [
                Input(self.id("struct"), "data"),
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
            struct = (
                sga.get_conventional_standard_structure()
            )  # always get conventional structure

            xrdc = XRDCalculator(
                wavelength=WAVELENGTHS[rad_source], symprec=0, debye_waller_factors=None
            )
            data = xrdc.get_pattern(struct, two_theta_range=None)

            return data.as_dict()


class DiffractionPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xrd = XRayDiffractionComponent(links={"struct": self.id()})
        self.tem = TEMDiffractionComponent(links={"default": self.id()})

    @property
    def title(self):
        return "Diffraction Pattern"

    @property
    def description(self):
        return (
            "Display powder or single crystal diffraction patterns for this structure."
        )

    def contents_layout(self) -> html.Div:

        state = {"mode": "powder"}

        # mode selector
        mode = self.get_choice_input(
            kwarg_label="mode",
            state=state,
            label="Mode",
            help_str="""Select whether to generate a powder diffraction pattern 
        (a pattern averaged over all orientations of a polycrystalline material) 
        or a single crystal diffraction pattern (a diffraction pattern generated 
        from a single crystal structure.""",
            options=[
                {"value": "powder", "label": "Powder"},
                {"value": "single", "label": "Single Crystal"},
            ],
        )

        return html.Div([Columns(Column(mode)), self.xrd.layout()])
