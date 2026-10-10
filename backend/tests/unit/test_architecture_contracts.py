"""Pruebas de contratos arquitectónicos, configuración e infraestructura común."""
import pytest
from app.core.config import settings
from app.core.security import create_access_token, decode_access_token
from app.core.middleware import tenant_context
from app.modules.policy.service import policy_service
from app.modules.policy.models import PolicyIssueRequest


@pytest.mark.unit
def test_settings_load():
    """Valida carga de configuraciones y valores por defecto."""
    assert settings.PROJECT_NAME == "Solventa Seguros Digitales"
    assert settings.BUREAU_TIMEOUT_SECONDS == 0.400
    assert settings.API_V1_STR == "/api/v1"


@pytest.mark.unit
def test_jwt_token_creation_and_claims():
    """Valida generación de JWT con claims de rol y expiración (HA-06, HA-13)."""
    token = create_access_token(
        subject="test@solventa.com",
        role="advisor",
        claims={"channel": "web"},
    )
    decoded = decode_access_token(token)
    assert decoded["sub"] == "test@solventa.com"
    assert decoded["role"] == "advisor"
    assert decoded["channel"] == "web"


@pytest.mark.unit
def test_tenant_contextvar():
    """Valida que la variable de contexto asíncrono para tenant funcione (HA-14 / ASR-06)."""
    token = tenant_context.set("banco-aliado-1")
    assert tenant_context.get() == "banco-aliado-1"
    tenant_context.reset(token)
    assert tenant_context.get() is None


@pytest.mark.unit
def test_policy_service_raises_not_implemented():
    """Valida que policy_service lance NotImplementedError antes de implementar HU-WEB-05."""
    req = PolicyIssueRequest(quote_id="Q1", tier="standard", insured_document="123")
    with pytest.raises(NotImplementedError):
        policy_service.issue_policy(req)


@pytest.mark.unit
def test_password_hash_and_verify():
    """Valida el hash bcrypt de contraseñas compatible con bcrypt 5."""
    from app.core.security import get_password_hash, verify_password

    hashed = get_password_hash("Solventa2026!")
    assert hashed.startswith("$2b$")
    assert verify_password("Solventa2026!", hashed)
    assert not verify_password("otra-clave", hashed)
