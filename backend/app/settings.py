from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Not to forget: these settings are loaded from environment variables based
    # on the class attribute names.
    database_url: str = "postgresql://postgres:postgres@localhost/postgres"


@lru_cache
def get_settings():
    return Settings()
