"""Configuración centralizada de la aplicación."""
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "Solventa Seguros Digitales"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Base de datos
    DATABASE_URL: str = "postgresql+asyncpg://solventa_user:solventa_password@localhost:5432/solventa"
    DB_HOST: Optional[str] = None
    DB_PORT: int = 5432
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None

    # Seguridad JWT y Autenticación (HU-WEB-13)
    JWT_SECRET_KEY: str = "solventa_super_secret_jwt_key_for_development_only_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Burós externos (ASR-02 / HA-02)
    BUREAU_TIMEOUT_SECONDS: float = 0.400  # 400 ms límite estricto

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET_POLICIES: str = "solventa-policies-dev"
    SQS_QUEUE_EVENTS: str = "solventa-outbox-events-dev"
    S3_DOCUMENTS_BUCKET: Optional[str] = None
    SQS_EVENTS_URL: Optional[str] = None

    @model_validator(mode="after")
    def assemble_db_connection(self) -> "Settings":
        """Ensambla DATABASE_URL si se proporcionan credenciales individuales de base de datos (RDS)."""
        is_default_url = "localhost:5432/solventa" in self.DATABASE_URL
        if (is_default_url or not self.DATABASE_URL) and (
            self.DB_HOST and self.DB_USER and self.DB_PASSWORD and self.DB_NAME
        ):
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        if self.S3_DOCUMENTS_BUCKET:
            self.S3_BUCKET_POLICIES = self.S3_DOCUMENTS_BUCKET
        if self.SQS_EVENTS_URL:
            self.SQS_QUEUE_EVENTS = self.SQS_EVENTS_URL
        return self


settings = Settings()

