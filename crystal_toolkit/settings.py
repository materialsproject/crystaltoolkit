from pydantic import BaseSettings


class Settings(BaseSettings):

    DEBUG_MODE: bool = False
    MP_EMBED_MODE: bool = False
    TRANSFORMATION_PREVIEWS: bool = True
    REDIS_URL: str = "redis://localhost:6379"
    ASSETS_PATH: str = None

    class Config:
        env_prefix = "CT_"


SETTINGS = Settings()
