import dash_core_components as dcc
import dash_html_components as html


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


class Row: pass

class Button(html.Button):

    def __init__(self, *args, button_kind=None, **kwargs):
        kwargs["className"] = "button"
        if button_kind:
            kwargs["className"] += f" is-{button_kind}"
        super().__init__(*args, **kwargs)

class Error: pass

class Icon(html.Span):

    def __init__(self, *args, **kwargs):
        kwargs["className"] = "icon"
        super().__init__(*args, **kwargs)


class Footer(html.Footer):

    def __init__(self, *args, **kwargs):
        kwargs["className"] = "footer"
        super().__init__(*args, **kwargs)

class Spinner: pass


class Options: pass

class Box: pass


class H1: pass
class H2: pass
class H3: pass
class H4: pass
class H5: pass
class H6: pass
