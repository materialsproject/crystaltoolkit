import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.components.core import MPComponent, PanelComponent
from crystal_toolkit.helpers.layouts import Columns, Column, Box

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
        #all_layouts["syntax-error"] = ...
        all_layouts["editor"] = dcc.Textarea(
            id=self.id("editor"),
            rows=16,
            className="textarea",
            style={"max-width": "90%"},
        )
        all_layouts["json"] = Box(dcc.SyntaxHighlighter(
            id=self.id("highlighted"), customStyle={"height": "100%",
                                                    "max-height": "800px"}
        ))
        return all_layouts

    def update_contents(self, new_store_contents):

        return Columns([Column(self.editor_layout), Column(self.json_layout)])

    def _generate_callbacks(self, app, cache):
        super()._generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("highlighted"), "children"), [Input(self.id(), "data")]
        )
        def update_highlighter(data):
            return data

        @app.callback(
            Output(self.id("editor"), "value"), [Input(self.id(), "data")]
        )
        def update_editor(data):
            return data
