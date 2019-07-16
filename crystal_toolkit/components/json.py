import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import Columns, Column, Box

from json import loads


class JSONEditor(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, has_output=True, **kwargs)

    @property
    def title(self):
        return "JSON Editor"

    @property
    def description(self):
        return (
            "Advanced users may find it useful to be able to edit the underlying "
            "JSON representation of the material. Changes are updated live."
        )

    @property
    def initial_contents(self):
        # TODO: this is so dumb, PanelComponent needs a rethink
        # (this comment is definition of technical debt)

        editor = dcc.Textarea(
            id=self.id("editor"),
            rows=16,
            className="textarea",
            style={"max-width": "88%", "max-height": "800px", "height": "100%"},
        )
        json = Box(
            dcc.SyntaxHighlighter(
                id=self.id("highlighted"),
                customStyle={"height": "100%", "max-height": "800px"},
            )
        )

        return Columns([Column(editor), Column(json)])

    def update_contents(self, new_store_contents):

        editor = dcc.Textarea(
            id=self.id("editor"),
            rows=16,
            className="textarea",
            style={"max-width": "88%", "max-height": "800px", "height": "100%"},
            value=new_store_contents,
        )
        json = Box(
            dcc.SyntaxHighlighter(
                id=self.id("highlighted"),
                customStyle={"height": "100%", "max-height": "800px"},
                children=new_store_contents,
            )
        )

        return Columns([Column(editor), Column(json)])

    def generate_callbacks(self, app, cache):
        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("highlighted"), "children"),
            [Input(self.id("editor"), "value")],
        )
        def update_highlighter(data):
            return data

        @app.callback(
            Output(self.id("out"), "data"),
            [Input(self.id("editor"), "value")],
            [State(self.id(), "data")],
        )
        def update_editor(new_data, current_data):
            if not new_data:
                return current_data
            return new_data
