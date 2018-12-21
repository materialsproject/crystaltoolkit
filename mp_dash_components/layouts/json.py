import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from mp_dash_components.layouts.core import MPComponent


class JSONComponent(MPComponent):

    @property
    def layouts(self):

        return {
            'json': dcc.SyntaxHighlighter(id=f"{self.id}_highlighted"),
            'store': self._store
        }

    def _generate_callbacks(self, app):

        @app.callback(
            Output(f"{self.id}_highlighted", "children"),
            [Input(self.store_id, "data")]
        )
        def update_highlighter(data):
            return self.to_data(data)
