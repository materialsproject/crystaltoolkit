from abc import ABC, abstractmethod
from pathlib import Path
from pydoc import classname
from typing import Optional, Any
from pydash import get
from monty.serialization import loadfn

from crystal_toolkit.core.mpcomponent import MPComponent

import crystal_toolkit.helpers.layouts as ctl
import dash_mp_components as mpc
from dash.dependencies import Input, Output
from dash import dcc
from dash import html

from crystal_toolkit import MODULE_PATH
from crystall_toolkit.apps.constants import APP_METADATA, APP_TREE
from crystal_toolkit.helpers.utils import (
    get_mp_app_icon,
    get_breadcrumb,
    is_logged_in,
    get_login_endpoints
)
from mp_web.layouts.apps_sidebar import get_apps_sidebar

#TODO: figure out what to do about this
# _MAIN_CITATION = loadfn(MODULE_PATH / "pages/about/cite/main_citation.json")
_MAIN_CITATION =  {"DOI": "10.1063/1.4812323"}

class MPApp(MPComponent, ABC):
    """
    Class to make an app for the Materials Project website.
    """

    @property
    def name(self):
        """
        Name of your app, will be included in navigation menu
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get(
            "name", "Name Not Defined"
        )

    def login_required(self, payload=None) -> bool:
        """
        Boolean flag for requiring authentication to display your app.
        Optionally, sub-class with logic to handle a specific payload
        to offer more fine-grained controls, for example "materials/"
        might be behind a login, but "materials/mp-13" may not be.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get(
            "login_required", False
        )

    @property
    def description(self):
        """
        Short description of app (aim for max 140 characters). Formatted as Markdown.
        This will display above the search bar.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("description", None)

    @property
    def long_description(self):
        """
        Long description of app (about one paragraph). Formatted as Markdown.
        This will display in the About section of the Documentation drawer.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("long_description", self.description)

    @property
    def url(self):
        """
        URL of your app, will set its url as https://materialsproject.org/{url}
        """
        return APP_METADATA[self.__class__.__name__]["url"]

    @property
    def author(self) -> Optional[str]:
        """
        Name of the author to attribute this app to. First-party apps are authored by 'Materials Project' 
        and thus that is the default value if no author exists in the app metadata.
        This will display under the app title as 'App by [author]'.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("author", "Materials Project")

    @property
    def category(self) -> Optional[None]:
        """
        Category of the app. This will change how it is grouped in the app overview and
        navigation.
        :return:
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("category", None)

    @property
    def credits(self) -> Optional[None]:
        """
        Credit lines associated with this app, to specifically credit individuals or funders
        not otherwise credited by reference to an appropriate publication.
        :return:
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("credits", None)

    @property
    def icon(self) -> Optional[str]:
        """
        Full class name(s) for the icon that represents this app.
        Fontastic icons use the "icon-fontastic-" prefix (e.g. "icon-fontastic-molecules")
        Font awesome icons use the "fa" or "fas" class plus the "fa-" prefix (e.g. "fa fa-user")
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("icon", None)

    @property
    def dois(self) -> ctl.List[str]:
        """
        :return: A list of DOI(s) to cite when using this app
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("dois", [])

    @property
    def docs_url(self) -> Optional[str]:
        """
        URL of the official Materials Project documentation page for this app
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("docs_url", None)

    @property
    def external_links(self) -> ctl.List[Any]:
        """
        :return: A list of external links to display with this app
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("external_links", None)

    @property
    def child_apps(self) -> ctl.List[str]:
        """
        :return: A list of MPApp class names that are "children" (with respect to the
        URL) of this app
        """
        # Matt apologizes for this cryptic code,
        # printing the APP_TREE variable should help it make sense
        return [
            d["NAME"]
            for child, d in get(APP_TREE, self.url.replace("/", ".")).items()
            if child != "NAME"
        ]

    @property
    def use_cache(self) -> bool:
        """
        Boolean flag that tells this app to cache the result
        of the update_main_content callback. Defaults to False.
        Note that cache can and will still be added to individual callbacks
        within an app (e.g. section callbacks for the Materials Detail page)
        """
        return False

    def generate_callbacks(self, app, cache):
        pass
    
    def app_container(self, children, **kwargs):
        return html.Div(children, **kwargs)

    def search_bar_container(self, search_bar):
        return html.Div(
            ctl.Container(
                [
                    html.P(self.description, className="has-text-centered mb-2"),
                    search_bar
                ],
                className="is-max-desktop"
            ),
            className="mp-search-bar"
        )

    def get_layout(self, payload=None):
        """
        Return a Dash layout for the app. If the app requires any
        global set-up before a layout can be generated, put this in
        the app's initializer.
        :param payload: anything in the URL after
        https://materialsproject.org/your_app_name/
        """
        raise NotImplementedError

    def get_breadcrumb_links(self, payload=None) -> dict:
        """
        Get the list of links to display as breadcrumbs below the app name.
        Note that these use the custom mpc.Link component so that certain breadcrumb 
        links can preserve query parameters when the link is clicked.
        :param payload: anything in the URL after https://materialsproject.org/your_app_name/
        :return: list of link components
        """
        breadcrumb_links = [
             mpc.Link("Home", href="/"),
        ]
        # having a category set means the MPApp is a top-level "App" on MP
        if self.category:
            breadcrumb_links.append(mpc.Link("Apps", href="/apps"))
        parts = self.url.split("/")
        # traverse the app tree to get an appropriate breadcrumb
        for idx, part in enumerate(parts):
            app_name = get(APP_TREE, parts[0 : idx + 1] + ["NAME"])
            if app_metadata := APP_METADATA.get(app_name):
                breadcrumb_links.append(mpc.Link(app_metadata.get("name"), href=f"/{app_metadata['url']}", preserveQuery=True))
        if payload:
            breadcrumb_links.append(mpc.Link(payload, href=f"/{payload}", preserveQuery=True)),

        return breadcrumb_links

    def get_page_title(self, payload=None):
        """
        Use to override the page <title> that you see
        in your browser.
        :param payload: anything in the URL after
        https://materialsproject.org/your_app_name/
        :return:
        """
        if not payload:
            return f"Materials Project - {self.name}"
        return f"Materials Project - {self.name} - {payload}"

    def get_page_meta_tags(self, payload=None):
        """
        Use to add to the page <meta> tags. These are
        used for social media previews and search engines.
        :param payload: anything in the URL after
        https://materialsproject.org/your_app_name/
        :return:
        """

        meta_tags = f"""
        <meta property="og:title" content="{self.get_page_title(payload=payload)}" />
        <meta property="og:description" content="{self.description}" />
        <meta property="og:site_name" content="Materials Project">"""

        return meta_tags

    def get_mp_layout(self, payload=None):
        """
        Returns your layout with added Materials Project styling.
        The app is only rendered if login_required is False or if the user is authenticated.
        Otherwise, a login screen is rendered.
        Do not override this method.
        :param payload: anything in the URL after
        https://materialsproject.org/your_app_name/
        :return:
        """
        access_granted = True
        if self.login_required(payload=payload):
            access_granted = is_logged_in()

        if self.icon:
            icon = get_mp_app_icon(self.icon)
        else:
            icon = None

        if self.dois and len(self.dois) > 0:
            citations = [
                mpc.CrossrefCard(identifier=doi, className="box")
                for doi in self.dois
            ]
        else:
            citations = []

        if self.external_links:
            clean_external_links = []

            for link in self.external_links:
                if "href" not in link:
                    return
                if "label" not in link:
                    link["label"] = "External Resource"
                if "twitter.com" in link["href"]:
                    link["icon"] = "hashtag"
                else:
                    link["icon"] = "link"
                clean_external_links.append(link)

            external_links = [
                html.A(
                    html.Span([ctl.Icon(kind=link["icon"]), " " + link["label"]]),
                    href=link["href"],
                    target="_blank",
                    className="tag",
                )
                for link in clean_external_links
            ]
        else:
            external_links = None

        if self.docs_url:
            docs_link = html.A(
                f"Go to {self.name} documentation page.",
                href=self.docs_url,
                target="_blank"
            )
        else:
            docs_link = None

        if self.credits:
            credits = [
                html.P(credit)
                for credit in self.credits
            ]
        else:
            credits = None

        breadcrumbs = get_breadcrumb(self.get_breadcrumb_links(payload))

        mp_app_header = html.Header(
            html.Div(
                [
                    breadcrumbs,
                    html.Div(
                        [
                            html.Div(
                                [
                                    icon, 
                                    html.Div(
                                        [
                                            ctl.H1(self.name, className="is-3 m-0"),
                                            mpc.DrawerTrigger(
                                                html.P(f"App by {self.author}", className="m-0 is-size-7"),
                                                forDrawerId=self.id("references-drawer")
                                            )
                                        ]
                                    )
                                ],
                                className="level-left",
                            ),
                            html.Div(
                                [
                                    mpc.DrawerTrigger(
                                        ctl.Button(
                                            [
                                                ctl.Icon(kind="book"),
                                                html.Span("References")
                                            ]
                                        ),
                                        forDrawerId=self.id("references-drawer")
                                    ),
                                    mpc.DrawerTrigger(
                                        ctl.Button(
                                            [
                                                ctl.Icon(kind="info-circle"),
                                                html.Span("Documentation")
                                            ]
                                        ),
                                        forDrawerId=self.id("documentation-drawer")
                                    ),
                                ],
                                className="level-right buttons",
                            ),
                        ],
                        className="level",
                    ),
                    # mp_app_description,
                    # html.Div(citations + external_links, className="tags is-centered"),
                    # search_bar
                ]
            ),
            className="mp-app-header",
        )

        drawers = [
            mpc.Drawer(
                [
                    ctl.H2("References", className="is-4"),
                    html.P(
                        [
                            html.Span(
                                """
                                To cite this app, include all of the references listed below
                                as well as the 
                                """
                            ),
                            html.A(
                                "main Materials Project citation.",
                                href=f"https://doi.org/{_MAIN_CITATION['DOI']}",
                                target="_blank"
                            )
                        ]
                        
                    ),
                    html.Div(citations),
                    ctl.H3("Acknowledgements", className="is-5") if credits else None,
                    html.Div(credits) if credits else None,
                ],
                id=self.id("references-drawer"),
                className="content undivided"
            ),
            mpc.Drawer(
                [
                    ctl.H2("Documentation", className="is-4"),
                    docs_link,
                    ctl.H3("About", className="is-5") if self.long_description else None,
                    mpc.Markdown(self.long_description) if self.long_description else None,
                    ctl.H3("External Links", className="is-5") if external_links else None,
                    html.Div(external_links, className="tags") if external_links else None,
                ],
                id=self.id("documentation-drawer"),
                className="content undivided"
            )
        ]

        if access_granted:
            mp_app_content = html.Section(
                [
                    html.Div(
                        [html.Progress(className="progress is-primary")],
                        id=self.id("mp-app-content"),
                    )
                ] + drawers,
                className="mp-app-content section",
            )

        else:
            login_endpoint, logout_endpoint = get_login_endpoints()
            mp_app_content = html.Section(
                [
                    ctl.Container(
                        ctl.Columns(
                            ctl.Column(
                                ctl.Box(
                                    [
                                        html.P(
                                            "Login to start using this app.",
                                            className="is-size-5 has-text-centered",
                                        ),
                                        html.A(
                                            "Login",
                                            href=login_endpoint,
                                            className="button is-primary is-block mt-3",
                                        ),
                                        html.A(
                                            "New user? Register for free.",
                                            href=login_endpoint,
                                            className="button is-primary is-outlined is-block mt-3",
                                        ),
                                    ]
                                ),
                                className="is-4-desktop is-8-tablet",
                            ),
                            className="is-centered",
                        )
                    )
                ] + drawers,
                className="mp-app-content section",
            )

        mp_apps_sidebar = get_apps_sidebar(self.name)

        return html.Div(
            [
                self.app_container(
                    mpc.DrawerContextProvider(
                        [
                            mp_apps_sidebar,
                            html.Div(
                                [mp_app_header, mp_app_content],
                                className="mp-app-content-container",
                            ),
                        ]
                    ),
                    id=self.id("app-container"),
                    className="mp-app-container is-gapless",
                ),
            ]
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("mp-app-content"), "children"), [Input("mp-url", "pathname")]
        )
        # @conditional_decorator(
        #     cache.memoize(
        #         timeout=60 * 60 * 24,
        #         # TODO: will ensure cache from previous release not used
        #         make_name=lambda x: f"{self.__class__.__name__}_{x}",
        #     ),
        #     self.use_cache,
        # )
        def update_main_content(pathname):
            _, payload = parse_pathname(pathname)

            return (self.get_layout(payload=payload),)


def parse_pathname(pathname):
    """
    Helper function for routing, e.g. to parse
    https://materialsproject.org/app/payload
    :param pathname: as defined in dcc.Location
    :return: tuple of app, payload (both strings)
    """

    app, payload = None, None

    if not pathname:
        return app, payload

    path = Path(pathname)
    parts = list(path.parts)

    # URLs without leading / will still resolve,
    # but will mess up routing logic
    if parts and parts[0] == "/":
        parts = parts[1:]

    # find the correct app, working backwards
    for idx in range(len(parts)):
        if leaf := get(APP_TREE, parts[: len(parts) - idx]):
            app = leaf["NAME"]
            payload = "/".join(parts[len(parts) - idx :])
            # TODO: there's some vagueness to resolve here regarding variable names, e.g. app vs app_url vs app_name
            return APP_METADATA[app]["url"], payload

    # else, unknown app, so just parse first part as "app" and remainder as "payload"
    if parts:
        app = parts[0]

    if len(parts) > 1:
        payload = "/".join(parts[1:])

    return app, payload