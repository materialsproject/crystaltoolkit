import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.components.core import MPComponent, PanelComponent
from crystal_toolkit.helpers.layouts import Button

from base64 import b64encode

class DownloadPanelComponent(PanelComponent):

    # human-readable label to file extension
    struct_options = {
        'CIF': 'cif',
        'POSCAR': 'poscar',
        'JSON': 'json'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def title(self):
        return "Download File"

    @property
    def description(self):
        return (
            "Download your crystal structure or molecule."
        )

    def update_contents(self, new_store_contents):

        options = dcc.Dropdown(
            id=self.id("file_extension"),
            value="cif",
            options=[{'label': k, 'value': v} for k, v in self.struct_options.items()],
            style={"display": "inline-block"}
        )

        download_button = Button("Download File", id=self.id("download"))

        return html.Div([
            options,
            download_button
        ])

    def _generate_callbacks(self, app, cache):
        super()._generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("download"), "children"),
            [Input(self.id(), "data"),
             Input(self.id("file_extension"), "value")]
        )
        def update_href(data, file_extension):

            structure = self.from_data(data)
            contents = structure.to(fmt=file_extension)

            print(contents)
            print(file_extension)

            base64 = b64encode(contents.encode("utf-8")).decode("ascii")

            href = f"data:text/plain;charset=utf-8;base64,{base64}"

            return html.A(f"Download File", href=href,
                          target="_blank")
