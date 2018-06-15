import mp_viewer
import dash
import dash_core_components as dcc
import dash_html_components as html

from dash_react_graph_vis import GraphComponent

import numpy as np
import json

from base64 import urlsafe_b64decode
from zlib import decompress
from urllib.parse import parse_qs
from uuid import uuid4

from dash.dependencies import Input, Output, State

from monty.serialization import loadfn

from structure_vis_mp import PymatgenVisualizationIntermediateFormat

from pymatgen import MPRester, Structure

app = dash.Dash()
app.title = "MP Dashboard"

app.scripts.config.serve_locally = True
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

mpr = MPRester()

DEFAULT_STRUCTURE = loadfn('default_structure.json')
DEFAULT_COLOR_SCHEME = 'VESTA'
DEFAULT_BONDING_METHOD = 'CrystalNN'

LAYOUT_STRUCTURE_VIEWER = html.Div(id='viewer-container', children=[
                        mp_viewer.StructureViewerComponent(
                            id='viewer',
                            data=PymatgenVisualizationIntermediateFormat(DEFAULT_STRUCTURE,
                                                                         bonding_strategy=
                                              DEFAULT_BONDING_METHOD,
                                                                         color_scheme=
                                              DEFAULT_COLOR_SCHEME).json
                        )
                    ], style={'height': '100%', 'width': '100%'})


# master app layout, includes layouts defined above
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    LAYOUT_STRUCTURE_VIEWER
])

app.server.secret_key = str(uuid4())
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
