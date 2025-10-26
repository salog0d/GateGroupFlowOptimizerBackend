from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        extra="ignore",
        case_sensitive=False,
    )

    db_user: Optional[str] = Field(None, alias="DB_USER")
    db_user_password: Optional[str] = Field(None, alias="DB_USER_PASSWORD")
    db_host: str = Field("localhost", alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    db_name: Optional[str] = Field(None, alias="DB_NAME")

    database_url_async_env: Optional[str] = Field(None, alias="DATABASE_URL_ASYNC")
    database_url_sync_env: Optional[str] = Field(None, alias="DATABASE_URL_SYNC")
    aviation_edge_api: str = Field(..., alias="AVIATION_EDGE_API")
    future_flights_url: str = Field(..., alias="FUTURE_FLIGHTS_URL")

    @computed_field
    @property
    def database_url_async(self) -> str:
        """
        URL para AsyncSession (asyncpg). Usa DATABASE_URL_ASYNC si existe; si no, arma desde componentes.
        """
        if self.database_url_async_env:
            return self.database_url_async_env
        if not all([self.db_user, self.db_user_password, self.db_name]):
            raise ValueError("Faltan DB_USER/DB_USER_PASSWORD/DB_NAME para armar DATABASE_URL_ASYNC")
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_user_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @computed_field
    @property
    def database_url_sync(self) -> str:
        """
        URL para herramientas síncronas (p.ej. Alembic con psycopg2).
        """
        if self.database_url_sync_env:
            return self.database_url_sync_env
        if not all([self.db_user, self.db_user_password, self.db_name]):
            raise ValueError("Faltan DB_USER/DB_USER_PASSWORD/DB_NAME para armar DATABASE_URL_SYNC")
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_user_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()