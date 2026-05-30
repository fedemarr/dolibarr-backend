# Configuracion central del sistema usando variables de entorno
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str
    ENVIRONMENT: Literal["development", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # Base de datos (usados solo si DATABASE_URL de Railway no esta disponible)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "dolibarr_automation"
    DB_USER: str = "automation_user"
    DB_PASSWORD: str = "automation_pass_dev"

    REDIS_URL: str = "redis://localhost:6379/0"

    DOLIBARR_URL: str
    DOLIBARR_API_KEY: str

    AWS_ACCESS_KEY_ID: str = "placeholder"
    AWS_SECRET_ACCESS_KEY: str = "placeholder"
    AWS_S3_BUCKET: str = "dolibarr-pdfs"
    AWS_REGION: str = "sa-east-1"

    RESEND_API_KEY: str = "placeholder"
    SLACK_WEBHOOK_URL: str = "placeholder"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @property
    def DATABASE_URL(self) -> str:
        # Railway provee DATABASE_URL directamente como variable de entorno
        railway_url = os.getenv("DATABASE_URL")
        if railway_url:
            return (
                railway_url
                .replace("postgres://", "postgresql+asyncpg://", 1)
                .replace("postgresql://", "postgresql+asyncpg://", 1)
            )
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        # URL para Alembic (necesita driver sincronico)
        railway_url = os.getenv("DATABASE_URL")
        if railway_url:
            return (
                railway_url
                .replace("postgres://", "postgresql+psycopg2://", 1)
                .replace("postgresql://", "postgresql+psycopg2://", 1)
            )
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


config = Configuracion()
