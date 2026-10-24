"""Configuración centralizada de la aplicación."""
from typing import Optional
from pydantic import SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "Solventa Seguros Digitales"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = []

    # Base de datos
    DATABASE_URL: str = "postgresql+asyncpg://solventa_user:solventa_password@localhost:5432/solventa"
    DB_HOST: Optional[str] = None
    DB_PORT: int = 5432
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None

    # Llaves sin valor por defecto: cada ambiente define las suyas, una por propósito
    JWT_SECRET_KEY: SecretStr
    OTP_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    PARTNER_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # SMS del código del asegurado (HU-MOV-02): "console" en desarrollo, "twilio" con credenciales
    SMS_PROVIDER: str = "console"
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None

    # Burós externos (ASR-02 / HA-02)
    BUREAU_TIMEOUT_SECONDS: float = 0.400  # 400 ms límite estricto

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET_POLICIES: str = "solventa-policies-dev"
    SQS_QUEUE_EVENTS: str = "solventa-outbox-events-dev"
    S3_DOCUMENTS_BUCKET: Optional[str] = None
    SQS_EVENTS_URL: Optional[str] = None

    @field_validator("JWT_SECRET_KEY", "OTP_SECRET_KEY")
    @classmethod
    def llave_suficiente(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_KEY_LENGTH:
            raise ValueError(f"debe tener al menos {MIN_KEY_LENGTH} caracteres")
        return value

    @model_validator(mode="after")
    def llaves_distintas(self) -> "Settings":
        if self.JWT_SECRET_KEY.get_secret_value() == self.OTP_SECRET_KEY.get_secret_value():
            raise ValueError("JWT_SECRET_KEY y OTP_SECRET_KEY deben ser distintas")
        return self

    @property
    def debug_enabled(self) -> bool:
        """Código de prueba en respuestas, cuentas sembradas y documentación interactiva."""
        return self.ENVIRONMENT != "production"

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


def load_settings(**values) -> Settings:
    """Carga la configuración; si es inválida, nombra los campos sin mostrar ningún valor."""
    try:
        return Settings(**values)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or 'configuración'}: {error['msg']}"
            for error in exc.errors()
        )
        raise RuntimeError(f"Configuración inválida o incompleta: {problems}") from None


settings = load_settings()

