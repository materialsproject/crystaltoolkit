from __future__ import annotations

import typing

from dash import Output, Input

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import Loading, dcc, html

if typing.TYPE_CHECKING:
    from ifermi.surface import FermiSurface
    from plotly.graph_objs import Figure


class FermiSurfaceComponent(MPComponent):
    """
    Component to display FermiSurface objects generated from ifermi.

    Args:
        fermi_surface: An ifermi FermiSurface object.
        id: A unique id, required if multiple of the same type of MPComponent are
            included in an app.
        kwargs: Keyword arguments that get passed to MPComponent.
    """

    def __init__(
        self,
        fermi_surface: FermiSurface = None,
        id: str | None = None,
        **kwargs,
    ):
        super().__init__(id=id, default_data=fermi_surface, **kwargs)

    @staticmethod
    def get_figure(fermi_surface: FermiSurface) -> Figure:
        """
        Get a fermi surface figure.

        Args:
            fermi_surface: An ifermi FermiSurface object.

        Returns:
            A plotly Figure object.
        """
        from ifermi.plot import FermiSurfacePlotter

        plotter = FermiSurfacePlotter(fermi_surface)
        fig = plotter.get_plot(plot_type="plotly")

        # ensure the plot has a transparent background
        fig.layout["paper_bgcolor"] = "rgba(0,0,0,0)"
        fig.layout["plot_bgcolor"] = "rgba(0,0,0,0)"
        fig.layout["scene"]["xaxis"]["backgroundcolor"] = "rgba(0,0,0,0)"
        fig.layout["scene"]["yaxis"]["backgroundcolor"] = "rgba(0,0,0,0)"
        fig.layout["scene"]["zaxis"]["backgroundcolor"] = "rgba(0,0,0,0)"

        # remove mouseover grid
        fig.layout["scene"]["xaxis"]["showspikes"] = False
        fig.layout["scene"]["yaxis"]["showspikes"] = False
        fig.layout["scene"]["zaxis"]["showspikes"] = False
        for data in fig.data:
            data["hoverinfo"] = "skip"

        # remove LaTeX from high-symmetry labels
        str_replace = {
            "$": "",
            "\\mid": "|",
            "\\Gamma": "Γ",
            "\\Sigma": "Σ",
            "GAMMA": "Γ",
            "_1": "₁",
            "_2": "₂",
            "_3": "₃",
            "_4": "₄",
            "_{1}": "₁",
            "_{2}": "₂",
            "_{3}": "₃",
            "_{4}": "₄",
            "^{*}": "*",
        }
        for label in fig.layout["scene"]["annotations"]:
            for find, replace in str_replace.items():
                label["text"] = label["text"].replace(find, replace)

        return fig

    def layout(self) -> html.Div:
        """Get a Dash layout for the component."""
        if initial_data := self.initial_data["default"]:
            figure = self.get_figure(initial_data)
        else:
            figure = None

        # id allows for callbacks
        return html.Div(
            [
                Loading(
                    [
                        dcc.Graph(
                            id=self.id("fermi-surface-graph"),
                            figure=figure,
                            config={"displayModeBar": False},
                            responsive=True,
                        )
                    ],
                    id=self.id("fermi-surface-div"),
                )
            ]
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("fermi-surface-graph"), "figure"), Input(self.id(), "data")
        )
        def update_plot(fermi_surface):
            # if update_plot is slow, an @cache decorator can be added here
            fermi_surface = self.from_data(fermi_surface)  # converts back to object
            return self.get_figure(fermi_surface)
