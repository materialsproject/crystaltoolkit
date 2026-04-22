"""Example app for the Reverse Pourbaix Diagram Component.
"""

from __future__ import annotations

import json
from pathlib import Path

import dash
from dash import html

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS
from crystal_toolkit.components.reverse_pourbaix import ReversePourbaixDiagramComponent

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)
app.config["suppress_callback_exceptions"] = True

# Load pre-computed heatmap data
DATA_PATH = Path(__file__).parent / "reverse_pourbaix_heatmap.json"

print(f"Loading heatmap data from: {DATA_PATH}")

with open(DATA_PATH) as f:
    heatmap_data = json.load(f)

print(f"  Grid points: {len(heatmap_data['grid'])}")
print(f"  pH range: {heatmap_data['ph_values'][0]} to {heatmap_data['ph_values'][-1]}")
print(f"  V range: {heatmap_data['v_values'][-1]} to {heatmap_data['v_values'][0]}")

# Create component
reverse_pourbaix_component = ReversePourbaixDiagramComponent(
    default_data=heatmap_data
)

# Layout
layout = html.Div(
    [
        html.H1("Reverse Pourbaix Diagram"),
        html.P(
            "Number of thermodynamically stable materials at each pH/potential "
            "combination (decomposition energy < 0.2 eV/atom)."
        ),
        reverse_pourbaix_component.layout(),
    ],
    style=dict(maxWidth="900px", margin="2em auto"),
)

ctc.register_crystal_toolkit(app=app, layout=layout)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
