import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from mp_dash_components.components.core import PanelComponent
from mp_dash_components.helpers.layouts import Columns, Column
#from mp_dash_components import JSONViewComponent

from json import loads

class JSONEditor(PanelComponent):
    @property
    def title(self):
        return "JSON Editor"

    @property
    def description(self):
        return (
            "Developers may find it useful to be able to edit the underlying "
            "JSON representation of the material. Changes are updated live."
        )

    @property
    def all_layouts(self):
        all_layouts = super().all_layouts
        all_layouts["editor"] = dcc.Textarea(
            id=self.id("editor"),
            rows=16,
            className="textarea",
            style={"max-width": "90%"},
        )
        all_layouts["json"] = dcc.SyntaxHighlighter(
            id=self.id("highlighted"), customStyle={"height": "100%"}
        )
        return all_layouts

    def update_contents(self, new_store_contents):

        #JSONViewComponent(id=self.id("json-editor"),
        #                  src=loads(new_store_contents))

        return Columns([#Column(self.editor_layout), Column(self.json_layout),
                        Column()])

    def _generate_callbacks(self, app, cache):
        super()._generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("json-editor"), "src"), [Input(self.id(), "data")]
        )
        def update_highlighter(data):
            return loads(data)
