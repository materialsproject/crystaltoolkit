from __future__ import annotations

from typing import TYPE_CHECKING

from flask_caching import Cache

from crystal_toolkit.settings import SETTINGS

if TYPE_CHECKING:
    from dash import Dash, html


class CrystalToolkitPlugin:
    """Enables Crystal Toolkit components to work with your Dash app.

    This is a replacement for the previous `register_crystal_toolkit`
    function, to instead use Dash's native plugin system.

    You can use this plugin when instantiating your Dash app:

    dash = Dash(..., plugins=[CrystalToolkitPlugin(layout=layout)])

    Eventually, it is hoped to remove the need for this plugin entirely.
    """

    def __init__(
        self, layout, cache: Cache | None = None, use_default_css=True
    ) -> None:
        """Provide your initial app layout.

        Provide a cache to improve performance. If running
        in debug mode, the cache will be automatically disabled. If
        not specified, a default "simple" cache will be enabled. The
        redis cache is recommended in production contexts.

        If `use_default_css` is set, Bulma and Font Awesome CSS will
        be loaded from external CDNs, as defined in Crystal Toolkit
        settings.
        """
        if cache:
            self.cache = cache
        elif SETTINGS.DEBUG_MODE:
            self.cache = Cache(config={"CACHE_TYPE": "null"})
        else:
            self.cache = Cache(config={"CACHE_TYPE": "simple"})

        self.layout = layout

        self.use_default_css = use_default_css

    def plug(self, app: Dash):
        """Initialize Crystal Toolkit plugin for the specified Dash app."""
        self.app = app
        self.cache.init_app(app.server)

        from crystal_toolkit import __version__ as ct_version

        # add metadata for "generator" tag
        app.config.meta_tags.append(
            {
                "name": "generator",
                "content": f"Crystal Toolkit {ct_version} (Materials Project)",
            }
        )

        # set default title, but respect the user if they override the default
        if app.title == "Dash":
            app.title = "Crystal Toolkit"

        # these should no longer be needed after switching to All-in-One components
        # and pattern-matching callbacks
        app.config["suppress_callback_exceptions"] = True
        app.layout = self.crystal_toolkit_layout(self.layout)

        if self.use_default_css:
            if bulma_css := SETTINGS.BULMA_CSS_URL:
                app.config.external_stylesheets.append(bulma_css)
            if font_awesome_css := SETTINGS.FONT_AWESOME_CSS_URL:
                app.config.external_stylesheets.append(font_awesome_css)

    def crystal_toolkit_layout(self, layout) -> html.Div:
        """Crystal Toolkit currently requires a set of dcc.Store components
        to be added to the layout in order to function.

        Eventually, it is hoped to remove the need for this method through
        use of All-in-One components. All-in-One components were not yet
        available when Crystal Toolkit was first developed.
        """
        from crystal_toolkit.core.mpcomponent import MPComponent

        # Crystal Toolkit has not been tested with dynamic layouts
        if callable(layout):
            layout = layout()

        stores_to_add = []
        for basename in MPComponent._all_id_basenames:
            # can use "if basename in layout_str:" to restrict to components present in initial layout
            # this would cause bugs for components displayed dynamically
            stores_to_add += MPComponent._app_stores_dict[basename]
        layout.children += stores_to_add

        for component in MPComponent._callbacks_to_generate:
            component.generate_callbacks(self.app, self.cache)

        return layout
