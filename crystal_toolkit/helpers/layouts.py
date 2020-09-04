import os
import warnings
from typing import Any, Dict, List, Optional, Union

import dash_core_components as dcc
import dash_html_components as html
from habanero import content_negotiation
from monty.serialization import dumpfn, loadfn

from crystal_toolkit import MODULE_PATH
from crystal_toolkit.settings import SETTINGS

BULMA_CSS = {
    "external_url": "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css"
}

FONT_AWESOME_CSS = {
    "external_url": "https://use.fontawesome.com/releases/v5.6.3/css/all.css"
}

PRIMARY_COLOR = "hsl(171, 100%, 41%)"

# TODO: change "kind" kwarg to list / group is- modifiers together

"""
Helper methods to make working with Bulma classes easier.
"""


class Section(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "section"
        super().__init__(*args, **kwargs)


class Container(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "container"
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
    ):
        kwargs["className"] = "columns"
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
    def __init__(self, *args, size=None, offset=None, narrow=False, **kwargs):
        kwargs["className"] = "column"
        if size:
            kwargs["className"] += f" is-{size}"
        if offset:
            kwargs["className"] += f" -is-offset-{size}"
        if narrow:
            kwargs["className"] += " is-narrow"
        super().__init__(*args, **kwargs)


class Button(html.Button):
    def __init__(self, *args, kind=None, size="normal", **kwargs):
        kwargs["className"] = f"button is-{size}"
        if kind:
            kwargs["className"] += f" is-{kind}"
        super().__init__(*args, **kwargs)


class Error(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "notification is-danger"
        super().__init__(*args, **kwargs)


class MessageContainer(html.Article):
    def __init__(self, *args, kind="warning", size="normal", **kwargs):
        if kind:
            kwargs["className"] = f"message is-{kind} is-{size}"
        else:
            kwargs["className"] = f"message is-{size}"
        super().__init__(*args, **kwargs)


class MessageHeader(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "message-header"
        super().__init__(*args, **kwargs)


class MessageBody(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "message-body"
        super().__init__(*args, **kwargs)


class Icon(html.Span):
    def __init__(self, kind="download", fill="s", *args, **kwargs):
        """
        Font-awesome icon. Good options for kind are "info-circle",
        "question-circle", "book", "code".
        """
        kwargs["className"] = "icon"
        if "fontastic" not in kind:
            # fontawesome styles (pre-distributed icons, e.g. download)
            super().__init__(html.I(className=f"fa{fill} fa-{kind}"), *args, **kwargs)
        else:
            # fontastic styles (custom icons, e.g. the MP app icons)
            super().__init__(html.I(className=kind), *args, **kwargs)


class Footer(html.Footer):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "footer"
        super().__init__(*args, **kwargs)


class Spinner(html.Button):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "button is-primary is-loading"
        kwargs["style"] = {"width": "35px", "height": "35px", "borderRadius": "35px"}
        kwargs["aria-label"] = "Loading"
        super().__init__(*args, **kwargs)


class Box(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "box"
        super().__init__(*args, **kwargs)


class H1(html.H1):
    def __init__(self, *args, subtitle=False, **kwargs):
        if subtitle:
            kwargs["className"] = "subtitle is-1"
        else:
            kwargs["className"] = "title is-1"
        super().__init__(*args, **kwargs)


class H2(html.H2):
    def __init__(self, *args, subtitle=False, **kwargs):
        if subtitle:
            kwargs["className"] = "subtitle is-2"
        else:
            kwargs["className"] = "title is-2"
        super().__init__(*args, **kwargs)


class H3(html.H3):
    def __init__(self, *args, subtitle=False, **kwargs):
        if subtitle:
            kwargs["className"] = "subtitle is-3"
        else:
            kwargs["className"] = "title is-3"
        super().__init__(*args, **kwargs)


class H4(html.H4):
    def __init__(self, *args, subtitle=False, **kwargs):
        if subtitle:
            kwargs["className"] = "subtitle is-4"
        else:
            kwargs["className"] = "title is-4"
        super().__init__(*args, **kwargs)


class H5(html.H5):
    def __init__(self, *args, subtitle=False, **kwargs):
        if subtitle:
            kwargs["className"] = "subtitle is-5"
        else:
            kwargs["className"] = "title is-5"
        super().__init__(*args, **kwargs)


class H6(html.H6):
    def __init__(self, *args, subtitle=False, **kwargs):
        if subtitle:
            kwargs["className"] = "subtitle is-6"
        else:
            kwargs["className"] = "title is-6"
        super().__init__(*args, **kwargs)


class Tag(html.Div):
    def __init__(
        self,
        tag,
        tag_type="primary",
        tag_addon=None,
        tag_addon_type="primary",
        size="normal",
        *args,
        **kwargs,
    ):
        kwargs["className"] = "tags"
        tags = [html.Span(tag, className=f"tag is-{tag_type} is-{size}")]
        if tag_addon:
            tags.append(
                html.Span(tag_addon, className=f"tag is-{tag_addon_type} is-{size}")
            )
            kwargs["className"] += " has-addons"
        super().__init__(tags, *args, **kwargs)


class TagContainer(html.Div):
    def __init__(self, tags: List[Tag], *args, **kwargs):
        kwargs["className"] = "field is-grouped is-grouped-multiline"
        tags = [html.Div(tag, className="control") for tag in tags]
        super().__init__(tags, *args, **kwargs)


class Textarea(html.Textarea):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "textarea"
        super().__init__(*args, **kwargs)


class Reveal(html.Details):
    def __init__(self, children=None, id=None, summary_id=None, title=None, **kwargs):
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
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "label"
        super().__init__(*args, **kwargs)


class Modal(html.Div):
    def __init__(self, children=None, id=None, active=False, **kwargs):
        kwargs["className"] = "modal"
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
        self, *args, addons=False, grouped=False, grouped_multiline=False, **kwargs
    ):
        kwargs["className"] = "field"
        if addons:
            kwargs["className"] += " has-addons"
        if grouped:
            kwargs["className"] += " is-grouped"
        if grouped_multiline:
            kwargs["className"] += " is-grouped-multiline"
        super().__init__(*args, **kwargs)


class Control(html.Div):
    """
    Control tag to wrap form elements,
    see https://bulma.io/documentation/form/general/
    """

    def __init__(self, *args, **kwargs):
        if "className" not in kwargs:
            kwargs["className"] = "control"
        else:
            kwargs["className"] += " control"
        super().__init__(*args, **kwargs)


class Level(html.Div):
    """

    """

    def __init__(self):
        ...


def get_tooltip(
    tooltip: html.Div, tooltip_text: str, underline: bool = True
) -> html.Div:
    """
    Add a tooltip, typically for help text.
    :param tooltip: element to apply tooltip to
    :param tooltip_text: text to show on hover
    :param underline: whether to show hint that element provides tooltip functionality
    :return: html.Div
    """
    if underline:
        style = None
    else:
        style = {"borderBottom": "0px"}

    return html.Div(
        [tooltip, html.Span(tooltip_text, className="tooltiptext")],
        className="tooltip",
        style=style,
    )


def get_data_list(data: Dict[str, str]):
    """
    Show a formatted table of data items.
    :param data: dictionary of label, value pairs
    :return: html.Div
    """
    contents = []
    for title, value in data.items():
        contents.append(html.Tr([html.Td(Label(title)), html.Td(value)]))
    return html.Table([html.Tbody(contents)], className="table")


def get_table(rows: List[List[Any]], header: Optional[List[str]] = None) -> html.Table:
    """
    Create a HTML table from a list of elements.
    :param rows: list of list of cell contents
    :return: html.Table
    """
    contents = []
    for row in rows:
        contents.append(html.Tr([html.Td(item) for item in row]))
    if not header:
        return html.Table([html.Tbody(contents)], className="table")
    else:
        header = html.Thead([html.Tr([html.Th(item) for item in header])])
        return html.Table([header, html.Tbody(contents)], className="table")


DOI_CACHE = loadfn(MODULE_PATH / "apps/assets/doi_cache.json")


def cite_me(
    doi: str = None, manual_ref: str = None, cite_text: str = "Cite me"
) -> html.Div:
    """
    Create a button to show users how to cite a particular resource.
    :param doi: DOI
    :param manual_ref: If DOI not available
    :param cite_text: Text to show as button label
    :return: A button
    """
    if doi:
        if doi in DOI_CACHE:
            ref = DOI_CACHE[doi]
        else:
            try:
                ref = content_negotiation(ids=doi, format="text", style="ieee")[3:]
                DOI_CACHE[doi] = ref
                dumpfn(DOI_CACHE, MODULE_PATH / "apps/assets/doi_cache.json")
            except Exception as exc:
                print("Error retrieving DOI", doi, exc)
                ref = f"DOI: {doi}"
        tooltip_text = f"If this analysis is useful, please cite {ref}"
    elif manual_ref:
        warnings.warn("Please use the DOI if available.")
        tooltip_text = (
            f"If this analysis is useful, please cite the "
            f"relevant publication: {manual_ref}"
        )
    else:
        tooltip_text = (
            f"If this analysis is useful, please cite the "
            f"relevant publication (publication pending)."
        )

    reference_button = html.A(
        [
            Button(
                [Icon(kind="book"), html.Span(cite_text)],
                size="small",
                kind="link",
                style={"height": "1.5rem"},
            )
        ],
        href=f"https://dx.doi.org/{doi}",
        target="_blank",
    )

    with_tooltip = get_tooltip(reference_button, tooltip_text, underline=False)

    return with_tooltip


def add_label_help(input, label, help):

    if (not label) and (not help):
        return input

    contents = []
    if label and not help:
        contents.append(html.Label(label, className="mpc-label"))
    if label and help:
        contents.append(
            get_tooltip(html.Label(label, className="mpc-label"), dcc.Markdown(help))
        )
    contents.append(input)

    return html.Div(
        contents,
        style={
            "display": "inline-block",
            "padding-right": "1rem",
            "vertical-align": "top",
        },
    )


class Loading(dcc.Loading):
    def __init__(self, *args, **kwargs):

        super().__init__(
            *args, color=PRIMARY_COLOR, type="dot", debug=SETTINGS.DEBUG_MODE, **kwargs
        )


def get_breadcrumb(parts):

    if not parts:
        return html.Div()

    breadcrumbs = html.Nav(
        html.Ul(
            [
                html.Li(
                    html.A(name, href=link),
                    className=(None if idx != len(parts) - 1 else "is-active"),
                )
                for idx, (name, link) in enumerate(parts.items())
            ]
        ),
        className="breadcrumb",
    )

    return breadcrumbs
