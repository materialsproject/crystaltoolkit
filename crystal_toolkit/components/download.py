import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import Button

from base64 import b64encode


class DownloadPanelComponent(PanelComponent):

    # human-readable label to file extension
    struct_options = {
        "CIF": "cif",
        "POSCAR": "poscar",
        "JSON": "json",
        "Prismatic": "prismatic",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def title(self):
        return "Download File"

    @property
    def description(self):
        return "Download your crystal structure or molecule."

    def update_contents(self, new_store_contents):

        options = dcc.Dropdown(
            id=self.id("fmt"),
            value="cif",
            options=[{"label": k, "value": v} for k, v in self.struct_options.items()],
        )

        download_button = Button("Download File", id=self.id("download"))

        return html.Div([options, download_button])

    def generate_callbacks(self, app, cache):
        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("download"), "children"),
            [Input(self.id(), "data"), Input(self.id("fmt"), "value")],
        )
        def update_href(data, fmt):

            structure = self.from_data(data)

            try:
                contents = structure.to(fmt=fmt)
            except Exception as exc:
                # don't fail silently, tell user what went wrong
                contents = exc

            base64 = b64encode(contents.encode("utf-8")).decode("ascii")

            href = f"data:text/plain;charset=utf-8;base64,{base64}"

            return html.A(
                f"Download File",
                href=href,
                download=f"{structure.composition.reduced_formula}.{fmt}",
                target="_blank",
            )
