"""
Author: Sheng Pang
Modifier: Min-Hsueh Chiu

Message Snake - A reusable Dash notification snackbar component.

Provides fixed-position toast notifications callable from any page.
Supports fade-in/fade-out animations, auto-dismiss, and manual close.

Usage:
    from crystal_toolkit.components.error_msg import ErrorMessageAIO

    # 1. Include in layout
    ErrorMessageAIO(
        "Invalid composition input!",
        aio_id=self.id("invalid-comp-alarm"),
        msg_type="error",
    ).layout(),

    # 2. Add to callback:
    Output(ErrorMessage.ids.visible(self.id("invalid-comp-alarm")), "data"),
    # Return True to display the message, and False to hide it.

    Note: Do not need to register callbacks as using All-in-one pattern
"""

from __future__ import annotations

from dash import MATCH, Input, Output, callback, ctx, dcc, html

from crystal_toolkit.core.mpcomponent import MPComponent

# Bulma-inspired color scheme for notification types
_TYPE_COLORS = {
    "info": {
        "background": "hsl(217, 71%, 53%)",  # Bulma $info / $link (#3273dc)
        "color": "#ffffff",
    },
    "warning": {
        "background": "hsl(44, 100%, 47%)",  # Bulma-inspired darker yellow/orange
        "color": "#ffffff",
    },
    "error": {
        "background": "hsl(348, 86%, 61%)",  # Bulma $danger (#f14668)
        "color": "#ffffff",
    },
    "success": {
        "background": "hsl(153, 53%, 53%)",  # Bulma $success (#48c78e)
        "color": "#ffffff",
    },
}

# Position presets: each maps to CSS properties
_POSITION_STYLES = {
    "top": {
        "top": "20px",
        "left": "50%",
        "transform": "translateX(-50%)",
    },
    "bottom": {
        "bottom": "20px",
        "left": "50%",
        "transform": "translateX(-50%)",
    },
    "center": {
        "top": "50%",
        "left": "50%",
        "transform": "translate(-50%, -50%)",
    },
    "top-right": {
        "top": "20px",
        "right": "20px",
    },
    "top-left": {
        "top": "20px",
        "left": "20px",
    },
    "bottom-right": {
        "bottom": "20px",
        "right": "20px",
    },
    "bottom-left": {
        "bottom": "20px",
        "left": "20px",
    },
}

# Icons per message type (Font Awesome classes)
_TYPE_ICONS = {
    "info": "fas fa-info-circle",
    "warning": "fas fa-exclamation-triangle",
    "error": "fas fa-times-circle",
    "success": "fas fa-check-circle",
}


class ErrorMessageAIO(html.Div, MPComponent):
    class ids:
        wrapper = lambda aio_id: {
            "component": "ErrorMessageAIO",
            "subcomponents": "wrapper",
            "aio_id": aio_id,
        }
        close_button = lambda aio_id: {
            "component": "ErrorMessageAIO",
            "subcomponents": "close_button",
            "aio_id": aio_id,
        }
        message = lambda aio_id: {
            "component": "ErrorMessageAIO",
            "subcomponents": "message",
            "aio_id": aio_id,
        }
        div = lambda aio_id: {
            "component": "ErrorMessageAIO",
            "subcomponents": "div",
            "aio_id": aio_id,
        }
        timer = lambda aio_id: {
            "component": "ErrorMessageAIO",
            "subcomponents": "timer",
            "aio_id": aio_id,
        }
        visible = lambda aio_id: {
            "component": "ErrorMessageAIO",
            "subcomponents": "visible",
            "aio_id": aio_id,
        }

    ids = ids

    # _callbacks_registered = False # no instance registry

    def __init__(
        self,
        message,
        aio_id,
        msg_type,
        position="bottom-right",
        style=None,
        show_icon=False,
        min_width="280px",
        max_width="420px",
        z_index=9999,
        auto_dismiss_ms=50000,
    ):
        """Create a fixed-position notification snackbar (message snake).

        Returns a Dash html.Div with fade-in animation, auto-dismiss timer,
        and optional close button. Must call register_message_snake_callbacks()
        to enable auto-dismiss and close functionality.

        Args:
            message (str): The notification message to display.
            id (str): Unique HTML id for the notification container.
            msg_type (str): Notification type - 'info', 'warning', 'error', 'success'.
            position (str): Fixed position on screen. One of:
                'top', 'bottom', 'center', 'top-right', 'top-left',
                'bottom-right', 'bottom-left'.
            style (dict, optional): Additional CSS style overrides.
            show_icon (bool): Whether to show a type-specific icon.
            min_width (str): Minimum width of the notification.
            max_width (str): Maximum width of the notification.
            z_index (int): CSS z-index for layering.
            auto_dismiss_ms (int): Auto-dismiss delay in milliseconds. Defaults to 50000 (50s).

        """

        self.snake_id = aio_id
        self.show_icon = show_icon
        self.msg_type = msg_type
        self.message = message
        self.auto_dismiss_ms = auto_dismiss_ms

        # Resolve type colors
        type_style = _TYPE_COLORS.get(msg_type, _TYPE_COLORS["info"])

        # Resolve position
        pos_style = _POSITION_STYLES.get(position, _POSITION_STYLES["bottom-right"])

        # Build the notification style
        self.notification_style = {
            "position": "fixed",
            "zIndex": z_index,
            "minWidth": min_width,
            "maxWidth": max_width,
            "padding": "14px 20px",
            "borderRadius": "6px",
            "boxShadow": "0 4px 14px rgba(0, 0, 0, 0.2)",
            "display": "flex",
            "alignItems": "center",
            "gap": "12px",
            "fontFamily": "'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
            "fontSize": "18px",
            "fontWeight": "500",
            "lineHeight": "1.4",
            # Visible on mount; fade-out handled by callback via transition
            "opacity": "1",
            "transition": "opacity 0.4s ease",
            **type_style,
            **pos_style,
        }

        # Apply user style overrides
        if style:
            self.notification_style.update(style)

        # Define the component's layout, this is originally from `layout()` for MPComponent
        # But since this is AIO, which subclassing html.Div
        sub_layouts = self._sub_layouts
        super().__init__(
            [  # Equivalent to `html.Div([...])`
                dcc.Store(id=self.ids.visible(self.snake_id), data=False),
                sub_layouts["notification_div"],
                sub_layouts["interval"],
            ],
            id=self.ids.wrapper(self.snake_id),
            style={"display": "none"},
        )

    @property
    def _sub_layouts(self):
        # Build inner content
        children = []

        # Icon
        if self.show_icon:
            icon_class = _TYPE_ICONS.get(self.msg_type, _TYPE_ICONS["info"])
            children.append(
                html.I(
                    className=icon_class,
                    style={"fontSize": "18px", "flexShrink": "0"},
                )
            )

        # Message text
        children.append(
            html.Span(
                self.message, id=self.ids.message(self.snake_id), style={"flex": "1"}
            )
        )

        # Close button
        children.append(
            html.Button(
                html.I(className="fas fa-times"),
                className="delete",
                style={
                    "background": "transparent",
                    "border": "none",
                    "color": "inherit",
                    "cursor": "pointer",
                    "fontSize": "18px",
                    "padding": "0",
                    "marginLeft": "8px",
                    "opacity": "0.8",
                    "flexShrink": "0",
                },
                id=self.ids.close_button(self.snake_id),
                n_clicks=0,
            )
        )

        # Notification div
        notification_div = html.Div(
            children=children,
            id=self.ids.div(self.snake_id),
            style=self.notification_style,
        )

        # Auto-dismiss interval timer (fires once after auto_dismiss_ms)
        interval = dcc.Interval(
            id=self.ids.timer(self.snake_id),
            interval=self.auto_dismiss_ms,
            n_intervals=0,
            max_intervals=1,
        )

        return {"notification_div": notification_div, "interval": interval}

    """
    def layout(self) -> html.Div:
        sub_layouts = self._sub_layouts
        return html.Div(
            [
                dcc.Store(id=self.ids.visible(self.snake_id), data=False),
                sub_layouts["notification_div"],
                sub_layouts["interval"],
            ],
            id=self.ids.wrapper(self.snake_id),
            style={"display": "none"},
        )
    """

    @callback(
        Output(ids.wrapper(MATCH), "style"),
        Input(ids.visible(MATCH), "data"),
        Input(ids.close_button(MATCH), "n_clicks"),
        prevent_initial_call=True,
    )
    def sync_message(command_visible, close_clicks):
        triggered = ctx.triggered_id

        if (
            isinstance(triggered, dict)
            and triggered.get("subcomponents") == "close_button"
        ):
            return {"display": "none"}

        return {"display": "block"} if command_visible else {"display": "none"}

    """
    @callback(
        Output(ids.wrapper(MATCH), "style"),
        Input(ids.timer(MATCH), "n_intervals"),
        Input(ids.close_button(MATCH), "n_clicks"),
        State(ids.wrapper(MATCH), "style"),
        prevent_initial_call=True,
    )
    def _dismiss_message_snake(n_intervals, n_clicks, current_style):
        # Fade out and hide the message snake on timer or close click.
        if not current_style:
            raise PreventUpdate

        if not ctx.triggered:
            raise PreventUpdate

        # Apply fade-out: transition opacity to 0, then hide
        new_style = {**current_style}
        new_style["transition"] = "opacity 0.4s ease"
        new_style["opacity"] = "0"
        new_style["pointerEvents"] = "none"
        # Override the fade-in animation so it does not reset
        new_style["animation"] = "none"
        return new_style
    """
