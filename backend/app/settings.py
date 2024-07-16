from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Not to forget: these settings are loaded from environment variables based
    # on the class attribute names.
    database_url: str = "postgresql://postgres:postgres@localhost/postgres"
    iam_api: str = "https://iam.api.cloud.yandex.net"
    translation_api: str = "https://translate.api.cloud.yandex.net"
    secret_key: str = "secret-key"
    domain_name: str | None = None
    env: Literal["DEV", "PROD"] = "DEV"
    origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://localhost:8000",
    )


settings = Settings()
