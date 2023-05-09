from __future__ import annotations

from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import Reveal


class PanelComponent(MPComponent):
    """A component intended to do wrap another component or set of components inside a panel. The
    key benefit is that the inner contents of the panel are not loaded until the panel is opened, so
    can reduce the number of callbacks run until a user initiates interaction.

    To use, implement the "contents_layout" method, and add any new callbacks necessary to fill it.
    """

    @property
    def title(self) -> str:
        return "Untitled Panel"

    @property
    def description(self) -> str | None:
        return None

    def panel_layout(self, open_by_default=False):
        message = html.Div(id=self.id("message"))

        description = html.Div(
            self.description,
            id=self.id("description"),
            className="mpc-panel-description",
        )

        initial_contents = html.Div(id=self.id("contents"))

        return Reveal(
            title=self.title,
            children=[message, description, html.Br(), initial_contents],
            id=self.id("panel"),
            summary_id=self.id("panel_summary"),
            open=open_by_default,
        )

    def contents_layout(self) -> html.Div:
        raise NotImplementedError

    def generate_callbacks(self, app, cache) -> None:
        pass

        @app.callback(
            Output(self.id("contents"), "children"),
            Input(self.id("panel_summary"), "n_clicks"),
            State(self.id("contents"), "children"),
        )
        def load_panel(panel_n_clicks, current_contents):
            if current_contents or panel_n_clicks is None:
                raise PreventUpdate

            return html.Div(self.contents_layout(), id=self.id("inner_contents"))
