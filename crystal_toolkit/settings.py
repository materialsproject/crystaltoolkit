from __future__ import annotations

from typing import Literal, Union

from pydantic_settings import BaseSettings

from crystal_toolkit import MODULE_PATH


class Settings(BaseSettings):
    """Crystal Toolkit settings class."""

    DEBUG_MODE: bool = False
    MP_EMBED_MODE: bool = False
    TEST_MODE: bool = False

    TRANSFORMATION_PREVIEWS: bool = False
    REDIS_URL: str = "redis://localhost:6379"
    ASSETS_PATH: str = str(MODULE_PATH / "apps" / "assets")
    APP_METADATA: str = str(MODULE_PATH / "apps" / "app_metadata.yaml")

    DEV_LOGIN_DISABLED: bool = True
    LOGIN_ENDPOINT: str = "https://profile.materialsproject.org/"
    API_KEY: Union[str, None] = ""
    API_EXTERNAL_ENDPOINT: str = "https://api.materialsproject.org"

    PERSISTENCE: bool = True
    PERSISTENCE_TYPE: Literal["memory", "session", "local"] = "local"

    class Config:
        """Crystal Toolkit environment variable config class."""

        env_prefix = "CT_"


SETTINGS = Settings()
