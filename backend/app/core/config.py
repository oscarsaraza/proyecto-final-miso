"""Configuración centralizada de la aplicación."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "Solventa Seguros Digitales"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Base de datos
    DATABASE_URL: str = "postgresql+asyncpg://solventa_user:solventa_password@localhost:5432/solventa"

    # Seguridad JWT
    JWT_SECRET_KEY: str = "solventa_super_secret_jwt_key_for_development_only_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Burós externos (ASR-02 / HA-02)
    BUREAU_TIMEOUT_SECONDS: float = 0.400  # 400 ms límite estricto

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET_POLICIES: str = "solventa-policies-dev"
    SQS_QUEUE_EVENTS: str = "solventa-outbox-events-dev"


settings = Settings()
