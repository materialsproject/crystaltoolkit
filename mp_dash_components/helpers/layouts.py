import dash_core_components as dcc
import dash_html_components as html

from typing import List

BULMA_CSS = {
    "external_url": "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css"
}

FONT_AWESOME_CSS = {
    "external_url": "https://use.fontawesome.com/releases/v5.6.3/css/all.css"
}


class Section(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "section"
        super().__init__(*args, **kwargs)


class Container(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "container"
        super().__init__(*args, **kwargs)


class Columns(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "columns"
        super().__init__(*args, **kwargs)


class Column(html.Div):
    def __init__(self, *args, size=None, offset=None, narrow=False, **kwargs):
        kwargs["className"] = "column"
        if size:
            kwargs["className"] += f" -is-{size}"
        if offset:
            kwargs["className"] += f" -is-offset-{size}"
        if narrow:
            kwargs["className"] += " -is-narrow"
        super().__init__(*args, **kwargs)


class Button(html.Button):
    def __init__(self, *args, button_kind=None, **kwargs):
        kwargs["className"] = "button"
        if button_kind:
            kwargs["className"] += f" is-{button_kind}"
        super().__init__(*args, **kwargs)


class Error(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "notification is-danger"
        super().__init__(*args, **kwargs)


class Warning(html.Div):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "notification is-warning"
        super().__init__(*args, **kwargs)


class Icon(html.Span):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "icon"
        super().__init__(*args, **kwargs)


class Footer(html.Footer):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "footer"
        super().__init__(*args, **kwargs)


class Spinner(html.Button):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "button is-primary is-loading"
        kwargs["style"] = {"width": "35px", "height": "35px", "border-radius": "40px"}
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
    def __init__(self, children=None, id=None, summary_title=None, **kwargs):
        if children is None:
            children = ["Loading..."]
        if id is None:
            id = summary_title
        contents_id = f"{id}_contents" if id else None
        super().__init__(
            [
                html.Summary(H4(summary_title, style={"display": "inline-block", "vertical-align": "middle"})),
                html.Div(children, id=contents_id),
            ],
            id=id,
            **kwargs,
        )


class Label(html.Label):
    def __init__(self, *args, **kwargs):
        kwargs["className"] = "label"
        super().__init__(*args, **kwargs)
