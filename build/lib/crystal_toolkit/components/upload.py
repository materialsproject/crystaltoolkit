from base64 import b64decode
from tempfile import NamedTemporaryFile

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from monty.serialization import loadfn
from pymatgen.core.structure import Molecule, Structure
from pymatgen.io.vasp.outputs import Chgcar

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import *


class StructureMoleculeUploadComponent(MPComponent):
    @property
    def _sub_layouts(self):

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
                    # TODO: CSS fix style and un-hide file name
                    html.Span(
                        id=self.id("upload_label"),
                        className="file-name",
                        style={"display": "none"},
                    ),
                ],
                className="file-label",
            ),
            className="file is-boxed",
            # TODO: CSS set sensible max-width, don't hard-code
            style={"max-width": "312px"},
        )

        upload = html.Div(
            [
                html.Label("Load from your computer: ", className="mpc-label"),
                dcc.Upload(upload_layout, id=self.id("upload_data"), multiple=False),
                html.Div(id=self.id("error_message_container")),
            ]
        )

        return {"upload": upload}

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("upload_label"), "children"),
            [Input(self.id("upload_data"), "filename")],
        )
        def show_filename_on_upload(filename):
            if not filename:
                raise PreventUpdate
            return filename

        @app.callback(
            Output(self.id("error_message_container"), "children"),
            [Input(self.id(), "data")],
        )
        def update_error_message(data):
            if not data:
                raise PreventUpdate
            if not data["error"]:
                return html.Div()
            else:
                return html.Div(
                    [
                        html.Br(),
                        MessageContainer(
                            [MessageHeader("Error"), MessageBody([data["error"]])],
                            kind="danger",
                            size="small",
                        ),
                    ]
                )

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

            error = None
            struct_or_mol = None

            # necessary to write to file so pymatgen's filetype detection can work
            with NamedTemporaryFile(suffix=filename) as tmp:
                tmp.write(decoded_contents)
                tmp.flush()
                try:
                    struct_or_mol = Structure.from_file(tmp.name)
                except:
                    try:
                        struct_or_mol = Molecule.from_file(tmp.name)
                    except:
                        try:
                            struct_or_mol = Chgcar.from_file(tmp.name)
                        except:
                            # TODO: fix these horrible try/excepts, loadfn may be dangerous
                            try:
                                struct_or_mol = loadfn(tmp.name)
                            except:
                                error = (
                                    "Could not parse uploaded file. "
                                    "If this seems like a bug, please report it. "
                                    "Crystal Toolkit understands all crystal "
                                    "structure file types and molecule file types "
                                    "supported by pymatgen."
                                )

            return {"data": struct_or_mol, "error": error}
