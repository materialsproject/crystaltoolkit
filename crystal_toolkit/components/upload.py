import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from crystal_toolkit import GraphComponent
from crystal_toolkit.components.core import MPComponent, PanelComponent
from crystal_toolkit.helpers.layouts import *
from crystal_toolkit.components.structure import StructureMoleculeComponent

from pymatgen.core.structure import Structure, Molecule
from pymatgen.analysis.graphs import StructureGraph, MoleculeGraph

from typing import Union


class StructureMoleculeUploadComponent(MPComponent):

    @property
    def all_layouts(self):

        upload = html.Div(
            [
                html.Label("Load from a local file:"),
                dcc.Upload(
                    id=self.id("upload_data"),
                    children=html.Div(
                        [
                            html.Span(
                                ["Drag and Drop or ", html.A("Select File")],
                                id=self.id("upload_label"),
                            ),
                            help_layout(
                                "Upload any file that pymatgen supports, "
                                "including CIF and VASP file formats."
                            ),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                    },
                    multiple=True,
                ),
            ]
        )

        return {
            'upload': upload
        }

    def _generate_callbacks(self, app, cache):


        @app.callback(
            Output(f"{structure_id}_upload_label", "children"),
            [Input(f"{structure_id}_upload_data", "filename")],
            [State(f"{structure_id}_upload_label", "children")],
        )
        def callback_upload_label(filenames, current_upload_label):
            """
           Displays the filename of any uploaded data.
           """
            if filenames:
                return "{}".format(", ".join(filenames))
            else:
                return current_upload_label

        @app.callback(
            Output(structure_id, "children"),
            [
                Input(f"{structure_id}_upload_data", "contents"),
                Input(f"{structure_id}_upload_data", "filename"),
                Input(f"{structure_id}_upload_data", "last_modified"),
            ],
        )
        def callback_update_structure(
                list_of_contents, list_of_filenames, list_of_modified_dates
        ):

            if list_of_contents is not None:

                # assume we only want the first input for now
                content_type, content_string = list_of_contents[0].split(",")
                decoded_contents = b64decode(content_string)
                name = list_of_filenames[0]

                # necessary to write to file so pymatgen's filetype detection can work
                with NamedTemporaryFile(suffix=name) as tmp:
                    tmp.write(decoded_contents)
                    tmp.flush()
                    structure = Structure.from_file(tmp.name)

                # TODO: remove (eventually, after vector support added)
                if "magmom" in structure.site_properties:
                    structure.add_site_property(
                        "magmom",
                        [float(m) for m in structure.site_properties["magmom"]],
                    )

                return dump_structure(structure)

            else:

                return None
