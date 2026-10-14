"""Pruebas unitarias de asegurabilidad y consentimiento Open Finance (TC-S1-03, TC-S1-04)."""
import pytest
from datetime import date
from app.modules.profile.models import ClientIdentification, ConsentRequest
from app.modules.profile.service import profile_service


@pytest.mark.unit
def test_profile_service_validate_age_raises_not_implemented():
    """Valida que validate_insurable_age lance NotImplementedError hasta HU-WEB-02."""
    client = ClientIdentification(
        document_type="CC",
        document_number="1020304050",
        first_name="Carlos",
        last_name="Perez",
        birth_date=date(1996, 5, 10),
        email="carlos@test.com",
        phone="3001234567",
    )
    with pytest.raises(NotImplementedError):
        profile_service.validate_insurable_age(client)


@pytest.mark.unit
@pytest.mark.skip(reason="TDD: Se habilitará al implementar HU-WEB-02 (Captura de datos e identificación)")
def test_insurable_age_validation():
    """TC-S1-03: Valida que solicitantes menores de 18 o mayores de 75 años no sean elegibles."""
    pass


@pytest.mark.unit
def test_consent_hash_generation():
    """TC-S1-04: Valida la generación de hash SHA-256 inalterable para auditoría de consentimiento (RC-01 / RC-04)."""
    profile_service.clear()
    request = ConsentRequest(
        document_number="1020304050",
        channel="web",
        otp_code="839201",
        terms_accepted=True,
        purpose="Perfilamiento y cotización con Open Finance",
        scope="Historial crediticio y capacidad de endeudamiento",
        validity_days=30,
    )

    record = profile_service.register_consent(request)

    assert record.document_number == "1020304050"
    assert record.status == "GRANTED"
    assert record.channel == "web"
    assert record.purpose == "Perfilamiento y cotización con Open Finance"
    assert record.scope == "Historial crediticio y capacidad de endeudamiento"
    assert record.validity_days == 30
    assert record.consent_id.startswith("CNS-")

    # 1. El hash SHA-256 debe tener exactamente 64 caracteres hexadecimales
    assert len(record.consent_hash) == 64
    assert all(c in "0123456789abcdef" for c in record.consent_hash)

    # 2. Verificación de cálculo canónico inalterable
    import hashlib
    canonical = (
        f"{request.document_number}|"
        f"{request.channel}|"
        f"{request.purpose}|"
        f"{request.scope}|"
        f"{request.validity_days}|"
        f"{request.terms_accepted}|"
        f"{record.granted_at}"
    )
    expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert record.consent_hash == expected_hash

    # 3. Alterar cualquier valor debe generar un hash completamente diferente
    tampered_canonical = canonical.replace("1020304050", "9999999999")
    tampered_hash = hashlib.sha256(tampered_canonical.encode("utf-8")).hexdigest()
    assert record.consent_hash != tampered_hash

    # 4. Verificación de vigencia activa y consulta
    assert profile_service.has_valid_consent("1020304050") is True
    assert profile_service.get_consent("1020304050") == record
    assert profile_service.has_valid_consent("9999999999") is False


@pytest.mark.unit
def test_consent_rejected_without_terms():
    """Valida que el consentimiento sea rechazado si el tomador no acepta los términos."""
    request = ConsentRequest(
        document_number="1020304050",
        channel="web",
        otp_code="839201",
        terms_accepted=False,
    )
    with pytest.raises(ValueError, match="El cliente debe aceptar expresamente los términos"):
        profile_service.register_consent(request)


@pytest.mark.unit
def test_consent_rejected_with_invalid_otp():
    """Valida el rechazo de consentimiento ante código OTP incorrecto o simulado de fallo."""
    request = ConsentRequest(
        document_number="1020304050",
        channel="web",
        otp_code="000000",
        terms_accepted=True,
    )
    with pytest.raises(ValueError, match="Código OTP de verificación incorrecto"):
        profile_service.register_consent(request)

