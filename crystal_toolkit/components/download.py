import dash_core_components as dcc
import dash_html_components as html
from dash import callback_context

from dash.dependencies import Input, Output, State

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import Button, Icon

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

    def contents_layout(self) -> html.Div:

        state = {"fmt": "cif"}

        options = self.get_choice_input(
            kwarg_label="fmt",
            state=state,
            options=[{"label": k, "value": v} for k, v in self.struct_options.items()],
            style={
                "border-radius": "4px 0px 0px 4px",
                "width": "10rem",
                "height": "1.5rem",
            },
        )

        # TODO: replace with a React native Download component
        download_button = html.A(
            Button(
                [Icon(kind="download"), html.Span(), "Download"],
                kind="primary",
                id=self.id("download"),
                style={"height": "2.25rem"},
            ),
            href="google.com",
            target="_blank",
            id=self.id("download-link"),
        )

        return html.Div(
            [
                html.Div([options], className="control"),
                html.Div([download_button], className="control"),
            ],
            className="field has-addons",
        )

    def generate_callbacks(self, app, cache):
        super().generate_callbacks(app, cache)

        @app.callback(
            [
                Output(self.id("download-link"), "href"),
                Output(self.id("download-link"), "download"),
            ],
            [Input(self.id(), "data"), Input(self.get_kwarg_id("fmt"), "value")],
        )
        def update_href(data, fmt):

            structure = self.from_data(data)
            fmt = self.reconstruct_kwarg_from_state(callback_context.inputs, "fmt")

            try:
                contents = structure.to(fmt=fmt)
            except Exception as exc:
                # don't fail silently, tell user what went wrong
                contents = exc

            base64 = b64encode(contents.encode("utf-8")).decode("ascii")

            href = f"data:text/plain;charset=utf-8;base64,{base64}"

            return href, f"{structure.composition.reduced_formula}.{fmt}"
