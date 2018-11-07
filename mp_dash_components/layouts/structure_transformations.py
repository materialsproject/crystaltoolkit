import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import dash_table_experiments as dt

import json

from mp_dash_components.converters.structure import StructureIntermediateFormat
from mp_dash_components import StructureViewerComponent, GraphComponent
from mp_dash_components.layouts.misc import help_layout
from mp_dash_components.layouts.structure import dump_structure

from pymatgen.core import Structure
from pymatgen.analysis.gb.grain import GrainBoundaryGenerator

from itertools import combinations_with_replacement

from tempfile import NamedTemporaryFile
from base64 import b64decode
from json import dumps, loads

import numpy as np

def standard_transformation_layout(id, description):

    # need enable checkmark
    # description
    # need error div
    # need args box
    # needs structure id

    return html.Div([
        dcc.Store()
    ])

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

        def validate_input():
            ...

    layout = generate_layout()

    return layout


all_structure_transformations = [replace_species_transformation]
def all_structure_transformations_dropdown():
    dcc.Dropdown(
        {'label': 'Replace species', 'value': 0}
    )


def grain_boundary_transformation(structure_id_in, structure_id_out, app=None):

    COLOR_MAPPING = {
        'top_incident': [[82, 175, 176]],
        'top': [[83, 150, 227]],
        'bottom': [[227, 95, 83]],
        'bottom_incident': [[82, 175, 176]]
    }

    #ELEMENTS = {}

    #FCC_ELEMENTS = {
    #    "Al": "mp-134",
    #    "Ni": "mp-23",
    #    "Cu": "mp-30",
    #    "Sr": "mp-76",
    #    "Rh": "mp-74",
    #    "Pd": "mp-2",
    #    "Ag": "mp-124",
    #    "Ce": "mp-28",
    #    "Yb": "mp-162",
    #    "Ir": "mp-101",
    #    "Pt": "mp-126",
    #    "Au": "mp-81",
    #    "Pb": "mp-20483",
    #    "Th": "mp-37",
    #    "Pa": "mp-10740",
    #    "Ca": "mp-45",
    #    "Ac": "mp-10018"
    #}
    #ELEMENTS.update(FCC_ELEMENTS)

    #BCC_ELEMENTS = {
    #    "Li": "mp-135",
    #    "K": "mp-58",
    #    "V": "mp-146",
    #    "Cr": "mp-90",
    #    "Fe": "mp-13",
    #    "Rb": "mp-70",
    #    "Nb": "mp-75",
    #    "Mo": "mp-129",
    #    "Cs": "mp-1",
    #    "Ba": "mp-122",
    #    "Ta": "mp-50",
    #    "W": "mp-91",
    #    "Na": "mp-127",
    #    "Eu": "mp-20071"
    #}
    #ELEMENTS.update(BCC_ELEMENTS)

    def generate_layout():

        return html.Div([
            html.Div(id=f'{structure_id_in}_gb_message'),
            html.Br(),
            html.Div([
                html.Label('Rotation axis'),
                dcc.Input(value='[1, 0, 0]', id=f'{structure_id_in}_gb_rotation_axis', type='text',
                          style={'width': '150px'})
            ]),
            html.Br(),
            html.Div([
                html.Label('Choose Σ'),
                dcc.Dropdown(
                    id=f'{structure_id_in}_gb_sigma_options',
                    options=[],
                    placeholder='...'
                )
            ], style={'width': '150px'}),
            html.Br(),
            html.Div([
                html.Label('Choose rotation angle'),
                dcc.Dropdown(
                    id=f'{structure_id_in}_gb_rotation_options',
                    options=[],
                    placeholder='...'
                )
            ], style={'width': '150px'}),
            html.Br(),
            html.Div([
                html.Label('Grain width'),
                dcc.Slider(
                    id=f'{structure_id_in}_gb_expand_times',
                    min=1,
                    max=6,
                    step=1,
                    value=2,
                    marks={2: '2', 4: '4', 6: '6'}
                )
            ], style={'width': '150px'}),
            html.Br(),
            html.Div([
                html.Label('Distance between grains in Å'),
                dcc.Input(value='0.0', id=f'{structure_id_in}_gb_vacuum_thickness', type='text',
                          style={'width': '150px'})
            ]),
            html.Br(),
            html.Div([
                html.Label('Plane'),
                dcc.Input(value='None', id=f'{structure_id_in}_gb_plane', type='text',
                          style={'width': '150px'})
            ])
        ])

    def generate_callbacks(app=app):

        @app.callback(
            Output(f'{structure_id_in}_gb_message', 'children'),
            [Input('json-editor-structure', 'value')]  # TODO remove hard coding
        )
        def check_constraints(structure_in):
            s = Structure.from_dict(loads(structure_in))
            spgrp = s.get_space_group_info()[1]
            if spgrp == 225 or spgrp == 229:
                return "✅ Transformation can be applied to this structure."
            else:
                return "❌ Transformation cannot be applied to this structure, " \
                       "it is only valid for body-centered cubic or face-centered " \
                       "cubic materials."


        @app.callback(
            Output(f'{structure_id_in}_gb_sigma_options', 'options'),
            [Input(f'{structure_id_in}_gb_rotation_axis', 'value')],
            [State(f'{structure_id_in}_gb_sigma_options', 'options')]
        )
        def calculate_sigma(rotation_axis, current_options):
            try:
                rotation_axis = json.loads(rotation_axis)
            except:
                return current_options
            else:
                sigmas = GrainBoundaryGenerator.enum_sigma_cubic(100, rotation_axis)
                options = []
                subscript_unicode_map = {0: '₀', 1: '₁', 2: '₂', 3: '₃', 4: '₄',
                                         5: '₅', 6: '₆', 7: '₇', 8: '₈', 9: '₉'}
                for sigma in sorted(sigmas.keys()):
                    sigma_label = "Σ{}".format(sigma)
                    for k, v in subscript_unicode_map.items():
                        sigma_label = sigma_label.replace(str(k), v)
                    options.append({
                        'label': sigma_label,
                        'value': sigma
                    })

                return options

        @app.callback(
            Output(f'{structure_id_in}_gb_rotation_options', 'options'),
            [Input(f'{structure_id_in}_gb_rotation_axis', 'value'),
             Input(f'{structure_id_in}_gb_sigma_options', 'value')],
            [State(f'{structure_id_in}_gb_rotation_options', 'options')]
        )
        def calculate_sigma(rotation_axis, sigma, current_options):
            try:
                rotation_axis = json.loads(rotation_axis)
                sigma = int(sigma)
            except:
                return current_options
            else:
                sigmas = GrainBoundaryGenerator.enum_sigma_cubic(100, rotation_axis)
                rotation_angles = sigmas[sigma]
                options = []
                for rotation_angle in sorted(rotation_angles):
                    options.append({
                        'label': "{:.2f}º".format(rotation_angle),
                        'value': rotation_angle
                    })

                return options

        @app.callback(
            Output(f'{structure_id_in}_gb_sigma_options', 'value'),
            [Input(f'{structure_id_in}_gb_sigma_options', 'options')],
            [State(f'{structure_id_in}_gb_sigma_options', 'value')]
        )
        def update_default_value(options, current_value):
            if len(options) > 0:
                return options[0]['value']
            else:
                return current_value

        @app.callback(
            Output(f'{structure_id_in}_gb_rotation_options', 'value'),
            [Input(f'{structure_id_in}_gb_rotation_options', 'options')],
            [State(f'{structure_id_in}_gb_rotation_options', 'value')]
        )
        def update_default_value(options, current_value):
            if len(options) > 0:
                return options[0]['value']
            else:
                return current_value

    layout = generate_layout()
    generate_callbacks(app=app)

    return layout


def all_structure_transformations_layout(structure_id, app=None):

    all_transformations = {
        '': html.Div(),
        'Make grain boundary': grain_boundary_transformation(structure_id,
                                                             f"{structure_id}_out",
                                                             app=app)
    }

    def generate_layout(structure_id):

        hidden_structure_div_in = html.Div(id=structure_id,
                                           style={'display': 'none'})

        hidden_structure_div_out = html.Div(id=f"{structure_id}_out",
                                            style={'display': 'none'})

        label = html.Label("Choose transformation to apply:")

        transformation_choice = dcc.Dropdown(id=f"{structure_id}_transformation_choice",
        options=[
            {'label': k, 'value': k} for k in all_transformations.keys()
        ], value='') #list(all_transformations.keys())[0])

        enabled = dcc.Checklist(options=[
            {'label': 'Enable transformation', 'value': 'enabled'}
        ], values=[], id=f"{structure_id}_enabled")

        options_container = html.Div(id=f"{structure_id}_transformation_options")

        return html.Div([
            html.Br(),
            hidden_structure_div_in,
            hidden_structure_div_out,
            label,
            transformation_choice,
            enabled,
            html.Br(),
            options_container
        ])

    def generate_callbacks(app):

        @app.callback(
            Output(f"{structure_id}_transformation_options", "children"),
            [Input(f"{structure_id}_transformation_choice", "value")]
        )
        def return_transformation_options(transformation_choice):
            if transformation_choice in all_transformations:
                return all_transformations[transformation_choice]
            else:
                return html.Div()

    layout = generate_layout(structure_id)
    generate_callbacks(app)

    return layout
