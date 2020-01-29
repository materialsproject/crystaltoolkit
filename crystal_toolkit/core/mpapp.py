from abc import ABC, abstractmethod
from crystal_toolkit.core.mpcomponent import MPComponent

from crystal_toolkit.helpers.layouts import *


def get_mp_app_icon(shortname):
    """
    Get an MP app icon, using the MP fontastic font.
    :param shortname: the name used for the app url, e.g. "xas"
    :return:
    """
    return html.Span(
        [html.Span(className=f"icon-fontastic-{shortname}")],
        className="icon is-large",
        style={
            "borderRadius": "50%",
            "fontSize": "1.5rem",
            "color": "#4bbdb4",
            "backgroundColor": "#2c3e50",
            "marginRight": "1rem",
            "verticalAlign": "middle",
            "boxShadow": "0 2px 5px 0 rgba(0, 0, 0, 0.26)",
        },
    )


class MPApp(MPComponent, ABC):
    """
    Class to make an app for the Materials Project website.
    """

    @property
    @abstractmethod
    def name(self):
        """
        Name of your app, will be included in navigation menu
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self):
        """
        Short description of app (max 140 characters).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def url(self):
        """
        URL of your app, will set its url as https://materialsproject.org/{url}
        """
        raise NotImplementedError

    @property
    def long_description(self):
        """
        Extended text giving an explanation of your app. Formatted sa Markdown.
        """
        return ""

    @property
    def dois(self) -> List[str]:
        """
        :return: A list of DOI(s) to cite when using this app
        """
        return []

    def _sub_layouts(self):
        raise {}

    def generate_callbacks(self, app, cache):
        pass

    def get_layout(self, payload=None):
        """
        Return a Dash layout for the app. If the app requires any
        global set-up before a layout can be generated, put this in
        the app's initializer.

        :param payload: anything in the URL after
        https://materialsproject.org/your_app_name/
        """
        raise NotImplementedError

    def get_mp_layout(self, payload=None):
        """
        Returns your layout with added Materials Project styling.
        Do not override this method.

        :param payload: anything in the URL after
        https://materialsproject.org/your_app_name/
        :return:
        """

        icon = get_mp_app_icon(self.url)

        if self.dois:
            citation = [
                html.Span(
                    cite_me(doi=doi, cite_text="Cite this app"),
                    style={
                        "display": "inline-block",
                        "verticalAlign": "middle",
                        "marginLeft": "1rem",
                    },
                )
                for doi in self.dois
            ]
        else:
            citation = []

        return Container(
            [
                Columns(
                    Column(
                        [
                            html.Br(),
                            html.Div(
                                [
                                    H2(
                                        [
                                            icon,
                                            html.Span(
                                                self.name,
                                                style={"verticalAlign": "middle"},
                                            ),
                                        ],
                                        style={"display": "inline-block"},
                                    ),
                                    *citation,
                                ]
                            ),
                            html.Div(
                                [
                                    html.Div(id="breadcrumb"),
                                    html.Br(),
                                    dcc.Markdown(self.long_description),
                                ],
                                style={"marginLeft": "4rem"},
                            ),
                        ]
                    )
                ),
                Columns(Column([self.get_layout(payload=payload)])),
            ]
        )
