import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.components.core import MPComponent, PanelComponent
from crystal_toolkit.helpers.layouts import Button


class DownloadComponent(PanelComponent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def title(self):
        return "Download File"

    @property
    def description(self):
        return (
            "Download as a common file type, such as CIF"
        )

    def update_contents(self, new_store_contents):

        return Button(id=self.id("download"))

    #def _generate_callbacks(self, app, cache):
    #    super()._generate_callbacks(app, cache)
#
    #    @app.callback(
    #        Output(self.id("highlighted"), "children"), [Input(self.id("editor"), "value")]
    #    )
    #    def update_highlighter(data):
    #        return data
#
    #    @app.callback(
    #        Output(self.id("out"), "data"), [Input(self.id("editor"), "value")],
    #        [State(self.id(), "data")]
    #    )
    #    def update_editor(new_data, current_data):
    #        if not new_data:
    #            return current_data
    #        return new_data
#
