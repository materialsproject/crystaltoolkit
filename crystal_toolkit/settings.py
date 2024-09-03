from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, HttpUrl, RedisDsn

try:
    # pydantic 2+
    from pydantic_settings import BaseSettings
except ImportError:
    # pydantic <2
    from pydantic import BaseSettings


MODULE_PATH = Path(__file__).parents[0]


class Settings(BaseSettings):
    """Crystal Toolkit settings."""

    DEBUG_MODE: bool = Field(
        default=False,
        help="This setting will set Dash's debug mode, will disable the cache used by Crystal Toolkit, and control log output.",
    )
    TEST_MODE: bool = Field(
        default=False,
        help="Set to True when Crytal Toolkit is run during automated testing. It will switch the default renderer to SVG instead of WebGL, since many testing environments do not have WebGL available.",
    )

    REDIS_URL: Optional[RedisDsn] = Field(
        default="redis://localhost:6379",
        help="Redis instance used by Crystal Toolkit for caching. If set to None, simple caching will be used instead.",
    )
    ASSETS_PATH: Path = Field(
        default=MODULE_PATH / "apps" / "assets",
        help="Path to assets folder. Used only when running the example Crystal Toolkit apps.",
    )

    PERSISTENCE: bool = Field(
        default=True,
        help="This setting controls whether Crystal Toolkit components in your app will have user-chosen values persisted by default or not. For example, choice of bonding algorithm, etc.",
    )
    PERSISTENCE_TYPE: Literal["memory", "session", "local"] = Field(
        default="local",
        help="If persistence enabled, this will control the type of persistence. See Dash documentation for more information.",
    )

    PRIMARY_COLOR: str = Field(
        default="hsl(171, 100%, 41%)",
        help="A default primary color used for some user interface elements.",
    )

    BULMA_CSS_URL: Optional[HttpUrl] = Field(
        default="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.4/css/bulma.min.css",
        help="If set, this CSS file will be loaded by default. Loading Bulma CSS is required only for aesthetic reasons.",
    )
    FONT_AWESOME_CSS_URL: Optional[HttpUrl] = Field(
        default="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css",
        help="If set, this CSS file will be loaded by default. Loading Font Awesome is required to display certain icons, but otherwise is not required for functionality.",
    )

    JUPYTER_EMBED_PORT: Optional[int] = Field(
        default=8884,
        help="The Jupyter extension (powered by Dash) requires a port to run on. If None, an available port will be chosen.",
    )
    JUPYTER_EMBED_MODE: Optional[Literal["external", "tab", "jupyterlab"]] = Field(
        default=None,
        help="The Jupyter extension mode to use. See Dash documentation for more information.",
    )

    # Legend settings. These control the defaults for crystal structure and molecule visualization.
    LEGEND_COLOR_SCHEME: Literal["Jmol", "VESTA", "accessible"] = Field(
        default="Jmol",
        help="Color scheme used to display atoms.",
    )
    LEGEND_RADIUS_SCHEME: Literal[
        "atomic",
        "specified_or_average_ionic",
        "covalent",
        "van_der_waals",
        "atomic_calculated",
        "uniform",
    ] = Field(
        default="uniform",
        help="Method with which to choose a radius when displaying atoms.",
    )
    LEGEND_CMAP: str = Field(
        default="coolwarm",
        help="Color map for displaying atoms when color-coded by a site property. Choose from matplotlib color maps.",
    )
    LEGEND_FALLBACK_COLOR: tuple = Field(
        default=(0, 0, 0),
        help="Fallback color for displaying atoms when a more specific color is not defined.",
    )
    LEGEND_FALLBACK_RADIUS: float = Field(
        default=1.0,
        help="Fallback radius for displaying atoms when a more specific radius (e.g. ionic radius) is not defined.",
    )
    LEGEND_UNIFORM_RADIUS: float = Field(
        default=0.5,
        help="Default radius for displaying atoms when uniform radii are chosen.",
    )

    # Materials Project API settings.
    # TODO: These should be deprecated in favor of setti
    API_KEY: Optional[str] = Field(default="", help="Materials Project API key.")
    API_EXTERNAL_ENDPOINT: str = Field(
        default="https://api.materialsproject.org",
        help="Materials Project API endpoint.",
    )

    # Materials Project deployment settings. If not running Crystal Toolkit for the Materials Project website, these can be ignored.
    DEV_LOGIN_DISABLED: bool = Field(
        default=True, help="Used internally by Materials Project."
    )
    LOGIN_ENDPOINT: str = Field(
        default="https://profile.materialsproject.org/",
        help="Used internally by Materials Project.",
    )
    APP_METADATA: Path = Field(
        default=MODULE_PATH / "apps" / "app_metadata.yaml",
        help="Path to app metadata field for Materials Project apps. Used as an alternative way of defining app metadata when defining many apps.",
    )

    # Experimental settings.
    TRANSFORMATION_PREVIEWS: bool = Field(
        default=False,
        help="This setting controls whether previews are rendered for structure transformations.",
    )
    DOI_CACHE_PATH: Optional[Path] = Field(
        default=MODULE_PATH / "apps/assets/doi_cache.json",
        help="Not currently used, maybe will be deprecated. This was used to avoid a CrossRef API lookup when a small set of DOIs were used in an app.",
    )

    # Deprecated settings.
    MP_EMBED_MODE: bool = Field(
        default=False,
        help="Deprecated. This was used for early versions of Crystal Toolkit when embedded in the Materials Project website.",
    )

    class Config:
        """Crystal Toolkit environment variable config class."""

        env_prefix = "CT_"

    def print(self):
        """Print settings."""
        print("Crystal Toolkit settings")
        for key, val in self.dict().items():
            print(f"  {key} = {val}")


SETTINGS = Settings()
