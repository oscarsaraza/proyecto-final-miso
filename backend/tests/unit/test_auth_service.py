"""Pruebas unitarias de modelos, seguridad, TOTP y servicio de autenticación (HU-WEB-13.1)."""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_totp,
    get_password_hash,
    validate_password_strength,
    verify_password,
    verify_totp,
)
from app.modules.auth.models import UserDB
from app.modules.auth.service import (
    DEFAULT_SEED_NAME,
    DEFAULT_SEED_PASSWORD,
    DEFAULT_SEED_TOTP_SECRET,
    DEFAULT_SEED_USERNAME,
    AuthService,
)


class InMemorySessionTestDouble:
    """Test Double asíncrono para simular operaciones de AsyncSession en pruebas unitarias."""

    def __init__(self):
        self.users = {}

    async def execute(self, stmt):
        class Result:
            def __init__(self, items):
                self._items = items

            def scalars(self):
                class Scalars:
                    def __init__(self, items):
                        self._items = items

                    def first(self):
                        return self._items[0] if self._items else None

                return Scalars(self._items)

        # Extraer el valor del filtro de username
        clean_username = stmt.whereclause.right.value
        user = self.users.get(clean_username)
        return Result([user] if user else [])

    def add(self, user):
        self.users[user.username] = user

    async def commit(self):
        pass

    async def refresh(self, user):
        pass


@pytest.fixture
def auth_service():
    return AuthService()


@pytest.fixture
def session():
    return InMemorySessionTestDouble()


@pytest.mark.unit
def test_password_strength_validation():
    """Valida política de contraseñas robustas según criterio HA-06."""
    # Válida: min 8 caracteres, mayúscula, minúscula, dígito y caracter especial
    assert validate_password_strength("SuperSecreta2026*") is True
    assert validate_password_strength("Valida123#") is True

    # Inválidas
    assert validate_password_strength("Short1!") is False  # < 8 chars
    assert validate_password_strength("supersecreta2026*") is False  # Sin mayúscula
    assert validate_password_strength("SUPERSECRETA2026*") is False  # Sin minúscula
    assert validate_password_strength("SuperSecreta****") is False  # Sin número
    assert validate_password_strength("SuperSecreta2026") is False  # Sin especial


@pytest.mark.unit
def test_bcrypt_hashing_and_verification():
    """Valida generación de hash bcrypt y verificación segura."""
    password = "SuperSecreta2026*"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("ContraseñaEquivocada", hashed) is False
    assert verify_password(password, "invalid_hash_string") is False


@pytest.mark.unit
def test_totp_rfc_6238_generation_and_tolerance_window():
    """Valida generación y tolerancia de 30 segundos del algoritmo TOTP RFC 6238 (HA-06)."""
    secret = "JBSWY3DPEHPK3PXP"
    base_timestamp = 1700000000

    # 1. Generación de código de 6 dígitos
    code_at_base = generate_totp(secret, timestamp=base_timestamp)
    assert len(code_at_base) == 6
    assert code_at_base.isdigit()

    # 2. Validación exacta en la misma ventana
    assert verify_totp(secret, code_at_base, timestamp=base_timestamp) is True

    # 3. Ventana de tolerancia: ±30 segundos
    assert verify_totp(secret, code_at_base, timestamp=base_timestamp + 25) is True
    assert verify_totp(secret, code_at_base, timestamp=base_timestamp - 25) is True

    # 4. Fuera de la ventana de tolerancia (+70 segundos = 2 ventanas después)
    assert verify_totp(secret, code_at_base, timestamp=base_timestamp + 70) is False

    # 5. Códigos erróneos o inválidos
    assert verify_totp(secret, "000000", timestamp=base_timestamp) is False
    assert verify_totp(secret, "abcdef", timestamp=base_timestamp) is False
    assert verify_totp(secret, "123", timestamp=base_timestamp) is False
    assert verify_totp(secret, "", timestamp=base_timestamp) is False


@pytest.mark.unit
def test_token_types_and_claims():
    """Valida creación y separación estricta de access_token y refresh_token."""
    access_token = create_access_token(
        subject="asesor@solventa.com",
        role="advisor",
        claims={"advisor_name": "Carlos Asesor"},
    )
    refresh_token = create_refresh_token(
        subject="asesor@solventa.com",
        role="advisor",
    )

    # Validar acceso
    decoded_access = decode_access_token(access_token)
    assert decoded_access["sub"] == "asesor@solventa.com"
    assert decoded_access["role"] == "advisor"
    assert decoded_access["advisor_name"] == "Carlos Asesor"
    assert decoded_access["type"] == "access"

    # Validar refresco
    decoded_refresh = decode_refresh_token(refresh_token)
    assert decoded_refresh["sub"] == "asesor@solventa.com"
    assert decoded_refresh["type"] == "refresh"

    # decode_access_token permite decodificar cualquier JWT firmado por la aplicación (compatibilidad HU-MOV-12)
    assert decode_access_token(refresh_token)["type"] == "refresh"

    # decode_refresh_token exige estrictamente type == 'refresh'
    with pytest.raises(Exception):
        decode_refresh_token(access_token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_seed_default_users(auth_service: AuthService, session: InMemorySessionTestDouble):
    """Valida creación idempotente del asesor semilla pre-configurado."""
    user = await auth_service.seed_default_users(session)
    assert user.username == DEFAULT_SEED_USERNAME
    assert user.full_name == DEFAULT_SEED_NAME
    assert user.role == "advisor"
    assert user.totp_secret == DEFAULT_SEED_TOTP_SECRET
    assert verify_password(DEFAULT_SEED_PASSWORD, user.hashed_password) is True

    # Segunda invocación no debe duplicar
    second_call = await auth_service.seed_default_users(session)
    assert second_call.username == user.username


@pytest.mark.unit
@pytest.mark.asyncio
async def test_authenticate_user_success(auth_service: AuthService, session: InMemorySessionTestDouble):
    """Valida autenticación exitosa con credenciales corporativas y TOTP correcto."""
    user = await auth_service.seed_default_users(session)
    valid_totp = generate_totp(user.totp_secret)

    authenticated_user = await auth_service.authenticate_user(
        session=session,
        username=DEFAULT_SEED_USERNAME,
        password=DEFAULT_SEED_PASSWORD,
        totp_code=valid_totp,
    )
    assert authenticated_user.username == DEFAULT_SEED_USERNAME
    assert authenticated_user.failed_attempts == 0
    assert authenticated_user.locked_until is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_authenticate_user_invalid_credentials_returns_unified_401(
    auth_service: AuthService, session: InMemorySessionTestDouble
):
    """Valida rechazo unificado por credenciales erróneas sin discriminar el fallo (Criterio 2)."""
    user = await auth_service.seed_default_users(session)
    valid_totp = generate_totp(user.totp_secret)

    # 1. Contraseña errónea
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(
            session=session,
            username=DEFAULT_SEED_USERNAME,
            password="WrongPassword123*",
            totp_code=valid_totp,
        )
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Credenciales o código de verificación inválidos"

    # 2. TOTP erróneo
    with pytest.raises(HTTPException) as exc_info_totp:
        await auth_service.authenticate_user(
            session=session,
            username=DEFAULT_SEED_USERNAME,
            password=DEFAULT_SEED_PASSWORD,
            totp_code="999999",
        )
    assert exc_info_totp.value.status_code == 401
    assert exc_info_totp.value.detail == "Credenciales o código de verificación inválidos"

    # 3. Usuario inexistente
    with pytest.raises(HTTPException) as exc_info_user:
        await auth_service.authenticate_user(
            session=session,
            username="noexiste@solventa.com",
            password=DEFAULT_SEED_PASSWORD,
            totp_code=valid_totp,
        )
    assert exc_info_user.value.status_code == 401
    assert exc_info_user.value.detail == "Credenciales o código de verificación inválidos"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_account_lockout_after_5_consecutive_failed_attempts(
    auth_service: AuthService, session: InMemorySessionTestDouble
):
    """Valida bloqueo temporal de 15 minutos (HTTP 423) al acumular 5 intentos fallidos consecutivos (Issue #111)."""
    user = await auth_service.seed_default_users(session)
    valid_totp = generate_totp(user.totp_secret)

    # Intentos 1 a 4 fallidos -> 401
    for attempt in range(1, 5):
        with pytest.raises(HTTPException) as exc:
            await auth_service.authenticate_user(
                session=session,
                username=DEFAULT_SEED_USERNAME,
                password=f"WrongPassword{attempt}*",
                totp_code=valid_totp,
            )
        assert exc.value.status_code == 401
        assert user.failed_attempts == attempt

    # Intento 5 fallido -> 423 Locked
    with pytest.raises(HTTPException) as exc_5:
        await auth_service.authenticate_user(
            session=session,
            username=DEFAULT_SEED_USERNAME,
            password="WrongPassword5*",
            totp_code=valid_totp,
        )
    assert exc_5.value.status_code == 423
    assert "Cuenta bloqueada por seguridad" in exc_5.value.detail
    assert "15 minutos" in exc_5.value.detail
    assert user.failed_attempts == 5
    assert user.locked_until is not None

    # Intentos subsiguientes mientras está bloqueado (incluso con credenciales válidas) -> 423
    with pytest.raises(HTTPException) as exc_subsequent:
        await auth_service.authenticate_user(
            session=session,
            username=DEFAULT_SEED_USERNAME,
            password=DEFAULT_SEED_PASSWORD,
            totp_code=valid_totp,
        )
    assert exc_subsequent.value.status_code == 423
    assert "Cuenta bloqueada por seguridad" in exc_subsequent.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lockout_expiration_restores_access(
    auth_service: AuthService, session: InMemorySessionTestDouble
):
    """Valida que una vez transcurridos los 15 minutos de bloqueo, el acceso se restablece exitosamente."""
    user = await auth_service.seed_default_users(session)
    valid_totp = generate_totp(user.totp_secret)

    # Forzar estado bloqueado con marca en el pasado (hace 20 minutos)
    user.failed_attempts = 3
    user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=20)

    # Autenticación con credenciales válidas
    authenticated_user = await auth_service.authenticate_user(
        session=session,
        username=DEFAULT_SEED_USERNAME,
        password=DEFAULT_SEED_PASSWORD,
        totp_code=valid_totp,
    )
    assert authenticated_user.failed_attempts == 0
    assert authenticated_user.locked_until is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_token_generation_and_refresh(
    auth_service: AuthService, session: InMemorySessionTestDouble
):
    """Valida generación de tokens y flujo de renovación silenciosa de sesión."""
    user = await auth_service.seed_default_users(session)

    # 1. Generar tokens iniciales
    tokens = auth_service.generate_session_tokens(user)
    assert tokens.role == "advisor"
    assert tokens.advisor_name == "Carlos Asesor"
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None

    # 2. Renovar sesión con el refresh token
    refreshed_tokens = await auth_service.refresh_session(session, tokens.refresh_token)
    assert refreshed_tokens.role == "advisor"
    assert refreshed_tokens.advisor_name == "Carlos Asesor"
    assert refreshed_tokens.access_token is not None

    # 3. Rechazo de token de refresco inválido
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.refresh_session(session, "invalid_refresh_token_payload")
    assert exc_info.value.status_code == 401

