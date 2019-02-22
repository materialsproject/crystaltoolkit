import dash_core_components as dcc
import dash_html_components as html

from typing import List

BULMA_CSS = {
    "external_url": "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css"
}

FONT_AWESOME_CSS = {
    "external_url": "https://use.fontawesome.com/releases/v5.6.3/css/all.css"
}

# TODO: change "kind" kwarg to list / group is- modifiers together


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
            kwargs["className"] += f" -is-{size}"
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
        super().__init__(html.I(className=f"fa{fill} fa-{kind}"), *args, **kwargs)


class Footer(html.Footer):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "footer"
        super().__init__(*args, **kwargs)


class Spinner(html.Button):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "button is-primary is-loading"
        kwargs["style"] = {"width": "35px", "height": "35px", "border-radius": "35px"}
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
    def __init__(self, children=None, id=None, title=None, **kwargs):
        if children is None:
            children = ["Loading..."]
        if id is None and isinstance(title, str):
            id = title
        if isinstance(title, str):
            title = H4(
                title, style={"display": "inline-block", "vertical-align": "middle"}
            )
        contents_id = f"{id}_contents" if id else None
        summary_id = f"{id}_summary" if id else None
        kwargs["style"] = {"margin-bottom": "1rem"}
        super().__init__(
            [
                html.Summary(title, id=summary_id),
                html.Div(
                    children,
                    id=contents_id,
                    style={"margin-top": "0.5rem", "margin-left": "1.1rem"},
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
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "control"
        super().__init__(*args, **kwargs)


def get_tooltip(tooltip, tooltip_text):
    return html.Div(
        [tooltip, html.Span(tooltip_text, className="tooltiptext")], className="tooltip"
    )


def get_data_list(data):
    contents = []
    for title, value in data.items():
        contents.append(
            html.Tr(
                [html.Td(Label(title)), html.Td(value)]
            )
        )
    return html.Table([html.Tbody(contents)], className="table")


def get_table(rows):
    contents = []
    for row in rows:
        contents.append(
            html.Tr(
                [html.Td(item) for item in row]
            )
        )
    return html.Table([html.Tbody(contents)], className="table")

# reference_button = Button(
#    [Icon(kind="book"), html.Span("Cite me")],
#    size="small",
#    kind="link"
# )
