"""Reverse Pourbaix Diagram Component.

Displays a heatmap of the number of thermodynamically stable materials
across pH and potential (V_SHE) space, based on pre-computed Pourbaix
stability data from the Materials Project database.

This is the "reverse" of the standard Pourbaix diagram: instead of showing
stability domains for a single material, it shows how many materials are
stable at each electrochemical condition.

See: Karlsson et al., Electrochimica Acta 549 (2026) 148053
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Component, Input, Output
from dash.exceptions import PreventUpdate
from frozendict import frozendict

from pymatgen.analysis.pourbaix_diagram import PREFAC

from crystal_toolkit.core.mpcomponent import MPComponent

logger = logging.getLogger(__name__)

__author__ = "Leo Karlsson"

# Grid and display constants
HEIGHT = 550
WIDTH = 700
MIN_PH = 0
MAX_PH = 14
MIN_V = -2
MAX_V = 2

class ReversePourbaixDiagramComponent(MPComponent):
    """Component for displaying a reverse Pourbaix diagram.

    Shows a heatmap of the number of stable materials at each pH/V
    combination.
    """

    default_state = frozendict(
        show_water_lines=True,
    )

    default_plot_style = frozendict(
        xaxis={
            "title": "pH",
            "anchor": "y",
            "mirror": "ticks",
            "showgrid": False,
            "showline": True,
            "side": "bottom",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "title": {"font": {"color": "#000000", "size": 24.0}, "text": "pH"},
            "type": "linear",
            "zeroline": False,
            "range": [MIN_PH, MAX_PH],
        },
        yaxis={
            "title": "Potential (V vs. SHE)",
            "anchor": "x",
            "mirror": "ticks",
            "range": [MIN_V, MAX_V],
            "showgrid": False,
            "showline": True,
            "side": "left",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "title": {"font": {"color": "#000000", "size": 24.0}, "text": "Potential (V vs. SHE)"},
            "type": "linear",
            "zeroline": False,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=HEIGHT,
        width=WIDTH,
        hovermode="closest",
        showlegend=False,
        margin=dict(l=80, b=70, t=10, r=20),
    )

    empty_plot_style = frozendict(
        xaxis={"visible": False},
        yaxis={"visible": False},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    @staticmethod
    def get_heatmap_figure(
        heatmap_data: dict,
        show_water_lines: bool = True,
        selected_ph: float | None = None,
        selected_v: float | None = None,
    ) -> go.Figure:
        """Generate a Plotly heatmap figure from pre-computed data.

        Args:
            heatmap_data: dict with keys 'ph_values', 'v_values', 'grid'
            grid is a list of {'pH': float, 'V': float, 'count': int}
            show_water_lines: if True, show HER/OER stability lines
            selected_ph: pH value of selected cell (for highlight)
            selected_v: V value of selected cell (for highlight)

        Returns:
            go.Figure with the heatmap
        """
        ph_values = heatmap_data["ph_values"]
        v_values = heatmap_data["v_values"]
        grid = heatmap_data["grid"]

        # Build the Z matrix
        # Create a lookup for fast access
        lookup = {}
        for point in grid:
            lookup[(point["pH"], point["V"])] = point["count"]

        z_matrix = []
        for v in v_values:
            row = []
            for ph in ph_values:
                row.append(lookup.get((ph, v), 0))
            z_matrix.append(row)

        data = []

        # Heatmap trace
        heatmap_trace = go.Heatmap(
            z=z_matrix,
            x=ph_values,
            y=v_values,
            colorscale="Viridis",
            colorbar={"title": "Number of<br>Materials"},
            hovertemplate=(
                "pH: %{x}<br>"
                "V: %{y} V<sub>SHE</sub><br>"
                "Stable materials: %{z}"
                "<extra></extra>"
            ),
        )
        data.append(heatmap_trace)

        # Water stability lines
        if show_water_lines:
            ph_range = [MIN_PH, MAX_PH]

            # Hydrogen evolution line
            data.append(
                go.Scatter(
                    x=ph_range,
                    y=[-ph_range[0] * PREFAC, -ph_range[1] * PREFAC],
                    mode="lines",
                    line={"color": "white", "dash": "dash", "width": 2},
                    name="H₂/H₂O",
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            # Oxygen evolution line
            data.append(
                go.Scatter(
                    x=ph_range,
                    y=[
                        -ph_range[0] * PREFAC + 1.23,
                        -ph_range[1] * PREFAC + 1.23,
                    ],
                    mode="lines",
                    line={"color": "white", "dash": "dash", "width": 2},
                    name="O₂/H₂O",
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        layout = {**ReversePourbaixDiagramComponent.default_plot_style}

        # Add selection rectangle if a cell is selected
        if selected_ph is not None and selected_v is not None:
            # Calculate cell boundaries
            ph_step = ph_values[1] - ph_values[0] if len(ph_values) > 1 else 1
            v_step = abs(v_values[0] - v_values[1]) if len(v_values) > 1 else 0.5

            layout["shapes"] = [
                {
                    "type": "rect",
                    "x0": selected_ph - ph_step / 2,
                    "x1": selected_ph + ph_step / 2,
                    "y0": selected_v - v_step / 2,
                    "y1": selected_v + v_step / 2,
                    "line": {"color": "white", "width": 3},
                    "fillcolor": "rgba(0,0,0,0)",
                }
            ]

        return go.Figure(data=data, layout=layout)

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        graph = html.Div(
            [
                dcc.Graph(
                    figure=go.Figure(
                        layout={**ReversePourbaixDiagramComponent.empty_plot_style}
                    ),
                    responsive=True,
                    config={"displayModeBar": False, "displaylogo": False},
                ),
            ],
            style={"minHeight": "500px"},
            id=self.id("graph-panel"),
        )

        info = html.Div(
            id=self.id("click-info"),
            style={
                "padding": "10px",
                "textAlign": "center",
                "color": "#666",
            },
            children="Click on the heatmap to explore stable materials at a specific condition.",
        )

        options = html.Div(
            [
                self.get_bool_input(
                    "show_water_lines",
                    default=self.default_state["show_water_lines"],
                    label="Show Water Stability Lines",
                    help_str="Show the hydrogen and oxygen evolution reaction lines.",
                ),
            ]
        )

        return {"graph": graph, "info": info, "options": options}

    def layout(self) -> html.Div:
        """Return the full component layout."""
        return html.Div(
            children=[
                self._sub_layouts["options"],
                self._sub_layouts["graph"],
                self._sub_layouts["info"],
            ]
        )

    def generate_callbacks(self, app, cache) -> None:
        """Register Dash callbacks for interactivity."""

        @app.callback(
            Output(self.id("graph-panel"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("show_water_lines"), "value"),
        )
        def update_figure(heatmap_json, show_water_lines):
            if not heatmap_json:
                raise PreventUpdate

            heatmap_data = self.from_data(heatmap_json)

            kwargs = self.reconstruct_kwargs_from_state()
            show_water_lines = kwargs.get("show_water_lines", True)

            figure = self.get_heatmap_figure(
                heatmap_data,
                show_water_lines=show_water_lines,
            )

            return dcc.Graph(
                figure=figure,
                responsive=True,
                config={"displayModeBar": False, "displaylogo": False},
            )
