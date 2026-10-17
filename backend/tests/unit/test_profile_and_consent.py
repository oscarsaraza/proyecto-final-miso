"""Pruebas unitarias de asegurabilidad y consentimiento Open Finance (TC-S1-03, TC-S1-04)."""
import pytest
from datetime import date
from app.modules.profile.models import ClientIdentification, ConsentRequest
from app.modules.profile.service import IneligibleAgeError, ProfileService, profile_service
from datetime import datetime, timezone


@pytest.mark.unit
def test_profile_service_validate_age_eligible():
    """Valida que un cliente en el rango asegurable retorne True."""
    client = ClientIdentification(
        document_type="CC",
        document_number="1020304050",
        first_name="Carlos",
        last_name="Perez",
        birth_date=date(1996, 5, 10),
        email="carlos@test.com",
        phone="3001234567",
    )
    assert profile_service.validate_insurable_age(client) is True


@pytest.mark.unit
@pytest.mark.parametrize(
    "birth_date, is_valid",
    [
        (date(2008, 10, 16), False),  # 17 años (menor por un día)
        (date(2008, 10, 15), True),   # 18 años exactos (límite inferior)
        (date(1986, 5, 20), True),    # 40 años (plena edad asegurable)
        (date(1951, 10, 15), True),   # 75 años exactos (límite superior)
        (date(1950, 10, 15), False),  # 76 años exactos (mayor al límite)
    ],
)
def test_insurable_age_validation(birth_date, is_valid):
    """TC-S1-03: Valida que solicitantes menores de 18 o mayores de 75 años no sean elegibles."""
    service = ProfileService(now=lambda: datetime(2026, 10, 15, tzinfo=timezone.utc))
    client = ClientIdentification(
        document_type="CC",
        document_number="1020304050",
        first_name="Carlos",
        last_name="Perez",
        birth_date=birth_date,
        email="carlos@test.com",
        phone="3001234567",
    )
    if is_valid:
        assert service.validate_insurable_age(client) is True
    else:
        with pytest.raises(IneligibleAgeError) as exc_info:
            service.validate_insurable_age(client)
        assert "Debe tener entre 18 y 75 años para ser asegurable" in str(exc_info.value)


@pytest.mark.unit
def test_insurable_age_rejects_future_birth_date():
    """Valida que una fecha de nacimiento futura sea rechazada con mensaje explicativo."""
    service = ProfileService(now=lambda: datetime(2026, 10, 15, tzinfo=timezone.utc))
    client = ClientIdentification(
        document_type="CC",
        document_number="1020304050",
        first_name="Carlos",
        last_name="Perez",
        birth_date=date(2026, 10, 16),
        email="carlos@test.com",
        phone="3001234567",
    )
    with pytest.raises(IneligibleAgeError) as exc_info:
        service.validate_insurable_age(client)
    assert "La fecha de nacimiento no puede ser una fecha futura." in str(exc_info.value)


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


@pytest.mark.unit
def test_consent_expiration_deterministic():
    """Valida que has_valid_consent expire exactamente al cumplirse el periodo de vigencia."""
    from datetime import datetime, timedelta, timezone
    from app.modules.profile.service import ProfileService

    start_time = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
    current_time = start_time
    service = ProfileService(now=lambda: current_time)

    request = ConsentRequest(
        document_number="1020304050",
        channel="web",
        otp_code="839201",
        terms_accepted=True,
        validity_days=30,
    )
    record = service.register_consent(request)
    assert record.status == "GRANTED"

    # En el día 29 sigue vigente
    current_time = start_time + timedelta(days=29)
    assert service.has_valid_consent("1020304050") is True

    # En el día 30 exacto (o microsegundo después) expira
    current_time = start_time + timedelta(days=30, seconds=1)
    assert service.has_valid_consent("1020304050") is False


@pytest.mark.unit
def test_consent_rejected_with_non_numeric_otp():
    """Valida que ConsentRequest rechace códigos OTP no numéricos o con longitud errónea."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ConsentRequest(
            document_number="1020304050",
            channel="web",
            otp_code="abcdef",
            terms_accepted=True,
        )

    with pytest.raises(ValidationError):
        ConsentRequest(
            document_number="1020304050",
            channel="web",
            otp_code="12345",
            terms_accepted=True,
        )


@pytest.mark.unit
def test_consent_rejected_with_empty_purpose_or_scope():
    """Valida que ConsentRequest rechace finalidad o alcance vacíos o insuficientes."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ConsentRequest(
            document_number="1020304050",
            channel="web",
            otp_code="839201",
            terms_accepted=True,
            purpose="",
        )

    with pytest.raises(ValidationError):
        ConsentRequest(
            document_number="1020304050",
            channel="web",
            otp_code="839201",
            terms_accepted=True,
            scope="ab",
        )


@pytest.mark.unit
async def test_catalogs_service_and_seed(test_db_session):
    """HU-WEB-02.1: Valida que los catálogos se hayan sembrado y se consulten ordenados alfabéticamente."""
    entities = await profile_service.get_active_financial_entities(test_db_session)
    assert len(entities) >= 30
    assert any(e.name == "Banco Unión" for e in entities)
    assert any(e.name == "Bancolombia" for e in entities)
    assert entities == sorted(entities, key=lambda x: x.name)

    cities = await profile_service.get_active_cities(test_db_session)
    assert len(cities) == 100
    assert any(c.name == "Bogotá, D.C." for c in cities)
    assert any(c.name == "Medellín" for c in cities)
    assert cities == sorted(cities, key=lambda x: x.name)


@pytest.mark.unit
async def test_catalogs_api_endpoints(async_client):
    """HU-WEB-02.1: Valida los endpoints GET /catalogs/financial-entities y GET /catalogs/cities en el BFF."""
    res_entities = await async_client.get("/api/v1/experience/catalogs/financial-entities")
    assert res_entities.status_code == 200
    entities_data = res_entities.json()
    assert len(entities_data) >= 30
    assert any(item["name"] == "Banco Unión" for item in entities_data)

    res_cities = await async_client.get("/api/v1/experience/catalogs/cities")
    assert res_cities.status_code == 200
    cities_data = res_cities.json()
    assert len(cities_data) == 100
    assert any(item["name"] == "Bogotá, D.C." for item in cities_data)



