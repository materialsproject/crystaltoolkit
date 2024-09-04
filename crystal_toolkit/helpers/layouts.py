"""Helper methods to make working with Bulma classes easier. This file incorporates
language from the Bulma documentation. See https://github.com/jgthms/bulma/blob/master/LICENSE
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Literal, Sequence
from uuid import uuid4

import dash_mp_components as mpc
from dash import dcc, html
from monty.serialization import loadfn

from crystal_toolkit.settings import SETTINGS

if TYPE_CHECKING:
    from dash.development.base_component import Component

BulmaPrimaryColor = Literal[
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

# Developer note: Subclasses use `*args`` since common usage of html/dcc components
# is to use the `children` arg as a positional argument, and we want to continue
# to allow this here, unless we override the `children` argument in the subclass.


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
        *args,
        addons: bool = False,
        addons_centered: bool = False,
        addons_right: bool = False,
        grouped: bool = False,
        grouped_centered: bool = False,
        grouped_right: bool = False,
        grouped_multiline: bool = False,
        **kwargs,
    ) -> None:
        """When combining several controls in a form, use the field class as a container, to keep the spacing consistent.

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

        super().__init__(*args, **kwargs)


class Control(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """To maintain an evenly balanced design, Bulma provides a very useful control container with which you can wrap the form controls.

        See https://bulma.io/documentation/form/general/
        """
        # Developer note: has-icon-left etc. have not yet been tested with dcc Components
        _update_css_class(kwargs, "control")
        super().__init__(*args, **kwargs)


class Input(dcc.Input):
    def __init__(
        self,
        *args,
        color: BulmaPrimaryColor | None = None,
        size: Literal["small", "normal", "medium", "large"] | None = None,
        rounded: bool = False,
        **kwargs,
    ) -> None:
        """A dcc.Input with Bulma styles attached.

        See https://bulma.io/documentation/form/input/
        """
        _update_css_class(kwargs, "input")
        _update_css_class(kwargs, f"is-{color}", color)
        _update_css_class(kwargs, f"is-{size}", size)
        _update_css_class(kwargs, "is-rounded", rounded)

        super().__init__(*args, **kwargs)


class Textarea(dcc.Textarea):
    def __init__(
        self,
        *args,
        color: BulmaPrimaryColor | None = None,
        size: Literal["small", "medium", "large"] | None = None,
        fixed_size: bool = False,
        **kwargs,
    ) -> None:
        """A dcc.Textarea with Bulma styles attached.

        See https://bulma.io/documentation/form/textarea/
        """
        _update_css_class(kwargs, "textarea")
        _update_css_class(kwargs, f"is-{color}", color)
        _update_css_class(kwargs, f"is-{size}", size)
        _update_css_class(kwargs, "has-fixed-size", fixed_size)

        super().__init__(*args, **kwargs)


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
        """Returns a dcc.Upload with Bulma styling.

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

        super().__init__(children=html.Div(children, className="file"), **kwargs)


class Label(html.Label):
    def __init__(self, *args, **kwargs) -> None:
        # TODO docstring, use Field([Label(...), Control(...), Help(...)])
        _update_css_class(kwargs, "label")
        super().__init__(*args, **kwargs)


class Help(html.P):
    def __init__(self, *args, **kwargs) -> None:
        # TODO docstring, use Field([Label(...), Control(...), Help(...)])
        _update_css_class(kwargs, "help")
        super().__init__(*args, **kwargs)


# Bulma "Elements"
# See https://bulma.io/documentation/elements/


class Block(html.Div):
    """The block element is a simple spacer tool. It allows sibling HTML elements to have a consistent margin between them.

    See https://bulma.io/documentation/elements/block/
    """

    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "block")
        super().__init__(*args, **kwargs)


class Box(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """The box element is a simple container with a white background, some padding, and a box shadow.

        See https://bulma.io/documentation/elements/box/
        """
        _update_css_class(kwargs, "box")
        super().__init__(*args, **kwargs)


class Button(html.Button):
    def __init__(
        self,
        *args,
        kind: Literal[BulmaPrimaryColor, "ghost"] | None = None,
        size: Literal["small", "normal", "medium", "large"] | None = None,
        display: Literal["fullwidth"] | None = None,
        light: bool = False,
        outlined: bool = False,
        inverted: bool = False,
        rounded: bool = False,
        loading: bool = False,
        static: bool = False,
        **kwargs,
    ) -> None:
        """The button is an essential element of any design. It's meant to look and behave as an interactive element of your page.

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
        super().__init__(*args, **kwargs)


class Content(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """A single class to handle WYSIWYG generated content, where only HTML tags are available.

        It is useful to use Content around a Markdown component.

        See https://bulma.io/documentation/elements/content/
        """
        _update_css_class(kwargs, "content")
        super().__init__(*args, **kwargs)


class Delete(html.Div):
    def __init__(
        self,
        *args,
        size: Literal["small", "normal", "medium", "large"] | None,
        **kwargs,
    ) -> None:
        """A versatile delete cross.

        See https://bulma.io/documentation/elements/delete/
        """
        _update_css_class(kwargs, "delete")
        _update_css_class(kwargs, f"is-{size}", size)
        super().__init__(*args, **kwargs)


class Icon(html.Span):
    def __init__(
        self,
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
            super().__init__(children=html.I(**i_kwargs), **kwargs)
        else:
            _update_css_class(i_kwargs, kind)
            super().__init__(children=html.I(**i_kwargs), **kwargs)


class Image(html.Figure):
    def __init__(
        self,
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
        ]
        | None = None,
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
            super().__init__(children=html.Img(**img_kwargs), **kwargs)
        else:
            super().__init__(children=children, **kwargs)


class Notification(html.Div):
    def __init__(
        self,
        *args,
        color: BulmaPrimaryColor | None = None,
        light: bool = False,
        **kwargs,
    ) -> None:
        """The notification is a simple colored block meant to draw the attention to the user about something.

        See https://bulma.io/documentation/elements/notification/
        """
        _update_css_class(kwargs, "notification")
        _update_css_class(kwargs, f"is-{color}", color)
        _update_css_class(kwargs, "is-light", light)
        super().__init__(*args, **kwargs)


class Error(Notification):
    def __init__(self, *args, **kwargs) -> None:
        """A Notification for errors."""
        super().__init__(*args, color="danger", **kwargs)


class Progress(html.Progress):
    def __init__(
        self,
        *args,
        color: BulmaPrimaryColor | None = None,
        size: Literal["small", "normal", "medium", "large"] | None = None,
        indeterminate: bool = False,
        value: int | None = None,
        max: int | None = None,
        **kwargs,
    ) -> None:
        """Native HTML progress bars.

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
        """A simple Table element.

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
        _update_css_class(kwargs, "table")
        _update_css_class(kwargs, "is-bordered", bordered)
        _update_css_class(kwargs, "is-striped", striped)
        _update_css_class(kwargs, "is-narrow", narrow)
        _update_css_class(kwargs, "is-hoverable", hoverable)
        _update_css_class(kwargs, "is-fullwidth", fullwidth)
        super().__init__(*args, **kwargs)

    def with_container(self, **kwargs) -> html.Div:
        """Add a container to make the Table scrollable."""
        _update_css_class(kwargs, "table-container")
        return html.Div(children=[self], **kwargs)


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
        """A tag element.

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
        _update_css_class(span_kwargs, "is-rounded", rounded)
        _update_css_class(span_kwargs, "is-delete", delete)

        tags = [html.Span(tag, **span_kwargs)]

        if addon:
            addon_kwargs = span_kwargs.copy()
            _update_css_class(addon_kwargs, f"is-{color}", addon_color)
            tags.append(html.Span(addon, **addon_kwargs))

            _update_css_class(kwargs, "tags has-addons")
            super().__init__(children=tags, **kwargs)
        else:
            super().__init__(children=tags, **kwargs)


class TagContainer(Field):
    def __init__(
        self, tags: list[Tag], grouped=True, grouped_multiline=True, **kwargs
    ) -> None:
        """Contain a list of tags and keep them evenly spaced.

        See https://bulma.io/documentation/elements/tag/
        """
        # Developer note: this class is a bit awkward. It has to
        # assume the children tags *might* contain addons, which
        # changes the class being used.
        tags = [Control(tag) for tag in tags]
        super().__init__(
            children=tags,
            grouped=grouped,
            grouped_multiline=grouped_multiline,
            **kwargs,
        )


class H1(html.H1):
    def __init__(
        self, *args, subtitle: bool = False, spaced: bool = False, **kwargs
    ) -> None:
        """H1 heading.

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
        """H2 heading.

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
        """H3 heading.

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
        """H4 heading.

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
        """H5 heading.

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
        """H6 heading.

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


class Breadcrumb(html.Nav):
    def __init__(
        self,
        parts: Sequence[tuple[str | Component, str]],
        alignment: Literal["centered", "right"] | None = None,
        separator: Literal["arrow", "bullet", "dot", "succeeds"] | None = None,
        size: Literal["small", "medium", "large"] | None = None,
        **kwargs,
    ) -> None:
        """Breadcrumb navigation. Supply a list of tuples of display
        name (string or any Component) and link (string) to construct the breadcrumb navigation.

        See https://bulma.io/documentation/components/breadcrumb/
        """
        _update_css_class(kwargs, "breadcrumb")
        _update_css_class(kwargs, f"is-{alignment}", alignment)
        _update_css_class(kwargs, f"has-{separator}-separator", separator)
        _update_css_class(kwargs, f"is-{size}", size)

        if isinstance(parts, dict):
            # For backwards compatibility, no longer recommended.
            parts = parts.items()

        links = [
            html.Li(
                dcc.Link(name, href=link),
                className="is-active" if idx == len(parts) - 1 else None,
            )
            for idx, (name, link) in enumerate(parts)
        ]

        kwargs["aria-label"] = "breadcrumbs"
        super(links).__init__(**kwargs)


class Card(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """Card container.

        See https://bulma.io/documentation/components/card/
        """
        _update_css_class(kwargs, "card")
        super().__init__(*args, **kwargs)


class CardHeader(html.Header):
    def __init__(self, *args, **kwargs) -> None:
        """Card header.

        See https://bulma.io/documentation/components/card/
        """
        _update_css_class(kwargs, "card-header")
        super().__init__(*args, **kwargs)


class CardImage(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """Card image. Provide a ctl.Image() as child.

        See https://bulma.io/documentation/components/card/
        """
        _update_css_class(kwargs, "card-header")
        super().__init__(*args, **kwargs)


class CardContent(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """Card content.

        See https://bulma.io/documentation/components/card/
        """
        _update_css_class(kwargs, "card-content")
        super().__init__(*args, **kwargs)


class CardFooter(html.Footer):
    def __init__(self, *args, **kwargs) -> None:
        """Card footer. Provide a list of ctl.CardFooterItem() as children.

        See https://bulma.io/documentation/components/card/
        """
        _update_css_class(kwargs, "card-footer")
        super().__init__(*args, **kwargs)


class CardFooterItem(html.A):
    def __init__(self, *args, **kwargs) -> None:
        """Card footer item.

        See https://bulma.io/documentation/components/card/
        """
        _update_css_class(kwargs, "card-footer-item")
        super().__init__(*args, **kwargs)


class Dropdown:
    # TODO: see if dcc.Dropdown can be styled with Bulma styles.
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("Not implemented, prefer dcc.Dropdown.")


class Menu:
    # TODO: map this to Scrollspy component automatically?
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError(
            "Not implemented, prefer dash_mp_components.Scrollspy menu which uses Bulma styles."
        )


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
    # rename to Message
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "message-header")
        super().__init__(*args, **kwargs)


class MessageBody(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "message-body")
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


class Navbar:
    # TODO: map this to Navbar component automatically?
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError(
            "Not implemented, prefer dash_mp_components.Navbar menu which uses Bulma styles."
        )


class Pagination(html.Nav):
    def __init__(self, *args, **kwargs) -> None:
        """Pagination container.

        See https://bulma.io/documentation/components/pagination/
        """
        _update_css_class(kwargs, "pagination")
        super().__init__(*args, **kwargs)


class PaginationPrevious(html.A):
    def __init__(self, *args, **kwargs) -> None:
        """Pagination previous button.

        See https://bulma.io/documentation/components/pagination/
        """
        _update_css_class(kwargs, "pagination-previous")
        super().__init__(*args, **kwargs)


class PaginationNext(html.A):
    def __init__(self, *args, **kwargs) -> None:
        """Pagination next button.

        See https://bulma.io/documentation/components/pagination/
        """
        _update_css_class(kwargs, "pagination-next")
        super().__init__(*args, **kwargs)


class PaginationList(html.Ul):
    def __init__(self, *args, **kwargs) -> None:
        """Pagination list container. Provide list of ctl.PaginationLink as children.

        See https://bulma.io/documentation/components/pagination/
        """
        _update_css_class(kwargs, "pagination-list")
        super().__init__(*args, **kwargs)


class PaginationLink(html.Li):
    def __init__(self, *args, current: bool, **kwargs) -> None:
        """Pagination link. Keyword arguments passed to html.A element.

        See https://bulma.io/documentation/components/pagination/
        """
        _update_css_class(kwargs, "pagination-link")
        _update_css_class(kwargs, "is-current", current)
        super().__init__(html.A(*args, **kwargs))


class PaginationEllipsis(html.Li):
    def __init__(self, **kwargs) -> None:
        """Pagination link. Keyword arguments passed to html.Span element.

        See https://bulma.io/documentation/components/pagination/
        """
        _update_css_class(kwargs, "pagination-ellipsis")
        super().__init__(html.Span("&hellip;", **kwargs))


class Panel:
    # TODO, https://bulma.io/documentation/components/panel/
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError


class PanelHeading:
    # TODO, https://bulma.io/documentation/components/panel/
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError


class PanelTabs:
    # TODO, https://bulma.io/documentation/components/panel/
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError


class PanelBlock:
    # TODO, https://bulma.io/documentation/components/panel/
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError


class Tabs:
    # TODO: see if dcc.Tabs can be styled with Bulma styles.
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("Not implemented, prefer dcc.Tabs.")


# Bulma "Layout"
# See https://bulma.io/documentation/layout/


class Container(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        _update_css_class(kwargs, "container")
        super().__init__(*args, **kwargs)


class Level(html.Nav):
    def __init__(
        self,
        *args,
        mobile: bool = False,
        **kwargs,
    ) -> None:
        """A multi-purpose horizontal level, which can contain almost any other element.

        Use either ctl.LevelLeft, ctl.LevelRight or ctl.LevelItem as children.

        See https://bulma.io/documentation/layout/level/
        """
        _update_css_class(kwargs, "level")
        _update_css_class(kwargs, f"is-{mobile}", mobile)
        super().__init__(*args, **kwargs)


class LevelLeft(html.Div):
    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        """Use with ctl.Level.

        See https://bulma.io/documentation/layout/level/
        """
        _update_css_class(kwargs, "level-left")
        super().__init__(*args, **kwargs)


class LevelRight(html.Div):
    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        """Use with ctl.Level.

        See https://bulma.io/documentation/layout/level/
        """
        _update_css_class(kwargs, "level-right")
        super().__init__(*args, **kwargs)


class LevelItem(html.Div):
    def __init__(
        self,
        *args,
        centered: bool = False,
        **kwargs,
    ) -> None:
        """Use with ctl.Level.

        See https://bulma.io/documentation/layout/level/
        """
        _update_css_class(kwargs, "level-item")
        _update_css_class(kwargs, "has-text-centered", centered)
        super().__init__(*args, **kwargs)


class MediaObject:
    # TODO, https://bulma.io/documentation/layout/media-object/
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError


class Hero(html.Div):
    def __init__(
        self,
        *args,
        color: BulmaPrimaryColor | None = None,
        size: Literal["small", "medium", "large", "halfheight", "fullheight"]
        | None = None,
        **kwargs,
    ) -> None:
        """Hero element. Provide a ctl.HeroBody() as child and, if using "fullheight", a
        ctl.HeroHead() and ctl.HeroFoot().

        See https://bulma.io/documentation/layout/hero/
        """
        _update_css_class(kwargs, "hero")
        _update_css_class(kwargs, f"is-{color}", color)
        _update_css_class(kwargs, f"is-{size}", size)
        super().__init__(*args, **kwargs)


class HeroBody(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """Use with ctl.Hero.

        See https://bulma.io/documentation/layout/hero/
        """
        _update_css_class(kwargs, "hero-body")
        super().__init__(*args, **kwargs)


class HeroHead(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """Use with "fullheight" ctl.Hero.

        See https://bulma.io/documentation/layout/hero/
        """
        _update_css_class(kwargs, "hero-head")
        super().__init__(*args, **kwargs)


class HeroFoot(html.Div):
    def __init__(self, *args, **kwargs) -> None:
        """Use with "fullheight" ctl.Hero.

        See https://bulma.io/documentation/layout/hero/
        """
        _update_css_class(kwargs, "hero-foot")
        super().__init__(*args, **kwargs)


class Section(html.Section):
    def __init__(
        self, *args, size: Literal["medium", "large"] | None = None, **kwargs
    ) -> None:
        """Section.

        See https://bulma.io/documentation/layout/section/
        """
        _update_css_class(kwargs, "section")
        _update_css_class(kwargs, f"is-{size}", size)
        super().__init__(*args, **kwargs)


class Footer(html.Footer):
    def __init__(self, *args, **kwargs) -> None:
        """Footer.

        See https://bulma.io/documentation/layout/footer/
        """
        _update_css_class(kwargs, "footer")
        super().__init__(*args, **kwargs)


class Tile(html.Div):
    def __init__(
        self,
        *args,
        context: Literal["ancestor", "parent", "child"] | None = None,
        vertical: bool = False,
        size: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] | None,
        **kwargs,
    ) -> None:
        """A single tile element to build 2-dimensional grids.

        See https://bulma.io/documentation/layout/tiles/
        """
        _update_css_class(kwargs, "tile")
        _update_css_class(kwargs, f"is-{context}", context)
        _update_css_class(kwargs, "is-vertical", vertical)
        _update_css_class(kwargs, f"is-{size}", size)
        super().__init__(*args, **kwargs)


# Bulma "Columns"
# See https://bulma.io/documentation/columns/


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


# Non-Bulma helpers


# TODO: review
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


# TODO: review
def add_label_help(input, label, help) -> mpc.FilterField:
    """Combine an input, label, and tooltip text into a single consistent component."""
    return mpc.FilterField(input, id=uuid4().hex, label=label, tooltip=help)


# TODO: review
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


# TODO: review
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


class Loading(dcc.Loading):
    def __init__(self, *args, **kwargs) -> None:
        """A wrapper around dcc.Loading that uses PRIMARY_COLOR and DEBUG_MODE from
        Crystal Toolkit settings.
        """
        if "type" not in kwargs:
            kwargs["type"] = "dot"
        super().__init__(
            *args, color=SETTINGS.PRIMARY_COLOR, debug=SETTINGS.DEBUG_MODE, **kwargs
        )


# DEPRECATED. Everything from here to the end of the file is deprecated. There is no
# immediate plan to remove these variables or functions which are fairly harmless,
# but please do not use in new projects.

PRIMARY_COLOR = SETTINGS.PRIMARY_COLOR

BULMA_CSS = {"external_url": SETTINGS.BULMA_CSS_URL}

FONT_AWESOME_CSS = {"external_url": SETTINGS.FONT_AWESOME_CSS_URL}

DOI_CACHE = loadfn(SETTINGS.DOI_CACHE_PATH) if SETTINGS.DOI_CACHE_PATH else {}


def get_table(rows: list[list[Any]], header: list[str] | None = None) -> html.Table:
    """Deprecated. Prefer ctl.Table class instead.

    Create a HTML table from a list of elements.

    :param rows: list of list of cell contents
    :return: html.Table
    """
    contents = [html.Tr([html.Td(item) for item in row]) for row in rows]
    if not header:
        return html.Table([html.Tbody(contents)], className="table")
    header = html.Thead([html.Tr([html.Th(item) for item in header])])
    return html.Table([header, html.Tbody(contents)], className="table")


def get_tooltip(
    tooltip_label: Any,
    tooltip_text: str,
    underline: bool = True,
    tooltip_id: str = "",
    wrapper_class: str | None = None,
    **kwargs,
):
    """Deprecated. Prefer alternative dcc.Tooltip component instead.

    Uses the tooltip component from dash-mp-components to add a tooltip, typically for help text.
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


def get_breadcrumb(parts):
    """Deprecated, prefer the ctl.Breadcrumb class instead, which is a drop-in replacement.

    Create a breadcrumb navigation bar.

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


class Spinner(html.Button):
    def __init__(self, *args, **kwargs) -> None:
        """Deprecated, prefer ctl.Button class instead with loading=True keyword argument."""
        _update_css_class(kwargs, "button is-primary is-loading")
        kwargs["style"] = {"width": "35px", "height": "35px", "borderRadius": "35px"}
        kwargs["aria-label"] = "Loading"
        super().__init__(*args, **kwargs)
