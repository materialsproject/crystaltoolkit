from pydantic import BaseSettings

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from crystal_toolkit import MODULE_PATH


class Settings(BaseSettings):

    DEBUG_MODE: bool = False
    MP_EMBED_MODE: bool = False
    TEST_MODE: bool = False

    TRANSFORMATION_PREVIEWS: bool = False
    REDIS_URL: str = "redis://localhost:6379"
    ASSETS_PATH: str = str(MODULE_PATH / "apps" / "assets")

    PERSISTENCE: bool = True
    PERSISTENCE_TYPE: Literal["memory", "session", "local"] = "local"

    JUPYTER_LAB_PRINT_REPR: bool = True

    class Config:
        env_prefix = "CT_"


SETTINGS = Settings()
