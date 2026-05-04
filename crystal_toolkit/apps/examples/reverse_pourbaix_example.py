"""Example app for the Reverse Pourbaix Diagram Component.

Renders the heatmap statically using the component's `get_heatmap_figure`
staticmethod. No interactivity. See the Materials Project web integration.
"""

from __future__ import annotations

import json
from pathlib import Path

import dash
from dash import dcc, html

import crystal_toolkit.components as ctc
from crystal_toolkit.components.reverse_pourbaix import ReversePourbaixDiagramComponent
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# Load pre-computed heatmap data
DATA_PATH = Path(__file__).parent / "reverse_pourbaix_heatmap.json"

with open(DATA_PATH) as f:
    heatmap_data = json.load(f)

# Build the heatmap figure directly — no component, no callbacks.
figure = ReversePourbaixDiagramComponent.get_heatmap_figure(heatmap_data)

layout = html.Div(
    [
        html.H1("Reverse Pourbaix Diagram"),
        html.P(
            "Number of thermodynamically stable materials at each pH/potential "
            "combination (decomposition energy < 0.2 eV/atom)."
        ),
        dcc.Graph(
            figure=figure,
            config={"displayModeBar": False, "displaylogo": False},
        ),
    ],
    style=dict(maxWidth="900px", margin="2em auto"),
)

ctc.register_crystal_toolkit(app=app, layout=layout)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
