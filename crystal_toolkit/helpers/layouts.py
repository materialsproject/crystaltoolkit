from __future__ import annotations

import warnings
from typing import Any, Literal, TypeAlias
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

BulmaSize: TypeAlias = Literal["small", "normal", "medium", "large"]

BulmaPrimaryColor: TypeAlias = Literal[
    "white",
    "black",
    "light",
    "dark",
    "primary",
    "link",
    "info",
    "success",
    "warning",
    "danger",
]

# TODO: change "kind" kwarg to list / group is- modifiers together?

"""
Helper methods to make working with Bulma classes easier. This file incorporates 
language from the Bulma documentation. See https://github.com/jgthms/bulma/blob/master/LICENSE
"""

__all__ = [
    "Field",
    "Control",
    "Input",
    "Textarea",
    "Select",
    "Checkbox",
    "Radio",
    "File",
    "Block",
    "Box",
    "Button",
    "Content",
    "Delete",
    "Icon",
    "Image",
    "Notification",
    "Error",
    "Progress",
    "Table",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
]


def _update_css_class(kwargs, class_name, conditional=True):
    """Convenience function to update className while respecting any additional classNames already
    set.
    """
    if conditional:
        if "className" in kwargs:
            kwargs["className"] += f" {class_name}"
        else:
            kwargs["className"] = class_name


# Bulma "Form"
# See https://bulma.io/documentation/form/general/


class Field(html.Div):
    def __init__(
        self,
        addons: bool = False,
        addons_centered: bool = False,
        addons_right: bool = False,
        grouped: bool = False,
        grouped_centered: bool = False,
        grouped_right: bool = False,
        grouped_multiline: bool = False,
        **kwargs,
    ) -> None:
        """
        When combining several controls in a form, use the field class as a container, to keep the spacing consistent.

        See https://bulma.io/documentation/form/general/
        """
        _update_css_class(kwargs, "field")

        _update_css_class(kwargs, "has-addons", addons)
        _update_css_class(kwargs, "has-addons-centered", addons_centered)
        _update_css_class(kwargs, "has-addons_right", addons_right)
        _update_css_class(kwargs, "is-grouped", grouped)
        _update_css_class(kwargs, "is-grouped-centered", grouped_centered)
        _update_css_class(kwargs, "is-grouped-right", grouped_right)
        _update_css_class(kwargs, "is-grouped-multiline", grouped_multiline)

        super().__init__(**kwargs)


class Control(html.Div):
    def __init__(self, **kwargs) -> None:
        """
        To maintain an evenly balanced design, Bulma provides a very useful control container with which you can wrap the form controls.

        See https://bulma.io/documentation/form/general/
        """
        # Developer note: has-icon-left etc. have not yet been tested with dcc Components
        _update_css_class(kwargs, "control")
        super().__init__(**kwargs)


class Input(dcc.Input):
    def __init__(
        self,
        color: BulmaPrimaryColor | None = None,
        size: Literal["small", "normal", "medium", "large"] | None = None,
        rounded: bool = False,
        **kwargs,
    ) -> None:
        """
        A dcc.Input with Bulma styles attached.

        See https://bulma.io/documentation/form/input/
        """

        _update_css_class(kwargs, "input")
        _update_css_class(kwargs, f"is-{color}", color)
        _update_css_class(kwargs, f"is-{size}", size)
        _update_css_class(kwargs, "is-rounded", rounded)

        super().__init__(**kwargs)


class Textarea(dcc.Textarea):
    def __init__(
        self,
        color: BulmaPrimaryColor | None = None,
        size: Literal["small", "medium", "large"] | None = None,
        fixed_size: bool = False,
        **kwargs,
    ) -> None:
        """
        A dcc.Textarea with Bulma styles attached.

        See https://bulma.io/documentation/form/textarea/
        """
        _update_css_class(kwargs, "textarea")
        _update_css_class(kwargs, f"is-{color}", color)
        _update_css_class(kwargs, f"is-{size}", size)
        _update_css_class(kwargs, "has-fixed-size", fixed_size)

        super().__init__(**kwargs)


class Select:
    # TODO: see if dcc.Dropdown can be styled with Bulma styles.
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("Not implemented, prefer dcc.Dropdown.")


class Checkbox:
    # TODO: see if dcc.Checklist can be styled with Bulma styles.
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("Not implemented, prefer dcc.Checklist.")


class Radio:
    # TODO: see if dcc.RadioItems can be styled with Bulma styles.
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("Not implemented, prefer dcc.RadioItems.")


class File(dcc.Upload):
    def __init__(
        self,
        icon: str | None = "upload",
        label: str | None = "Choose a file...",
        alignment: Literal["centered", "right"] | None = None,
        fullwidth: bool = False,
        boxed: bool = False,
        color: BulmaPrimaryColor | None = None,
        size: Literal["small", "normal", "medium", "large"] | None = None,
        placeholder: str | None = None,
        **kwargs,
    ) -> None:
        """
        Returns a dcc.Upload with Bulma styling.

        See https://bulma.io/documentation/form/file/
        """
        div_kwargs = {"className": "file"}

        children = []
        if icon or label:
            cta = html.Span(className="file-cta")
            if icon:
                cta.children.append(Icon(kind=icon))
            if label:
                cta.children.append(html.Span(label, className="file-label"))
            children.append(cta)

        if placeholder:
            _update_css_class(div_kwargs, "has_name")
            children.append(html.Span(placeholder, className="file-name"))

        _update_css_class(div_kwargs, f"is-{alignment}", alignment)
        _update_css_class(div_kwargs, "is-fullwidth", fullwidth)
        _update_css_class(div_kwargs, "is-boxed", boxed)
        _update_css_class(div_kwargs, f"is-{color}", color)
        _update_css_class(div_kwargs, f"is-{size}", size)

        return dcc.Upload(children=html.Div(children, className="file"), **kwargs)


# Bulma "Elements"
# See https://bulma.io/documentation/elements/


class Block(html.Div):
    """
    The block element is a simple spacer tool. It allows sibling HTML elements to have a consistent margin between them.

    See https://bulma.io/documentation/elements/block/
    """

    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "block")
        super().__init__(*args, **kwargs)


class Box(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """
        The box element is a simple container with a white background, some padding, and a box shadow.

        See https://bulma.io/documentation/elements/box/
        """
        _update_css_class(kwargs, "box")
        super().__init__(*args, **kwargs)


class Button(html.Button):
    def __init__(
        self,
        *args,
        kind: Literal[BulmaPrimaryColor, "ghost"] | None = None,
        size: BulmaSize | None = None,
        display: Literal["fullwidth"] | None = None,
        light: bool = False,
        outlined: bool = False,
        inverted: bool = False,
        rounded: bool = False,
        loading: bool = False,
        static: bool = False,
        disabled: bool = False,
        **kwargs,
    ) -> None:
        """
        The button is an essential element of any design. It's meant to look and behave as an interactive element of your page.

        See https://bulma.io/documentation/elements/button/
        """
        _update_css_class(kwargs, "button")
        _update_css_class(kwargs, f"is-{size}", size)
        _update_css_class(kwargs, f"is-{kind}", kind)
        _update_css_class(kwargs, f"is-{display}", display)
        _update_css_class(kwargs, "is-light", light)
        _update_css_class(kwargs, "is-outlined", outlined)
        _update_css_class(kwargs, "is-inverted", inverted)
        _update_css_class(kwargs, "is-rounded", rounded)
        _update_css_class(kwargs, "is-loading", loading)
        _update_css_class(kwargs, "is-static", static)
        _update_css_class(kwargs, "is-disabled", disabled)
        super().__init__(*args, **kwargs)


class Content(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """
        A single class to handle WYSIWYG generated content, where only HTML tags are available.

        It is useful to use Content around a Markdown component.

        See https://bulma.io/documentation/elements/content/
        """
        _update_css_class(kwargs, "content")
        super().__init__(*args, **kwargs)


class Delete(html.Div):
    def __init__(self, *args, size: BulmaSize | None, **kwargs) -> None:
        """
        A versatile delete cross.

        See https://bulma.io/documentation/elements/delete/
        """
        _update_css_class(kwargs, "delete")
        _update_css_class(kwargs, f"is-{size}", size)
        super().__init__(*args, **kwargs)


class Icon(html.Span):
    def __init__(
        self,
        *args,
        kind: str = "download",
        fill: Literal["s", "r", "l", "d"] = "s",
        fontawesome: bool = True,
        size: Literal["small", "medium", "large"] | None = None,
        color: BulmaPrimaryColor | None = None,
        i_kwargs: dict | None = None,
        **kwargs,
    ) -> None:
        """Bulma is compatible with all icon font libraries: Font Awesome 5, Font Awesome 4, Material Design Icons, Ionicons, etc.

        See also https://bulma.io/documentation/elements/icon/

        Here, we assume using Font Awesome, where "kind" is a Font Awesome icon
        such as "info-circle", "question-circle", "book" or "code", and "fill"
        specifies whether it is solid ("s"), regular ("r"), light ("l") or
        duotone ("d"). See fontawesome.com for more.

        If not using Font Awesome, set fontawesome to False.

        An Icon is a html.Span(html.I()), i_kwargs get passed to the
        html.I element.
        """
        _update_css_class(kwargs, "icon")
        _update_css_class(kwargs, f"is-{size}", size)
        _update_css_class(kwargs, f"has-text-{color}", color)

        # fontastic styles (custom icons, e.g. the MP app icons)
        if "fontastic" in kind:
            fontawesome = False

        i_kwargs = i_kwargs or {}

        # fontawesome styles (pre-distributed icons, e.g. download)
        if fontawesome:
            _update_css_class(i_kwargs, f"fa{fill} fa-{kind}")
            super().__init__(html.I(**i_kwargs), *args, **kwargs)
        else:
            _update_css_class(i_kwargs, kind)
            super().__init__(html.I(**i_kwargs), *args, **kwargs)


class Image(html.Figure):
    def __init__(
        self,
        *args,
        square_size: Literal[16, 24, 32, 48, 64, 96, 128] | None = None,
        ratio: Literal[
            "square",
            "1by1",
            "5by4",
            "4by3",
            "3by2",
            "5by3",
            "16by9",
            "2by1",
            "3by1",
            "4by5",
            "3by4",
            "2by3",
            "3by5",
            "9by16",
            "1by2",
            "1by3",
        ] = None,
        rounded: bool = False,
        img_kwargs: dict | None = None,
        src: str | None = None,
        alt: str | None = None,
        children=None,
        **kwargs,
    ) -> None:
        """A container for responsive images.

        See https://bulma.io/documentation/elements/image/

        An Image is typically a html.Figure(html.Img()), img_kwargs get passed to the
        html.Img element. For convenience, src and alt kwargs are also provided, and
        these will also get passed to the html.Img element.

        If children are specified, these will be used instead of the html.Img
        (for example, to maintain the ratio of an iframe).
        """
        _update_css_class(kwargs, "image")
        _update_css_class(kwargs, f"is-{square_size}x{square_size}", square_size)
        _update_css_class(kwargs, f"is-{ratio}", ratio)
        _update_css_class(kwargs, "is-rounded", rounded)
        if not children:
            img_kwargs = img_kwargs or {}
            if src and src not in img_kwargs:
                img_kwargs[src] = src
            if alt and alt not in img_kwargs:
                img_kwargs[alt] = alt
            return super().__init__(html.Img(**img_kwargs), *args, **kwargs)
        else:
            return super().__init__(children, *args, **kwargs)


class Notification(html.Div):
    def __init__(
        self,
        *args,
        color: BulmaPrimaryColor | None = None,
        light: bool = False,
        **kwargs,
    ) -> None:
        """
        The notification is a simple colored block meant to draw the attention to the user about something.

        See https://bulma.io/documentation/elements/notification/
        """
        _update_css_class(kwargs, "notification")
        _update_css_class(kwargs, f"is-{color}", color)
        _update_css_class(kwargs, "is-light", light)
        super().__init__(*args, **kwargs)


class Error(Notification):
    def __init__(self, *args, **kwargs) -> None:
        """
        A Notification for errors.
        """
        super().__init__(*args, color="danger", **kwargs)


class Progress(html.Progress):
    def __init__(
        self,
        *args,
        color: BulmaPrimaryColor | None = None,
        size: BulmaSize | None = None,
        indeterminate: bool = False,
        value: int | None = None,
        max: int | None = None,
        **kwargs,
    ) -> None:
        """
        Native HTML progress bars.

        See https://bulma.io/documentation/elements/progress/
        """
        _update_css_class(kwargs, "progress")
        _update_css_class(kwargs, color, f"is-{color}", color)
        _update_css_class(kwargs, size, f"is-{size}", size)
        if indeterminate:
            value = None
        if value:
            kwargs["value"] = value
        if max:
            kwargs["max"] = max
        super().__init__(*args, **kwargs)


class Table(html.Table):
    def __init__(
        self,
        *args,
        bordered: bool = False,
        striped: bool = False,
        narrow: bool = False,
        hoverable: bool = False,
        fullwidth: bool = False,
        **kwargs,
    ) -> None:
        """
        A simple Table element.

        See https://bulma.io/documentation/elements/table/

        Typically users are expected to use DataTable or AgGrid instead
        for any tables that require interactivity.

        Use with:

        * html.Thead, the optional top part of the table
        * html.Tfoot, the optional bottom part of the table
        * html.Tbody the main content of the table
        * html.Tr, each table row
        * html.Th, a table cell heading
        * html.Td, a table cell
        """
        html.Th
        _update_css_class(kwargs, "table")
        _update_css_class(kwargs, "is-bordered", bordered)
        _update_css_class(kwargs, "is-striped", striped)
        _update_css_class(kwargs, "is-narrow", narrow)
        _update_css_class(kwargs, "is-hoverable", hoverable)
        _update_css_class(kwargs, "is-fullwidth", fullwidth)

    def with_container(self, *args, **kwargs) -> html.Div:
        """
        Add a container to make the Table scrollable.
        """
        _update_css_class(kwargs, "table-container")
        return html.Div([self], *args, **kwargs)


class Tag(html.Div):
    def __init__(
        self,
        tag: str,
        color: BulmaPrimaryColor | None = "primary",
        size: Literal["normal", "medium", "large"] | None = None,
        rounded: bool = False,
        delete: bool = False,
        addon: str | None = None,
        addon_color: BulmaPrimaryColor | None = "primary",
        span_kwargs: dict | None = None,
        **kwargs,
    ) -> None:
        """
        A tag element.

        See https://bulma.io/documentation/elements/tag/

        kwargs are passed to the container Div, span_kwargs to the inner
        html.Span element.
        """
        # Developer note: this class is a bit awkward. It assumes a tag is a
        # html.Span, but it could be a html.A, etc. It also has to handle
        # both a Tag and a Tag with addons (technically a container + two Tags)

        # for backwards compatibility
        if tag_type := kwargs.get("tag_type"):
            color = tag_type
        if tag_addon_type := kwargs.get("tag_addon_type"):
            addon_color = tag_addon_type
        if tag_addon := kwargs.get("tag_addon"):
            addon = tag_addon

        span_kwargs = span_kwargs or {}
        _update_css_class(span_kwargs, "tag")
        _update_css_class(span_kwargs, f"is-{color}", color)
        _update_css_class(span_kwargs, f"is-{size}", size)
        _update_css_class(span_kwargs, f"is-rounded", rounded)
        _update_css_class(span_kwargs, f"is-delete", delete)

        tags = [html.Span(tag, **span_kwargs)]

        if addon:
            addon_kwargs = span_kwargs.copy()
            _update_css_class(addon_kwargs, f"is-{color}", addon_color)
            tags.append(html.Span(addon, **addon_kwargs))

            _update_css_class(kwargs, "tags has-addons")
            super().__init__(tags, **kwargs)
        else:
            super().__init__(tags, **kwargs)


class TagContainer(Field):
    def __init__(
        self, tags: list[Tag], grouped=True, grouped_multiline=True, **kwargs
    ) -> None:
        """
        Contain a list of tags and keep them evenly spaced.

        See https://bulma.io/documentation/elements/tag/
        """
        # Developer note: this class is a bit awkward. It has to
        # assume the children tags *might* contain addons, which
        # changes the class being used.
        tags = [Control(tag) for tag in tags]
        super().__init__(
            tags, grouped=grouped, grouped_multiline=grouped_multiline, **kwargs
        )


class H1(html.H1):
    def __init__(
        self, *args, subtitle: bool = False, spaced: bool = False, **kwargs
    ) -> None:
        """
        H1 heading.

        See https://bulma.io/documentation/elements/title/
        """
        if not subtitle:
            _update_css_class(kwargs, "title is-1")
        else:
            _update_css_class(kwargs, "subtitle is-1")
        _update_css_class(kwargs, "is-spaced", spaced)
        super().__init__(*args, **kwargs)


class H2(html.H2):
    def __init__(
        self, *args, subtitle: bool = False, spaced: bool = False, **kwargs
    ) -> None:
        """
        H2 heading.

        See https://bulma.io/documentation/elements/title/
        """
        if not subtitle:
            _update_css_class(kwargs, "title is-2")
        else:
            _update_css_class(kwargs, "subtitle is-2")
        _update_css_class(kwargs, "is-spaced", spaced)
        super().__init__(*args, **kwargs)


class H3(html.H3):
    def __init__(
        self, *args, subtitle: bool = False, spaced: bool = False, **kwargs
    ) -> None:
        """
        H3 heading.

        See https://bulma.io/documentation/elements/title/
        """
        if not subtitle:
            _update_css_class(kwargs, "title is-3")
        else:
            _update_css_class(kwargs, "subtitle is-3")
        _update_css_class(kwargs, "is-spaced", spaced)
        super().__init__(*args, **kwargs)


class H4(html.H4):
    def __init__(
        self, *args, subtitle: bool = False, spaced: bool = False, **kwargs
    ) -> None:
        """
        H4 heading.

        See https://bulma.io/documentation/elements/title/
        """
        if not subtitle:
            _update_css_class(kwargs, "title is-4")
        else:
            _update_css_class(kwargs, "subtitle is-4")
        _update_css_class(kwargs, "is-spaced", spaced)
        super().__init__(*args, **kwargs)


class H5(html.H5):
    def __init__(
        self, *args, subtitle: bool = False, spaced: bool = False, **kwargs
    ) -> None:
        """
        H5 heading.

        See https://bulma.io/documentation/elements/title/
        """
        if not subtitle:
            _update_css_class(kwargs, "title is-5")
        else:
            _update_css_class(kwargs, "subtitle is-5")
        _update_css_class(kwargs, "is-spaced", spaced)
        super().__init__(*args, **kwargs)


class H6(html.H6):
    def __init__(
        self, *args, subtitle: bool = False, spaced: bool = False, **kwargs
    ) -> None:
        """
        H6 heading.

        See https://bulma.io/documentation/elements/title/
        """
        if not subtitle:
            _update_css_class(kwargs, "title is-6")
        else:
            _update_css_class(kwargs, "subtitle is-6")
        _update_css_class(kwargs, "is-spaced", spaced)
        super().__init__(*args, **kwargs)


# Bulma "Components"
# See https://bulma.io/documentation/components/


class Section(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "section")
        super().__init__(*args, **kwargs)


class Container(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "container")
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
