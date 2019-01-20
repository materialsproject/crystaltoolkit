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

        # upload_field = html.Span(
        #    id=self.id("upload_label"),
        #    className="file-name",
        #    ##placeholder="CIF, XYZ, and more...",
        #    #readOnly=True,
        # )
        ##upload_field = html.Input
        # upload_button = Button(
        #    [Icon(kind="upload"), html.Span(), "Upload"],
        #    kind="primary",
        #    id=self.id("upload_button"),
        # )
        # upload = dcc.Upload(
        #    Field(
        #        [Control(upload_field), Control(upload_button)],
        #        addons=True,
        #        style={"margin-bottom": "0"},
        #    ),
        #    id=self.id("upload_data"),
        #    multiple=False,
        # )

        # this is a very custom component based on Bulma css stlyes
        upload_layout = html.Div(
            html.Label(
                [
                    html.Span(
                        [
                            Icon(kind="upload"),
                            html.Span(
                                "Choose a file to upload or drag and drop",
                                className="file-label",
                            ),
                        ],
                        className="file-cta",
                    ),
                    # TODO: fix style and un-hide file name
                    html.Span(
                        id=self.id("upload_label"),
                        className="file-name",
                        style={"display": "none"},
                    ),
                ],
                className="file-label",
            ),
            className="file is-boxed",
        )

        upload = html.Div(
            [
                html.Label("Load from your computer: ", className="mpc-label"),
                dcc.Upload(upload_layout, id=self.id("upload_data"), multiple=False),
            ]
        )

        return {"upload": upload}

    def _generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("upload_label"), "children"),
            [Input(self.id("upload_data"), "filename")],
        )
        def show_filename_on_upload(filename):
            if not filename:
                raise PreventUpdate
            print(filename)
            return filename

        @app.callback(
            Output(self.id(), "data"),
            [
                Input(self.id("upload_data"), "contents"),
                Input(self.id("upload_data"), "filename"),
                Input(self.id("upload_data"), "last_modified"),
            ],
        )
        def callback_update_structure(contents, filename, last_modified):

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
