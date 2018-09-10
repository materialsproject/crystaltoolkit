import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import dash_table_experiments as dt

from mp_dash_components.converters.structure import StructureIntermediateFormat
from mp_dash_components import StructureViewerComponent, GraphComponent
from mp_dash_components.layouts.misc import help_layout

from pymatgen.core import Structure

from itertools import combinations_with_replacement

from tempfile import NamedTemporaryFile
from base64 import b64decode
from json import dumps, loads

import numpy as np

def replace_species_transformation(structure_id_in=None, structure_id_out=None):

    def generate_layout():

        species_to_replace = dcc.Dropdown(
            options=[{
                'label': 'Si', 'value': 'Si'
            }],
            value='Si'
        )

        table = dt.DataTable(
            rows=[{'Species': 'Si', 'Amount /%': 100}],
            row_selectable=False,
            filterable=False,
            sortable=True,
            editable=True,
            selected_row_indices=[],
            id='replace'
        )

        error_settings = ...
        error_applying_transformation = ...

        return html.Div([species_to_replace, html.Br(), table])

    def generate_callbacks():

        def apply_transformation():
            ...

        def check_for_errors():
            ...


    layout = generate_layout()

    return layout


all_structure_transformations = [replace_species_transformation]
def all_structure_transformations_dropdown():
    dcc.Dropdown(
        {'label': 'Replace species', 'value': 0}
    )

