from __future__ import annotations

from abc import ABC

from dash import html
from dash.dependencies import Input, Output

import crystal_toolkit.helpers.layouts as ctl
from crystal_toolkit.apps.constants import APP_METADATA
from crystal_toolkit.core.mpcomponent import MPComponent


class MPApp(MPComponent, ABC):
    """Class to make an app for the Materials Project website."""

    @property
    def name(self):
        """Name of your app, will be included in navigation menu."""
        return APP_METADATA.get(self.__class__.__name__, {}).get(
            "name", "Name Not Defined"
        )

    def login_required(self, payload=None) -> bool:
        """Boolean flag for requiring authentication to display your app.
        Optionally, sub-class with logic to handle a specific payload
        to offer more fine-grained controls, for example "materials/"
        might be behind a login, but "materials/mp-13" may not be.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get(
            "login_required", False
        )

    @property
    def description(self) -> str:
        """Short description of app (aim for max 140 characters). Formatted as Markdown.
        This will display above the search bar.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("description")

    @property
    def long_description(self):
        """Long description of app (about one paragraph). Formatted as Markdown.
        This will display in the About section of the Documentation drawer.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get(
            "long_description", self.description
        )

    @property
    def url(self):
        """URL of your app, will set its url as https://materialsproject.org/{url}."""
        return APP_METADATA[self.__class__.__name__]["url"]

    @property
    def author(self) -> str | None:
        """Name of the author to attribute this app to. First-party apps are authored by 'Materials Project'
        and thus that is the default value if no author exists in the app metadata.
        This will display under the app title as 'App by [author]'.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get(
            "author", "Materials Project"
        )

    @property
    def category(self) -> str | None:
        """Category of the app. This will change how it is grouped in the app overview and
        navigation.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("category")

    @property
    def credits(self) -> str | None:
        """Credit lines associated with this app, to specifically credit individuals or funders
        not otherwise credited by reference to an appropriate publication.
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("credits")

    @property
    def icon(self) -> str | None:
        """Full class name(s) for the icon that represents this app.
        Fontastic icons use the "icon-fontastic-" prefix (e.g. "icon-fontastic-molecules")
        Font awesome icons use the "fa" or "fas" class plus the "fa-" prefix (e.g. "fa fa-user").
        """
        return APP_METADATA.get(self.__class__.__name__, {}).get("icon")

    @property
    def dois(self) -> list[str]:
        """A list of DOI(s) to cite when using this app."""
        return APP_METADATA.get(self.__class__.__name__, {}).get("dois", [])

    @property
    def docs_url(self) -> str | None:
        """URL of the official Materials Project documentation page for this app."""
        return APP_METADATA.get(self.__class__.__name__, {}).get("docs_url")

    @property
    def external_links(self):
        """A list of external links to display with this app."""
        return APP_METADATA.get(self.__class__.__name__, {}).get("external_links")

    @property
    def use_cache(self) -> bool:
        """Boolean flag that tells this app to cache the result
        of the update_main_content callback. Defaults to False.
        Note that cache can and will still be added to individual callbacks
        within an app (e.g. section callbacks for the Materials Detail page).
        """
        return False

    def search_bar_container(self, search_bar):
        return html.Div(
            ctl.Container(
                [
                    html.P(self.description, className="has-text-centered mb-2"),
                    search_bar,
                ],
                className="is-max-desktop",
            ),
            className="mp-search-bar",
        )

    def generate_callbacks(self, app, cache) -> None:
        @app.callback(
            Output(self.id("mp-app-content"), "children"), Input("mp-url", "pathname")
        )
        def update_main_content(pathname):
            _, payload = parse_pathname(pathname)  # noqa: F821

            return self.get_layout(payload=payload)
