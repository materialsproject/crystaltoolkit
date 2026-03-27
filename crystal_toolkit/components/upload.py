from __future__ import annotations

import gzip
import tarfile
import zipfile
from base64 import b64decode
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from dash import dcc, html
from dash.dependencies import Component, Input, Output
from dash.exceptions import PreventUpdate
from monty.serialization import loadfn
from pymatgen.core import Molecule, Structure
from pymatgen.io.lobster import Charge, Icohplist
from pymatgen.io.vasp.outputs import Chgcar

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import (
    Icon,
    MessageBody,
    MessageContainer,
    MessageHeader,
)


class StructureMoleculeUploadComponent(MPComponent):
    @property
    def _sub_layouts(self) -> dict[str, Component]:
        # this is a very custom component based on Bulma css styles
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
            # TODO: CSS set sensible maxWidth, don't hard-code
            style={"maxWidth": "312px"},
        )

        upload = html.Div(
            [
                html.Label("Load from your computer: ", className="mpc-label"),
                dcc.Upload(upload_layout, id=self.id("upload_data"), multiple=False),
                html.Div(id=self.id("error_message_container")),
            ]
        )

        return {"upload": upload}

    def generate_callbacks(self, app, cache) -> None:
        @app.callback(
            Output(self.id("upload_label"), "children"),
            Input(self.id("upload_data"), "filename"),
        )
        def show_filename_on_upload(filename):
            if not filename:
                raise PreventUpdate
            return filename

        @app.callback(
            Output(self.id("error_message_container"), "children"),
            Input(self.id(), "data"),
        )
        def update_error_message(data):
            if not data:
                raise PreventUpdate
            if not data["error"]:
                return html.Div()
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
            Input(self.id("upload_data"), "contents"),
            Input(self.id("upload_data"), "filename"),
            Input(self.id("upload_data"), "last_modified"),
        )
        def callback_update_structure(contents, filename, last_modified):
            if not contents:
                raise PreventUpdate

            # assume we only want the first input for now
            _, content_string = contents.split(",")
            decoded_contents = b64decode(content_string)

            error = None
            struct_or_mol = None

            # necessary to write to file so pymatgen's filetype detection can work
            with NamedTemporaryFile(suffix=filename) as tmp:
                tmp.write(decoded_contents)
                tmp.flush()
                try:
                    struct_or_mol = Structure.from_file(tmp.name)
                except Exception:
                    try:
                        struct_or_mol = Molecule.from_file(tmp.name)
                    except Exception:
                        try:
                            struct_or_mol = Chgcar.from_file(tmp.name)
                        except Exception:
                            # TODO: fix these horrible try/excepts, loadfn may be dangerous
                            try:
                                struct_or_mol = loadfn(tmp.name)
                            except Exception:
                                error = (
                                    "Could not parse uploaded file. "
                                    "If this seems like a bug, please report it. "
                                    "Crystal Toolkit understands all crystal "
                                    "structure file types and molecule file types "
                                    "supported by pymatgen."
                                )

            return {"data": struct_or_mol, "error": error}


class LobsterEnvUploadComponent(MPComponent):
    """Component for uploading LOBSTER output files (gz or zip archives)."""

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        # this is a very custom component based on Bulma css styles
        upload_layout = html.Div(
            html.Label(
                [
                    html.Span(
                        [
                            Icon(kind="upload"),
                            html.Span(
                                "Choose a gz or zip file with LOBSTER outputs",
                                className="file-label",
                            ),
                        ],
                        className="file-cta",
                    ),
                    html.Span(
                        id=self.id("upload_label"),
                        className="file-name",
                        style={"display": "none"},
                    ),
                ],
                className="file-label",
            ),
            className="file is-boxed",
            style={"maxWidth": "600px"},
        )

        upload = html.Div(
            [
                html.Label(
                    "Upload LOBSTER outputs (ICOHPLIST.lobster / ICOBILIST.lobster/ ICOOPLIST.lobster, CHARGE.lobster and CONTCAR): ",
                    className="mpc-label",
                ),
                dcc.Upload(upload_layout, id=self.id("upload_data"), multiple=False),
                html.Div(id=self.id("error_message_container")),
            ]
        )

        return {"upload": upload}

    def generate_callbacks(self, app, cache) -> None:
        @app.callback(
            Output(self.id("upload_label"), "children"),
            Input(self.id("upload_data"), "filename"),
        )
        def show_filename_on_upload(filename):
            if not filename:
                raise PreventUpdate
            return filename

        @app.callback(
            Output(self.id("error_message_container"), "children"),
            Input(self.id(), "data"),
        )
        def update_error_message(data):
            if not data:
                raise PreventUpdate
            if not data.get("error"):
                return html.Div()
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
            Input(self.id("upload_data"), "contents"),
            Input(self.id("upload_data"), "filename"),
            Input(self.id("upload_data"), "last_modified"),
        )
        def callback_update_lobsterenv_data(contents, filename, last_modified):
            if not contents:
                raise PreventUpdate

            _, content_string = contents.split(",")
            decoded_contents = b64decode(content_string)

            error = None
            structure = None
            obj_icohp = None
            obj_charge = None

            def extract_nested_archives(directory_path):
                """Recursively extract nested gz and zip files in a directory."""
                for file_path in directory_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            if (
                                file_path.suffix == ".gz"
                                and file_path.name != "CHARGE.lobster"
                            ):
                                # Extract gz file
                                with gzip.open(file_path, "rb") as gz:
                                    extracted_content = gz.read()
                                # Write extracted content with same name but without .gz
                                base_name = file_path.stem
                                extract_path = file_path.parent / base_name
                                extract_path.write_bytes(extracted_content)
                                # Delete the original gz file
                                file_path.unlink()
                            elif file_path.suffix == ".zip":
                                # Extract zip file
                                extract_to = file_path.parent / file_path.stem
                                extract_to.mkdir(exist_ok=True)
                                with zipfile.ZipFile(file_path) as zf:
                                    zf.extractall(extract_to)
                                # Delete the original zip file
                                file_path.unlink()
                        except Exception:
                            # Skip files that can't be extracted
                            pass

                # Recursively check for more nested archives
                has_archives = any(
                    f.suffix in [".gz", ".zip"] and f.is_file()
                    for f in directory_path.rglob("*")
                    if f.name != "CHARGE.lobster"
                )
                if has_archives:
                    extract_nested_archives(directory_path)

            try:
                # Extract archive to temporary directory
                with TemporaryDirectory() as tmpdir:
                    tmpdir_path = Path(tmpdir)

                    # Check if it's a zip or tar.gz file
                    if filename.endswith(".zip"):
                        # Write to temporary file and extract
                        with NamedTemporaryFile(
                            suffix=".zip", delete=False
                        ) as tmp_file:
                            tmp_file.write(decoded_contents)
                            tmp_file.flush()
                            with zipfile.ZipFile(tmp_file.name) as zf:
                                zf.extractall(tmpdir_path)
                    elif filename.endswith((".tar.gz", ".tgz")):
                        # Write to temporary file and extract
                        with NamedTemporaryFile(
                            suffix=".tar.gz", delete=False
                        ) as tmp_file:
                            tmp_file.write(decoded_contents)
                            tmp_file.flush()
                            with tarfile.open(tmp_file.name) as tar:
                                tar.extractall(tmpdir_path)
                    elif filename.endswith(".gz"):
                        # Single gzip file, try to extract
                        with NamedTemporaryFile(suffix=".gz", delete=False) as tmp_file:
                            tmp_file.write(decoded_contents)
                            tmp_file.flush()
                            with gzip.open(tmp_file.name, "rb") as gz:
                                extracted_content = gz.read()
                            # Write extracted content to temp location
                            base_name = filename.rsplit(".gz", 1)[0]
                            extract_path = tmpdir_path / base_name
                            extract_path.write_bytes(extracted_content)
                    else:
                        raise ValueError("File must be a .zip, .tar.gz, or .gz archive")

                    # Extract nested archives
                    extract_nested_archives(tmpdir_path)

                    # Find the required files in the extracted directory
                    icohp_file = None
                    charge_file = None
                    structure_file = None
                    are_coops = False
                    are_cobis = False

                    for file_path in tmpdir_path.rglob("*"):
                        if file_path.is_file():
                            # Check for ICOHP variants
                            if "ICOHPLIST.lobster" in file_path.name:
                                icohp_file = file_path
                                are_coops = False
                                are_cobis = False
                            elif "ICOBILIST.lobster" in file_path.name:
                                icohp_file = file_path
                                are_coops = False
                                are_cobis = True
                            elif "ICOOPLIST.lobster" in file_path.name:
                                icohp_file = file_path
                                are_coops = True
                                are_cobis = False
                            # Check for CHARGE
                            elif "CHARGE.lobster" in file_path.name:
                                charge_file = file_path
                            # Check for structure files
                            elif file_path.name == "CONTCAR":
                                structure_file = file_path
                            elif file_path.name == "POSCAR":
                                raise ValueError(
                                    "POSCAR file found in archive, but CONTCAR is usually compatible with LOBSTER outputs. Please ensure your archive contains a CONTCAR file for best results."
                                )

                    # Validate that all required files are present
                    if not icohp_file:
                        raise FileNotFoundError(
                            "Neither of ICOHPLIST.lobster, ICOBILIST.lobster or ICOOPLIST.lobster not found in archive"
                        )
                    if not charge_file:
                        raise FileNotFoundError("CHARGE.lobster not found in archive")
                    if not structure_file:
                        raise FileNotFoundError("CONTCAR not found in archive")

                    # Load the files using pymatgen
                    try:
                        structure = Structure.from_file(str(structure_file))
                    except Exception as e:
                        raise ValueError(f"Failed to load CONTCAR: {e!s}") from e

                    try:
                        obj_icohp = Icohplist(
                            filename=str(icohp_file),
                            are_coops=are_coops,
                            are_cobis=are_cobis,
                        )
                    except Exception as e:
                        raise ValueError(
                            f"Failed to load ICOHPLIST.lobster: {e!s}"
                        ) from e

                    try:
                        obj_charge = Charge(filename=str(charge_file))
                    except Exception as e:
                        raise ValueError(f"Failed to load CHARGE.lobster: {e!s}") from e

            except FileNotFoundError as e:
                error = f"Archive error: {e!s}"
            except ValueError as e:
                error = str(e)
            except Exception as e:
                error = f"Failed to process uploaded file: {e!s}"

            return {
                "structure": structure,
                "obj_icohp": obj_icohp,
                "obj_charge": obj_charge,
                "error": error,
            }
