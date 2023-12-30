from typing import Any, Literal

from pydantic import AnyHttpUrl, MySQLDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl | Literal["*"]] = ["*"]
    """List of origins that should be allowed to make CORS requests."""

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Any) -> list[str] | str:
        """Transform the string of origins into a list of origins."""

        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    LOG_JSON_FORMAT: bool = False
    LOG_LEVEL: str = "INFO"

    SESSION_SECRET_KEY: str = "secret"

    DEEPGRAM_SECRET_KEY: str = ""
    OPENAI_API_KEY: str = ""

    MYSQL_USER: str = "app"
    MYSQL_PASSWORD: str = "app"
    MYSQL_DATABASE: str = "db"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306

    @property
    def DATABASE_URL(self) -> str:
        """Return the database URL as a string."""

        dsn = MySQLDsn.build(
            scheme="mysql+asyncmy",
            username=self.MYSQL_USER,
            password=self.MYSQL_PASSWORD,
            host=self.MYSQL_HOST,
            port=self.MYSQL_PORT,
            path=self.MYSQL_DATABASE,
        )

        return str(dsn)


# Ignore the issue of "Argument missing for parameter ..." for the Settings class
# because the argument is loaded from the environment variables by pydantic-settings.
settings = Settings()  # pyright: ignore[reportGeneralTypeIssues]
"""Global settings for the application."""
