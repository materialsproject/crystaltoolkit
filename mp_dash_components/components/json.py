import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from mp_dash_components.components.core import MPComponent


class JSONComponent(MPComponent):

    @property
    def all_layouts(self):

        return {
            'json': dcc.SyntaxHighlighter(id=self.id("highlighted"))
        }

    def _generate_callbacks(self, app):

        @app.callback(
            Output(self.id("highlighted"), "children"),
            [Input(self.id(), "data")]
        )
        def update_highlighter(data):
            return self.to_data(data)
