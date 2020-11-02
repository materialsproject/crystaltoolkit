from typing import Optional

from pydantic import BaseSettings

from crystal_toolkit import MODULE_PATH

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


class Settings(BaseSettings):

    DEBUG_MODE: bool = False
    MP_EMBED_MODE: bool = False
    TEST_MODE: bool = False

    TRANSFORMATION_PREVIEWS: bool = False
    REDIS_URL: str = "redis://localhost:6379"
    ASSETS_PATH: str = str(MODULE_PATH / "apps" / "assets")

    PERSISTENCE: bool = True
    PERSISTENCE_TYPE: Literal["memory", "session", "local"] = "local"

    SENTRY_DSN: Optional[str] = None

    class Config:
        env_prefix = "CT_"


SETTINGS = Settings()
