from __future__ import annotations

import typing

import matplotlib.pyplot as plt
from dash import Input, Output

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import Box, Column, Columns, Loading, dcc

if typing.TYPE_CHECKING:
    from dash.development.base_component import Component
    from ifermi.surface import FermiSurface
    from plotly.graph_objects import Figure


class FermiSurfaceComponent(MPComponent):
    """Component to display FermiSurface objects generated from ifermi.

    Args:
        fermi_surface: An ifermi FermiSurface object.
        id: A unique id, required if multiple of the same type of MPComponent are
            included in an app.
        kwargs: Keyword arguments that get passed to MPComponent.
    """

    def __init__(
        self,
        fermi_surface: FermiSurface | None = None,
        id: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(id=id, default_data=fermi_surface, **kwargs)

    @staticmethod
    def get_figure(fermi_surface: FermiSurface, **kwargs) -> Figure:
        """Get a fermi surface figure.

        Args:
            fermi_surface: An ifermi FermiSurface object.
            kwargs: Keyword arguments that get passed to FermiSurfacePlotter.get_plot.

        Returns:
            A plotly Figure object.
        """
        from ifermi.plot import FermiSurfacePlotter

        plotter = FermiSurfacePlotter(fermi_surface)
        fig = plotter.get_plot(plot_type="plotly", **kwargs)

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

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        if fermi_surface := self.initial_data["default"]:
            figure = self.get_figure(fermi_surface, color_properties=False)
        else:
            figure = None

        state = {
            "show_cell": True,
            "show_labels": True,
            "color_properties": False,
        }

        graph = Loading(
            [
                dcc.Graph(
                    id=self.id("fermi-surface-graph"),  # id allows for callbacks
                    figure=figure,
                    config={"displayModeBar": False},
                    responsive=True,
                )
            ],
            id=self.id("fermi-surface-div"),
        )

        show_cell = self.get_bool_input(
            "show_cell",
            state=state,
            label="Show Brillouin zone edges",
            help_str="Show the edges of the Brillouin zone.",
        )

        show_labels = self.get_bool_input(
            "show_labels",
            state=state,
            label="Show high-symmetry labels",
            help_str="Show the labels for high-symmetry points in the Brillouin zone.",
        )

        options = [{"label": "None", "value": False}]
        if fermi_surface is not None and fermi_surface.has_properties:
            options += [{"label": key, "value": key} for key in plt.colormaps()]
        color_properties = self.get_choice_input(
            kwarg_label="color_properties",
            state=state,
            label="Property colormap",
            help_str="Colormap to use if the Fermi surface has properties (such as "
            "group velocity) included",
            options=options,
            style={"width": "10rem"},
        )

        return {
            "graph": graph,
            "show_cell": show_cell,
            "show_labels": show_labels,
            "color_properties": color_properties,
        }

    def layout(self) -> Component:
        """Get a Dash layout for the component."""
        layouts = self._sub_layouts

        return Columns(
            [
                Column(
                    [Box([layouts["graph"]], style={"height": "480px"})],
                    size=8,
                    style={"height": "600px"},
                ),
                Column(
                    [
                        layouts["show_cell"],
                        layouts["show_labels"],
                        layouts["color_properties"],
                    ],
                    size=4,
                ),
            ]
        )

    def generate_callbacks(self, app, cache) -> None:
        @app.callback(
            Output(self.id("fermi-surface-graph"), "figure"),
            Input(self.id(), "data"),
            Input(self.get_all_kwargs_id(), "value"),
        )
        def update_plot(fermi_surface, *args):
            # if update_plot is slow, an @cache decorator can be added here
            fermi_surface = self.from_data(fermi_surface)  # converts back to object
            kwargs = self.reconstruct_kwargs_from_state()

            # invert show_cell and show_labels
            kwargs["hide_cell"] = not kwargs.pop("show_cell")
            kwargs["hide_labels"] = not kwargs.pop("show_labels")

            return self.get_figure(fermi_surface, **kwargs)
