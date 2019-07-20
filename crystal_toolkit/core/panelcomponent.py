import traceback

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import (
    Reveal,
    MessageContainer,
    MessageHeader,
    MessageBody,
)

import flask

PRIMARY_COLOR = "hsl(171, 100%, 41%)"


class PanelComponent2(MPComponent):
    """
    A Component intended to do analysis for something
    that is MSONable (typically a Structure) using a
    combination of one or more other MPComponents.
    """

    def __init__(self, open_by_default=False, *args, **kwargs):

        self.open_by_default = open_by_default
        super().__init__(*args, **kwargs)

    @property
    def title(self):
        return "Untitled Panel"

    @property
    def description(self):
        return None

    @property
    def loading_text(self):
        return "Loading"

    @property
    def all_layouts(self):

        message = html.Div(id=self.id("message"))

        description = html.Div(
            self.description,
            id=self.id("description"),
            className="mpc-panel-description",
        )

        if self.open_by_default:

            initial_contents = dcc.Loading(
                [html.Div(id=self.id("inner_contents"))],
                id=self.id("contents"),
                color=PRIMARY_COLOR,
            )

            panel = Reveal(
                title=self.title,
                children=[message, description, initial_contents],
                id=self.id("panel"),
                open=True,
            )

        else:

            initial_contents = dcc.Loading(
                [], id=self.id("contents"), color=PRIMARY_COLOR
            )

            panel = Reveal(
                title=self.title,
                children=[message, description, initial_contents],
                id=self.id("panel"),
            )

        return {"panel": panel}

    @property
    def update_panel_contents_inputs(self):
        return [Input(self.id(), "data")]

    def update_panel_contents(self, *args):
        raise NotImplementedError

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("contents"), "children"),
            [Input(f"{self.id('panel')}_summary", "n_clicks")],
            [State(self.id("contents"), "children")],
        )
        def load_panel(panel_n_clicks, current_contents):

            if current_contents or panel_n_clicks is None:
                raise PreventUpdate

            loading_text = html.P(
                [self.loading_text, html.Span("."), html.Span("."), html.Span(".")],
                className="mpc-loading",
            )

            return html.Div(loading_text, id=self.id("inner_contents"))


class PanelComponent(MPComponent):
    def __init__(
        self,
        *args,
        open_by_default=False,
        enable_error_message=True,
        has_output=False,
        **kwargs,
    ):

        self.open_by_default = open_by_default
        self.enable_error_message = enable_error_message
        self.has_output = has_output

        if self.description and len(self.description) > 140:
            raise ValueError(
                f"Description is too long, please keep to 140 characters or "
                f"fewer: {self.description[0:140]}..."
            )

        super().__init__(*args, **kwargs)

        if self.has_output:
            self.create_store("out")

    @property
    def title(self):
        return "Panel Title"

    @property
    def initial_contents(self):
        return html.P(
            [self.loading_text, html.Span("."), html.Span("."), html.Span(".")],
            className="mpc-loading",
        )

    @property
    def reference(self):
        # TODO: Implement
        return None

    @property
    def help(self):
        # TODO: Implement
        return None

    @property
    def description(self):
        return None

    @property
    def loading_text(self):
        return "Loading"

    @property
    def header(self):
        return html.Div()

    @property
    def footer(self):
        return html.Div()

    @property
    def all_layouts(self):

        initial_contents = html.Div(self.initial_contents, id=self.id("contents"))

        message = html.Div(id=self.id("message"))

        description = html.Div(
            self.description,
            id=self.id("description"),
            className="mpc-panel-description",
        )

        contents = html.Div(
            [message, description, self.header, initial_contents, self.footer]
        )

        panel = Reveal(
            title=self.title,
            children=contents,
            id=self.id("panel"),
            open=self.open_by_default,
        )

        return {"panel": panel}

    def update_contents(self, new_store_contents, *args):
        raise PreventUpdate

    @property
    def update_contents_additional_inputs(self):
        return []

    def generate_callbacks(self, app, cache):
        @cache.memoize(
            timeout=60 * 60 * 24,
            make_name=lambda x: f"{self.__class__.__name__}_{x}_cached",
        )
        def update_contents(*args, **kwargs):
            return self.update_contents(*args, **kwargs)

        @app.callback(
            [
                Output(self.id("contents"), "children"),
                Output(self.id("message"), "children"),
            ],
            [Input(self.id("panel") + "_summary", "n_clicks"), Input(self.id(), "data")]
            + [
                Input(component, property)
                for component, property in self.update_contents_additional_inputs
            ],
            [State(self.id("panel"), "open")],
        )
        def load_contents(panel_n_clicks, store_contents, *args):
            """
            Only update panel contents if panel is open by default, to speed up
            initial load time.
            """
            panel_initially_open = args[-1]
            # if the panel outputs data, we have to make sure callbacks are fired
            # regardless of if the panel is open or not
            if (not self.has_output) and (
                (panel_n_clicks is None) or (panel_initially_open is None)
            ):
                raise PreventUpdate
            if not store_contents:
                return html.Div(), html.Div()

            self.logger.debug(f"{self.__class__.__name__} panel callback fired.")

            try:
                return self.update_contents(store_contents, *args[:-1]), html.Div()
            except Exception as exception:
                self.logger.error(
                    f"Callback error.",
                    exc_info=True,
                    extra={"store_contents": store_contents},
                )
                error_header = (
                    "An error was encountered when trying to load this component, "
                    "please report this if it seems like a bug, thank you!"
                )
                # TODO: add GitHub Issue badge to error message box
                return (
                    html.Div(),
                    MessageContainer(
                        [
                            MessageHeader("Error"),
                            MessageBody(
                                [
                                    html.Div(error_header),
                                    dcc.Markdown(f"> {traceback.format_exc()}"),
                                ]
                            ),
                        ],
                        kind="danger",
                    ),
                )
