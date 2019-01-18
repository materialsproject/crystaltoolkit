import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from crystal_toolkit import GraphComponent
from crystal_toolkit.components.core import MPComponent, PanelComponent
from crystal_toolkit.helpers.layouts import *
from crystal_toolkit.components.structure import StructureMoleculeComponent

from tempfile import NamedTemporaryFile
from base64 import b64decode

from pymatgen.core.structure import Structure, Molecule
from pymatgen.analysis.graphs import StructureGraph, MoleculeGraph

from typing import Union


class StructureMoleculeUploadComponent(MPComponent):
    @property
    def all_layouts(self):

        upload_field = dcc.Input(
            id=self.id("upload_label"),
            className="input",
            placeholder="CIF, XYZ, and more...",
            readOnly=True,
        )
        upload_button = Button(
            [Icon(kind="upload"), html.Span(), "Upload"],
            kind="primary",
            id=self.id("upload_button"),
        )
        upload = dcc.Upload(
            Field(
                [Control(upload_field), Control(upload_button)],
                addons=True,
                style={"margin-bottom": "0"},
            ),
            id=self.id("upload_data"),
            multiple=False,
        )

        return {"upload": upload}

    def _generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("upload_label"), "value"),
            [Input(self.id("upload_data"), "filename")],
        )
        def show_filename_on_upload(filename):
            if not filename:
                raise PreventUpdate
            return filename

        @app.callback(
            Output(self.id(), "data"),
            [
                Input(self.id("upload_data"), "contents"),
                Input(self.id("upload_data"), "filename"),
                Input(self.id("upload_data"), "last_modified"),
            ],
        )
        def callback_update_structure(
            contents, filename, last_modified
        ):

            if not contents:
                raise PreventUpdate

            # assume we only want the first input for now
            content_type, content_string = contents.split(",")
            decoded_contents = b64decode(content_string)

            # necessary to write to file so pymatgen's filetype detection can work
            with NamedTemporaryFile(suffix=filename) as tmp:
                tmp.write(decoded_contents)
                tmp.flush()
                try:
                    struct_or_mol = Structure.from_file(tmp.name)
                except:
                    struct_or_mol = Molecule.from_file(tmp.name)

            return self.to_data(struct_or_mol)
