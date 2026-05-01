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

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import pyarrow.parquet as pq
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

# Stability cutoff (eV/atom) — the recommended practical value is 0.2,
# matching the metastability threshold used in Karlsson et al. and the
# upstream MP/Sun/Aykol references.
DEFAULT_CUTOFF = 0.2
CUTOFF_RANGE = [0.1, 0.5]
CUTOFF_STEP = 0.1

def _resolve_cutoff(value) -> float:
    """Unwrap a slider value (which may be a list) to a float, falling back
    to the default cutoff."""
    if isinstance(value, list):
        value = value[0] if value else DEFAULT_CUTOFF
    if value is None:
        return DEFAULT_CUTOFF
    return float(value)


def _snap_to_grid(ph: float, v: float) -> tuple[int, float]:
    """Snap a clicked (pH, V) point to the precomputed grid keys."""
    return int(round(ph)), round(v * 2) / 2


class ReversePourbaixDiagramComponent(MPComponent):
    """Component for displaying a reverse Pourbaix diagram.

    Shows a heatmap of the number of stable materials at each pH/V
    combination, where stability is defined by a user-tunable
    decomposition energy cutoff (eV/atom). Clicking on a cell exposes
    the list of mp_ids stable at that condition for downstream use.
    """

    default_state = frozendict(
        show_water_lines=True,
        stability_cutoff=DEFAULT_CUTOFF,
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

    def __init__(self, parquet_path: str | Path | None = None, *args, **kwargs):
        """
        Args:
            parquet_path: path to the precomputed (pH, V, mp_id, decomposition_energy)
                parquet file. Loaded once at component construction. If None, the
                click-to-list functionality is disabled but the heatmap still works.
        """
        super().__init__(*args, **kwargs)
        self._stability_df: pd.DataFrame | None = None
        if parquet_path is not None:
            logger.info("Loading reverse-Pourbaix stability data from %s", parquet_path)
            df = pq.read_table(parquet_path).to_pandas()
            # Index by (pH, V) for fast cell-click lookups.
            self._stability_df = df.set_index(["pH", "V"]).sort_index()
            logger.info(
                "Loaded %d stability rows across %d cells",
                len(df),
                self._stability_df.index.nunique(),
            )

    @staticmethod
    def _format_cutoff_key(cutoff: float) -> str:
        """Format a cutoff float to match the JSON key convention.

        JSON keys are stored as e.g. "0.1", "0.2" — i.e. one decimal.
        """
        return f"{cutoff:.1f}"

    def get_stable_mp_ids(self, ph: float, v: float, cutoff: float) -> list[str]:
        """Return mp_ids stable at (pH, V) below the given decomposition-energy cutoff.

        Returns an empty list if the parquet data is not loaded.
        """
        if self._stability_df is None:
            return []
        ph_key, v_key = _snap_to_grid(ph, v)
        try:
            cell = self._stability_df.loc[(ph_key, v_key)]
        except KeyError:
            logger.debug("No stability data for (pH=%s, V=%s)", ph_key, v_key)
            return []
        stable = cell[cell["decomposition_energy"] <= cutoff]
        return stable["mp_id"].tolist()

    @staticmethod
    def get_heatmap_figure(
        heatmap_data: dict[str, Any],
        stability_cutoff: float = DEFAULT_CUTOFF,
        show_water_lines: bool = True,
        selected_ph: float | None = None,
        selected_v: float | None = None,
    ) -> go.Figure:
        """Generate a Plotly heatmap figure from pre-computed data."""
        ph_values = heatmap_data["ph_values"]
        v_values = heatmap_data["v_values"]
        grid = heatmap_data["grid"]

        cutoff_key = ReversePourbaixDiagramComponent._format_cutoff_key(stability_cutoff)

        lookup: dict[tuple[float, float], int] = {
            (point["pH"], point["V"]): point["counts"][cutoff_key] for point in grid
        }

        z_matrix = [
            [lookup.get((ph, v), 0) for ph in ph_values] for v in v_values
        ]

        data: list[go.BaseTraceType] = []

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

        if show_water_lines:
            ph_range = [MIN_PH, MAX_PH]
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
            data.append(
                go.Scatter(
                    x=ph_range,
                    y=[-ph_range[0] * PREFAC + 1.23, -ph_range[1] * PREFAC + 1.23],
                    mode="lines",
                    line={"color": "white", "dash": "dash", "width": 2},
                    name="O₂/H₂O",
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        layout = {**ReversePourbaixDiagramComponent.default_plot_style}

        if selected_ph is not None and selected_v is not None:
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
                    id=self.id("heatmap"),
                    figure=go.Figure(
                        layout={**ReversePourbaixDiagramComponent.empty_plot_style}
                    ),
                    responsive=True,
                    config={"displayModeBar": False, "displaylogo": False},
                ),
            ],
            #style={"minHeight": "500px"},
            id=self.id("graph-panel"),
        )

        # Holds the list of mp_ids stable at the most recently clicked cell.
        # Downstream callbacks (filtering, table rendering, etc.) can read this.
        mp_id_store = dcc.Store(id=self.id("stable-mp-ids"), data=[])

        # Selection panel — mirrors the panel structure the app uses for
        # Options so they render identically when stacked. The click callback
        # writes to the inner content div (id "click-info"); the outer panel
        # chrome is static.
        info = html.Div(
            [
                html.Div("Selected conditions", className="panel-heading"),
                html.Div(
                    "Click on the heatmap to see the list of stable materials "
                    "at those conditions.",
                    id=self.id("click-info"),
                    className="panel-block is-block",
                ),
            ],
            className="panel",
        )

        options = html.Div(
            [
                self.get_bool_input(
                    "show_water_lines",
                    default=self.default_state["show_water_lines"],
                    label="Show Water Stability Lines",
                    help_str=(
                        "Show the hydrogen and oxygen evolution reaction lines. "
                        "Potential scale is SHE."
                    ),
                ),
                self.get_slider_input(
                    kwarg_label="stability_cutoff",
                    default=self.default_state["stability_cutoff"],
                    domain=CUTOFF_RANGE,
                    step=CUTOFF_STEP,
                    label="Stability Cutoff (eV/atom)",
                    help_str=(
                        "Materials with a decomposition energy (G_pbx, distance "
                        "from the Pourbaix hull) below this cutoff are counted as "
                        "stable. The recommended value is 0.2 eV/atom, the "
                        "practical metastability threshold used in Karlsson et al. "
                        "Higher cutoffs include progressively more metastable phases."
                    ),
                ),
            ]
        )

        return {"graph": graph, "info": info, "options": options, "store": mp_id_store}

    def layout(self) -> html.Div:
        """Return the full component layout."""
        return html.Div(
            children=[
                self._sub_layouts["options"],
                self._sub_layouts["graph"],
                self._sub_layouts["store"],
                self._sub_layouts["info"],
            ]
        )

    def generate_callbacks(self, app, cache) -> None:
        """Register Dash callbacks for interactivity."""

        @app.callback(
            Output(self.id("graph-panel"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("show_water_lines"), "value"),
            Input(self.get_kwarg_id("stability_cutoff"), "value"),
        )
        def update_figure(heatmap_json, show_water_lines, stability_cutoff):
            if not heatmap_json:
                raise PreventUpdate

            heatmap_data = self.from_data(heatmap_json)

            if isinstance(show_water_lines, list):
                show_water_lines = show_water_lines[0] if show_water_lines else True

            figure = self.get_heatmap_figure(
                heatmap_data,
                stability_cutoff=_resolve_cutoff(stability_cutoff),
                show_water_lines=bool(show_water_lines),
            )

            return dcc.Graph(
                id=self.id("heatmap"),  # keep stable id so clickData callback can find it
                figure=figure,
                responsive=True,
                config={"displayModeBar": False, "displaylogo": False},
            )