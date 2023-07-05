from __future__ import annotations

import warnings
from typing import Any
from uuid import uuid4

import dash_mp_components as mpc
from dash import dcc, html
from monty.serialization import loadfn

from crystal_toolkit import MODULE_PATH
from crystal_toolkit.settings import SETTINGS

BULMA_CSS = {
    "external_url": "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css"
}

FONT_AWESOME_CSS = {
    "external_url": "https://use.fontawesome.com/releases/v5.6.3/css/all.css"
}

PRIMARY_COLOR = "hsl(171, 100%, 41%)"

# TODO: change "kind" kwarg to list / group is- modifiers together?

"""
Helper methods to make working with Bulma classes easier.
"""


def _update_css_class(kwargs, class_name):
    """Convenience function to update className while respecting any additional classNames already
    set.
    """
    if "className" in kwargs:
        kwargs["className"] += f" {class_name}"
    else:
        kwargs["className"] = class_name


class Section(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "section")
        super().__init__(*args, **kwargs)


class Container(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "container")
        super().__init__(*args, **kwargs)


class Block(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "block")
        super().__init__(*args, **kwargs)


class Columns(html.Div):
    def __init__(
        self,
        *args,
        desktop_only=False,
        centered=False,
        gapless=False,
        multiline=False,
        **kwargs,
    ) -> None:
        _update_css_class(kwargs, "columns")
        if desktop_only:
            kwargs["className"] += " is-desktop"
        if centered:
            kwargs["className"] += " is-centered"
        if gapless:
            kwargs["className"] += " is-gapless"
        if multiline:
            kwargs["className"] += " is-multiline"
        super().__init__(*args, **kwargs)


class Column(html.Div):
    def __init__(
        self,
        *args,
        size: str | None = None,
        offset=None,
        narrow: bool = False,
        **kwargs,
    ) -> None:
        _update_css_class(kwargs, "column")
        if size:
            kwargs["className"] += f" is-{size}"
        if offset:
            kwargs["className"] += f" -is-offset-{size}"
        if narrow:
            kwargs["className"] += " is-narrow"
        super().__init__(*args, **kwargs)


class Button(html.Button):
    def __init__(
        self, *args, kind: str | None = None, size: str = "normal", **kwargs
    ) -> None:
        _update_css_class(kwargs, f"button is-{size}")
        if kind:
            kwargs["className"] += f" is-{kind}"
        super().__init__(*args, **kwargs)


class Error(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "notification is-danger")
        super().__init__(*args, **kwargs)


class MessageContainer(html.Article):
    def __init__(
        self, *args, kind: str = "warning", size: str = "normal", **kwargs
    ) -> None:
        if kind:
            _update_css_class(kwargs, f"message is-{kind} is-{size}")
        else:
            _update_css_class(kwargs, f"message is-{size}")
        super().__init__(*args, **kwargs)


class MessageHeader(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "message-header")
        super().__init__(*args, **kwargs)


class MessageBody(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "message-body")
        super().__init__(*args, **kwargs)


class Icon(html.Span):
    def __init__(
        self, kind: str = "download", fill: str = "s", *args, **kwargs
    ) -> None:
        """Font-awesome icon.

        Good options for kind are "info-circle", "question-circle", "book", "code".
        """
        _update_css_class(kwargs, "icon")
        if "fontastic" not in kind:
            # fontawesome styles (pre-distributed icons, e.g. download)
            super().__init__(html.I(className=f"fa{fill} fa-{kind}"), *args, **kwargs)
        else:
            # fontastic styles (custom icons, e.g. the MP app icons)
            super().__init__(html.I(className=kind), *args, **kwargs)


class Footer(html.Footer):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "footer")
        super().__init__(*args, **kwargs)


class Spinner(html.Button):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "button is-primary is-loading")
        kwargs["style"] = {"width": "35px", "height": "35px", "borderRadius": "35px"}
        kwargs["aria-label"] = "Loading"
        super().__init__(*args, **kwargs)


class Box(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "box")
        super().__init__(*args, **kwargs)


class H1(html.H1):
    def __init__(self, *args, subtitle: bool = False, **kwargs) -> None:
        if subtitle:
            _update_css_class(kwargs, "subtitle is-1")
        else:
            _update_css_class(kwargs, "title is-1")
        super().__init__(*args, **kwargs)


class H2(html.H2):
    def __init__(self, *args, subtitle: bool = False, **kwargs) -> None:
        if subtitle:
            _update_css_class(kwargs, "subtitle is-2")
        else:
            _update_css_class(kwargs, "title is-2")
        super().__init__(*args, **kwargs)


class H3(html.H3):
    def __init__(self, *args, subtitle: bool = False, **kwargs) -> None:
        if subtitle:
            _update_css_class(kwargs, "subtitle is-3")
        else:
            _update_css_class(kwargs, "title is-3")
        super().__init__(*args, **kwargs)


class H4(html.H4):
    def __init__(self, *args, subtitle: bool = False, **kwargs) -> None:
        if subtitle:
            _update_css_class(kwargs, "subtitle is-4")
        else:
            _update_css_class(kwargs, "title is-4")
        super().__init__(*args, **kwargs)


class H5(html.H5):
    def __init__(self, *args, subtitle: bool = False, **kwargs) -> None:
        if subtitle:
            _update_css_class(kwargs, "subtitle is-5")
        else:
            _update_css_class(kwargs, "title is-5")
        super().__init__(*args, **kwargs)


class H6(html.H6):
    def __init__(self, *args, subtitle: bool = False, **kwargs) -> None:
        if subtitle:
            _update_css_class(kwargs, "subtitle is-6")
        else:
            _update_css_class(kwargs, "title is-6")
        super().__init__(*args, **kwargs)


class Tag(html.Div):
    def __init__(
        self,
        tag,
        tag_type="primary",
        tag_addon=None,
        tag_addon_type="primary",
        size: str = "normal",
        *args,
        **kwargs,
    ) -> None:
        _update_css_class(kwargs, "tags")
        tags = [html.Span(tag, className=f"tag is-{tag_type} is-{size}")]
        if tag_addon:
            tags.append(
                html.Span(tag_addon, className=f"tag is-{tag_addon_type} is-{size}")
            )
            kwargs["className"] += " has-addons"
        super().__init__(tags, *args, **kwargs)


class TagContainer(html.Div):
    def __init__(self, tags: list[Tag], *args, **kwargs) -> None:
        _update_css_class(kwargs, "field is-grouped is-grouped-multiline")
        tags = [html.Div(tag, className="control") for tag in tags]
        super().__init__(tags, *args, **kwargs)


class Textarea(dcc.Textarea):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "textarea")
        super().__init__(*args, **kwargs)


class Reveal(html.Details):
    def __init__(
        self, children=None, id=None, summary_id=None, title=None, **kwargs
    ) -> None:
        if children is None:
            children = ["Loading..."]
        if id is None and isinstance(title, str):
            id = title
        if isinstance(title, str):
            title = H4(
                title, style={"display": "inline-block", "verticalAlign": "middle"}
            )
        contents_id = f"{id}_contents" if id else None
        summary_id = summary_id or f"{id}_summary"
        kwargs["style"] = {"marginBottom": "1rem"}
        super().__init__(
            [
                html.Summary(title, id=summary_id),
                html.Div(
                    children,
                    id=contents_id,
                    style={"marginTop": "0.5rem", "marginLeft": "1.1rem"},
                ),
            ],
            id=id,
            **kwargs,
        )


class Label(html.Label):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "label")
        super().__init__(*args, **kwargs)


class Modal(html.Div):
    def __init__(
        self,
        children: list | None = None,
        id: str | None = None,
        active: bool = False,
        **kwargs,
    ) -> None:
        _update_css_class(kwargs, "modal")
        if active:
            kwargs["className"] += " is-active"
        super().__init__(
            [
                html.Div(className="modal-background"),
                html.Div(
                    children=children, id=f"{id}_contents", className="modal-contents"
                ),
                html.Button(id=f"{id}_close", className="modal-close is-large"),
            ],
            **kwargs,
        )


class Field(html.Div):
    def __init__(
        self,
        *args,
        addons: bool = False,
        grouped: bool = False,
        grouped_multiline: bool = False,
        **kwargs,
    ) -> None:
        _update_css_class(kwargs, "field")
        if addons:
            kwargs["className"] += " has-addons"
        if grouped:
            kwargs["className"] += " is-grouped"
        if grouped_multiline:
            kwargs["className"] += " is-grouped-multiline"
        super().__init__(*args, **kwargs)


class Control(html.Div):
    """Control tag to wrap form elements, see https://bulma.io/documentation/form/general/."""

    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "control")
        super().__init__(*args, **kwargs)


class Input(dcc.Input):
    """Control tag to wrap form elements, see https://bulma.io/documentation/input/general/."""

    def __init__(
        self,
        *args,
        color="primary",
        **kwargs,
    ) -> None:
        _update_css_class(kwargs, f"input is-{color}")
        super().__init__(*args, **kwargs)


def get_tooltip(
    tooltip_label: Any,
    tooltip_text: str,
    underline: bool = True,
    tooltip_id: str = "",
    wrapper_class: str | None = None,
    **kwargs,
):
    """Uses the tooltip component from dash-mp-components to add a tooltip, typically for help text.
    This component uses react-tooltip under the hood.

    :param tooltip_label: text or component to display and apply hover behavior to
    :param tooltip_text: text to show on hover
    :param tooltip_id: unique id of the tooltip (will generate one if not supplied)
    :param wrapper_class: class to add to the span that wraps all the returned tooltip components (label + content)
    :param kwargs: additional props added to Tooltip component. See the components js file in
        dash-mp-components for a full list of props.
    :return: html.Span
    """
    if not tooltip_id:
        tooltip_id = uuid4().hex

    tooltip_class = "tooltip-label" if underline else None
    return html.Span(
        [
            html.Span(
                tooltip_label,
                className=tooltip_class,
                **{"data-tip": True, "data-for": tooltip_id},
            ),
            mpc.Tooltip(tooltip_text, id=tooltip_id, **kwargs),
        ],
        className=wrapper_class,
    )


def get_data_list(data: dict[str, str | int | float | list[str | int | float]]):
    """Show a formatted table of data items.

    :param data: dictionary of label, value pairs
    :return: html.Div
    """
    contents = []
    for title, value in data.items():
        label = Label(title) if isinstance(title, str) else title
        contents.append(html.Tr([html.Td(label), html.Td(value)]))
    return html.Table([html.Tbody(contents)], className="table")


def get_table(rows: list[list[Any]], header: list[str] | None = None) -> html.Table:
    """Create a HTML table from a list of elements.

    :param rows: list of list of cell contents
    :return: html.Table
    """
    contents = [html.Tr([html.Td(item) for item in row]) for row in rows]
    if not header:
        return html.Table([html.Tbody(contents)], className="table")
    header = html.Thead([html.Tr([html.Th(item) for item in header])])
    return html.Table([header, html.Tbody(contents)], className="table")


DOI_CACHE = loadfn(MODULE_PATH / "apps/assets/doi_cache.json")


def cite_me(
    doi: str | None = None, manual_ref: str | None = None, cite_text: str = "Cite me"
) -> html.Div:
    """Create a button to show users how to cite a particular resource.

    :param doi: DOI
    :param manual_ref: If DOI not available
    :param cite_text: Text to show as button label
    :return: A button
    """
    if doi:
        component = mpc.PublicationButton(id=doi, doi=doi, showTooltip=True)
    elif manual_ref:
        warnings.warn("Please use the DOI if available.")
        component = mpc.PublicationButton(
            children=cite_text, id=manual_ref, url=manual_ref
        )

    return component


def add_label_help(input, label, help) -> mpc.FilterField:
    """Combine an input, label, and tooltip text into a single consistent component."""
    return mpc.FilterField(input, id=uuid4().hex, label=label, tooltip=help)


class Loading(dcc.Loading):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args, color=PRIMARY_COLOR, type="dot", debug=SETTINGS.DEBUG_MODE, **kwargs
        )


def get_breadcrumb(parts):
    """Create a breadcrumb navigation bar.

    Args:
        parts (dict): Dictionary of name, link pairs.

    Returns:
        html.Nav: Breadcrumb navigation bar.
    """
    if not parts:
        return html.Nav()

    links = [
        html.Li(
            dcc.Link(name, href=link),
            className="is-active" if idx == len(parts) - 1 else None,
        )
        for idx, (name, link) in enumerate(parts.items())
    ]
    return html.Nav(html.Ul(links), className="breadcrumb")
