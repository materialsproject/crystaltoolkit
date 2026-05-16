from __future__ import annotations

import warnings
from importlib.metadata import version
from typing import TYPE_CHECKING

import dash_mp_components as mpc
from dash.dependencies import Component, Input, Output
from dash.exceptions import PreventUpdate
from lobsterpy.plotting import InteractiveCohpPlotter
from plotly.subplots import make_subplots
from pymatgen.electronic_structure.dos import LobsterCompleteDos

from crystal_toolkit.components.bandstructure import BandstructureAndDosComponent
from crystal_toolkit.components.localenv import (
    _get_lobsterenv_inputs,
    _perform_lobsterenv_analysis,
)
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import (
    H4,
    H5,
    Column,
    Columns,
    Loading,
    MessageBody,
    MessageContainer,
    cite_me,
    dcc,
    html,
)

if TYPE_CHECKING:
    import plotly.graph_objects as go
    from pymatgen.core import Structure
    from pymatgen.io.lobster import Charge, Icohplist

warnings.filterwarnings("ignore")


class CohpAndDosComponent(MPComponent):
    def __init__(
        self,
        mpid: str | None = None,
        density_of_states: LobsterCompleteDos | None = None,
        cohp_plot_data: dict | None = None,
        lobsterpy_text_description: dict | None = None,
        calc_quality_description: str | None = None,
        obj_charge: Charge | None = None,
        obj_icohp: Icohplist | None = None,
        structure: Structure | None = None,
        id: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            id=id,
            default_data={
                "mpid": mpid,
                "density_of_states": density_of_states,
                "cohp_plot_data": cohp_plot_data,
                "lobsterpy_text_description": lobsterpy_text_description,
                "calc_quality_description": calc_quality_description,
                "obj_charge": obj_charge,
                "obj_icohp": obj_icohp,
                "structure": structure,
            },
            **kwargs,
        )

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        (
            density_of_states,
            cohp_plot_data,
            lobsterpy_text_description,
            calc_quality_description,
        ) = CohpAndDosComponent._get_plot_inputs(self.initial_data["default"])

        fig = CohpAndDosComponent.get_figure(
            dos=density_of_states,
            cohp_plot_data=cohp_plot_data,
        )

        # Main plot
        graph = html.Div(
            [
                dcc.Graph(
                    figure=fig,
                    config={"displayModeBar": False},
                    responsive=True,
                    style={"width": "100%"},
                )
            ],
            id=self.id("cohp-dos-graph"),
        )

        # COHP/DOS plot controls
        analysis_options = [
            {"label": "all", "value": "all"},
            {"label": "cation-anion", "value": "cation-anion"},
        ]

        analysis_mode = html.Div(
            [
                self.get_choice_input(
                    kwarg_label="analysis-mode",
                    state={"analysis-mode": "all"},
                    label="Bonds summary mode",
                    help_str="Summary mode to choose from",
                    options=analysis_options,
                )
            ],
            style={"width": "200px"},
            id=self.id("options-container"),
        )

        # LobsterEnv-specific controls
        lobsterenv_state = {
            "lobsterenv-analysis-mode": "all",
            "perc_strength_icohp": 0.15,
            "which_charge": "Mulliken",
            "adapt_extremum": True,
            "noise_cutoff": 1e-3,
        }

        lobsterenv_analysis_options = [
            {"label": "all", "value": "all"},
            {"label": "cation-anion", "value": "cation-anion"},
        ]

        lobsterenv_analysis_mode = self.get_choice_input(
            kwarg_label="lobsterenv-analysis-mode",
            state=lobsterenv_state,
            label="Analysis mode",
            help_str="Choose whether to analyze all bonds or only cation-anion bonds",
            options=lobsterenv_analysis_options,
        )

        charge_type_options = [
            {"label": "Mulliken", "value": "Mulliken"},
            {"label": "Loewdin", "value": "Loewdin"},
        ]

        charge_type = self.get_choice_input(
            kwarg_label="which_charge",
            state=lobsterenv_state,
            label="Charge type",
            help_str="Select the atomic charge type to use for the cation-anion classification",
            options=charge_type_options,
        )

        icohp_cutoff = html.Div(
            [
                H5("ICOHP cutoff %"),
                dcc.Slider(
                    id=self.id("perc_strength_icohp"),
                    min=0,
                    max=1,
                    step=0.01,
                    value=0.15,
                    marks={i: f"{i:.0%}" for i in [0, 0.25, 0.5, 0.75, 1]},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ],
            style={"width": "100%"},
        )

        adapt_extremum = self.get_bool_input(
            label="Adapt extremum to additional condition",
            kwarg_label="adapt_extremum",
            state=lobsterenv_state,
            help_str="If enabled, adapts the ICOHP extremum based on additional conditions (cation-anion mode)",
        )

        noise_cutoff = self.get_numerical_input(
            label="Noise cutoff",
            kwarg_label="noise_cutoff",
            state=lobsterenv_state,
            help_str="Noise cutoff threshold for filtering small bond strength values",
            shape=(),
            min=0.0,
        )

        lobsterenv_controls = Columns(
            [
                Column([lobsterenv_analysis_mode, charge_type], size=3),
                Column([icohp_cutoff], size=3),
                Column([adapt_extremum, noise_cutoff], size=3),
            ]
        )

        # LobsterEnv analysis view container
        lobsterenv_analysis = Loading(
            id=self.id("lobsterenv_analysis"),
            children=mpc.Markdown(
                "Local environment analysis will appear here when LOBSTER data is available."
            ),
        )

        analysis_description = lobsterpy_text_description.get("all")

        lobsterpy_version = version("lobsterpy")

        repo_link = html.A(
            f"LobsterPy v{lobsterpy_version}",
            href="https://github.com/JaGeo/LobsterPy.git",
            style={"white-space": "nowrap"},
        )

        analysis_description_div = html.Div(
            [
                MessageContainer(
                    MessageBody(
                        [f"{analysis_description} - ", repo_link],
                    ),
                    kind="dark",
                    size="normal",
                ),
            ],
            id=self.id("analysis-description"),
            # style={"position": "relative"}
        )

        calc_quality_description_div = html.Div(
            [
                MessageContainer(
                    MessageBody(
                        [f"{calc_quality_description}"],
                    ),
                    kind="info",
                    size="normal",
                )
            ],
            id=self.id("calc-quality-description"),
            # style={"position": "relative"}
        )

        return {
            "graph": graph,
            "analysis-mode": analysis_mode,
            "lobsterenv-controls": lobsterenv_controls,
            "lobsterenv-analysis": lobsterenv_analysis,
            "analysis-description": analysis_description_div,
            "calc-quality-description": calc_quality_description_div,
        }

    def layout(self):
        """Return the layout of the component."""
        # Get the sub-layouts
        # and create the main layout
        sub_layouts = self._sub_layouts

        graph = sub_layouts["graph"]

        controls = Columns(
            [
                Column(
                    [
                        sub_layouts["analysis-mode"],
                    ]
                )
            ]
        )

        # Create the description div
        description_header = H4(
            "Bonding analysis summary",
            id=self.id("summary_text"),
            style={"display": "inline-block"},
        )

        description_div = Columns([Column([sub_layouts["analysis-description"]])])

        calc_quality_header = H4(
            "Calculation quality",
            id=self.id("calc-quality-text"),
            style={"display": "inline-block"},
        )
        calc_quality_div = Columns([Column([sub_layouts["calc-quality-description"]])])

        lobsterenv_header = H4(
            "Local environment analysis (LobsterEnv)",
            id=self.id("lobsterenv_text"),
            style={"display": "inline-block"},
        )

        lobsterenv_description = dcc.Markdown(
            "The LobsterEnv algorithm is developed by George et al. to analyze "
            "local chemical environments based on the outputs of LOBSTER calculations. "
            "This analysis relies on the ICOHP values calculated by LOBSTER, which "
            "are a measure of bond strength. The local environment is determined by including all neighbors "
            "with ICOHP values stronger than a certain threshold. "
            "The threshold can be set as a percentage of the strongest ICOHP in the structure, and can be adjusted using the slider below. "
        )

        lobsterenv_citation = cite_me(
            doi="10.1002/cplu.202200123",
            cite_text="How to cite LobsterEnv",
        )

        lobsterenv_div = Columns([Column([sub_layouts["lobsterenv-analysis"]])])

        return Column(
            [
                controls,
                graph,
                html.Br(),
                description_header,
                description_div,
                calc_quality_header,
                calc_quality_div,
                html.Br(),
                lobsterenv_header,
                lobsterenv_description,
                html.Br(),
                lobsterenv_citation,
                html.Br(),
                sub_layouts["lobsterenv-controls"],
                html.Br(),
                lobsterenv_div,
            ]
        )

    @staticmethod
    def _get_plot_inputs(
        data: dict | None,
    ) -> tuple[LobsterCompleteDos, dict, dict, str] | tuple[None, None, None, None]:
        data = data or {}

        density_of_states = data.get("density_of_states")
        cohp_plot_data = data.get("cohp_plot_data")
        lobsterpy_text_description = data.get("lobsterpy_text_description")
        calc_quality_description = data.get("calc_quality_description")

        if density_of_states and isinstance(density_of_states, dict):
            density_of_states = LobsterCompleteDos.from_dict(density_of_states)

        return (
            density_of_states,
            cohp_plot_data,
            lobsterpy_text_description,
            calc_quality_description,
        )

    @staticmethod
    def get_figure(
        dos,
        cohp_plot_data,
        dos_select="ap",
        energy_window=(-10.0, 5.0),
        which_bonds="all",
        **kwargs,
    ) -> go.Figure:
        """Get a COHP figure.

        Args:
            charge_obj:  pymatgen lobster.io.charge object.
            completecohp_obj: pymatgen.electronic_structure.cohp.CompleteCohp object
            icohplist_obj: pymatgen lobster.io.Icohplist object
            madelung_obj: pymatgen lobster.io.MadelungEnergies object
            kwargs: Keyword arguments that get passed to InteractiveCohpPlotter.get_plot.

        Returns:
            A plotly Figure object.
        """

        cohp_plotter = InteractiveCohpPlotter(are_cobis=False, are_coops=False)

        # Get the COHP plot
        cohp_plotter.add_cohps_from_plot_data(cohp_plot_data.get(which_bonds))
        cohp_fig = cohp_plotter.get_plot(
            ylim=[-10, 5],
            xlim=[-5, 5],
        )

        dos_traces = BandstructureAndDosComponent.get_dos_traces(
            dos=dos, energy_window=energy_window, dos_select=dos_select
        )

        fig = make_subplots(
            rows=1,
            cols=2,
            shared_yaxes=True,
            horizontal_spacing=0.05,
            column_widths=[0.6, 0.4],
        )

        # Adapt traces names and formatting to crystal-toolkit style
        for ix, trace in enumerate(cohp_fig.data):
            trace.visible = True
            trace.line.width = None
            if trace.line.dash:
                trace.line.dash = "dot"
            if trace.line.dash != "dot":
                trace.name = f"{cohp_fig.data[ix].name} (spin ↑)"
                legend_spin_down_name = trace.name.split(" (")
                cohp_fig.data[ix + 1].name = f"{legend_spin_down_name[0]} (spin ↓)"

            fig.add_trace(trace, row=1, col=1)

        for trace in dos_traces:
            fig.add_trace(trace, row=1, col=2)

        # Update axes layout to match Crystal Toolkit's aesthetic
        fig.update_layout(
            xaxis1=dict(
                title="COHP (eV)",
                range=[-5, 5],
                showgrid=False,
                linecolor="rgb(71,71,71)",
                mirror=True,
                domain=[0, 0.62],  # 60% width for COHP
            ),
            xaxis2=dict(
                title="DOS",
                showgrid=False,
                linecolor="rgb(71,71,71)",
                mirror=True,
                domain=[0.65, 1],  # 35% width for DOS
            ),
            yaxis=dict(
                title="E - E<sub>F</sub> (eV)",
                range=[-10, 5],
                showgrid=False,
                linecolor="rgb(71,71,71)",
                mirror=True,
            ),
            yaxis2=dict(
                range=[-10, 5], showgrid=False, linecolor="rgb(71,71,71)", mirror=True
            ),
            hovermode="closest",
            plot_bgcolor="rgba(230,230,230,230)",
            margin=dict(l=60, b=50, t=50, pad=0, r=30),
            # height=500,
            # width=1000,
            autosize=True,
            showlegend=True,
        )

        legend = dict(
            x=1.02,
            y=1.005,
            xanchor="left",
            yanchor="top",
            bordercolor="#333",
            borderwidth=2,
            traceorder="normal",
        )

        fig["layout"]["legend"] = legend

        return fig

    def generate_callbacks(self, app, cache) -> None:
        """Register callback functions for this component."""

        @app.callback(
            Output(self.id("cohp-dos-graph"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("analysis-mode"), "value"),
        )
        def update_graph(data, label_select):
            """Update the COHP and DOS graph."""

            # Get the data from the store
            (
                density_of_states,
                cohp_plot_data,
                _lobsterpy_text_description,
                _calc_quality_description,
            ) = self._get_plot_inputs(data)

            fig = self.get_figure(
                density_of_states,
                cohp_plot_data,
                which_bonds=label_select
                if isinstance(label_select, str)
                else label_select[0],
            )

            return dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={"width": "100%"},
            )

        @app.callback(
            Output(self.id("analysis-description"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("analysis-mode"), "value"),
        )
        def update_text(data, label_select) -> MessageContainer:
            """Update the text description of the bonding analysis."""
            (
                _density_of_states,
                _cohp_plot_data,
                lobsterpy_text_description,
                _calc_quality_description,
            ) = self._get_plot_inputs(data)

            which_bonds = (
                label_select if isinstance(label_select, str) else label_select[0]
            )
            analysis_description = lobsterpy_text_description.get(which_bonds)

            lobsterpy_version = version("lobsterpy")

            repo_link = html.A(
                f"LobsterPy v{lobsterpy_version}",
                href="https://github.com/JaGeo/LobsterPy.git",
                style={"white-space": "nowrap"},
            )

            return MessageContainer(
                MessageBody([f"{analysis_description} - ", repo_link]),
                kind="dark",
                size="normal",
            )

        @app.callback(
            Output(self.id("lobsterenv_analysis"), "children"),
            Input(self.id(), "data"),
            Input(self.id("perc_strength_icohp"), "value"),
            Input(self.get_kwarg_id("lobsterenv-analysis-mode"), "value"),
            Input(self.get_kwarg_id("which_charge"), "value"),
            Input(self.get_kwarg_id("adapt_extremum"), "value"),
            Input(self.get_kwarg_id("noise_cutoff"), "value"),
        )
        def get_lobsterenv_analysis(
            data,
            perc_strength_icohp,
            analysis_mode,
            which_charge,
            adapt_extremum,
            noise_cutoff,
        ):
            """Generate LobsterEnv local environment analysis."""
            if not data:
                raise PreventUpdate

            # Handle slider value
            if isinstance(perc_strength_icohp, list):
                perc_strength_icohp = (
                    float(perc_strength_icohp[0]) if perc_strength_icohp else 0.15
                )
            else:
                perc_strength_icohp = (
                    float(perc_strength_icohp)
                    if perc_strength_icohp is not None
                    else 0.15
                )

            # Handle charge type
            which_charge = (
                which_charge[0]
                if isinstance(which_charge, list)
                else (which_charge or "Mulliken")
            )

            # Handle adapt_extremum
            adapt_extremum = (
                adapt_extremum[0]
                if isinstance(adapt_extremum, list)
                else (adapt_extremum if adapt_extremum is not None else True)
            )

            # Handle noise_cutoff
            noise_cutoff = (
                float(noise_cutoff[0])
                if isinstance(noise_cutoff, list)
                else (float(noise_cutoff) if noise_cutoff is not None else 1e-3)
            )

            try:
                struct, obj_icohp, obj_charge = _get_lobsterenv_inputs(data)
            except ValueError as e:
                return mpc.Markdown(str(e))

            if (
                not isinstance(data, dict)
                or "obj_icohp" not in data
                or "obj_charge" not in data
            ):
                return mpc.Markdown(
                    "LobsterEnv requires LOBSTER outputs (ICOHP + charge data). "
                    "Please provide `obj_icohp` and `obj_charge` in the component data."
                )

            # Determine if we should only show cation-anion bonds
            only_cation_anion = (
                analysis_mode == "cation-anion"
                if isinstance(analysis_mode, str)
                else analysis_mode[0] == "cation-anion"
            )

            try:
                return _perform_lobsterenv_analysis(
                    struct,
                    obj_icohp,
                    obj_charge,
                    perc_strength_icohp,
                    which_charge,
                    only_cation_anion,
                    adapt_extremum,
                    noise_cutoff,
                )
            except ValueError as e:
                return mpc.Markdown(str(e))


class COHPAndDosPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cohp = CohpAndDosComponent()
        self.cohp.attach_from(self, this_store_name="mpid")

    @property
    def title(self) -> str:
        return "COHP and Density of States"

    @property
    def description(self) -> str:
        return "Display the COHP and density of states for this structure \
        if it has been calculated by the Materials Project."

    @property
    def initial_contents(self) -> html.Div:
        return html.Div(
            [
                super().initial_contents,
                html.Div([self.cohp.standard_layout], style={"display": "none"}),
            ]
        )

    def update_contents(self, new_store_contents, *args) -> html.Div:
        return self.cohp.standard_layout
