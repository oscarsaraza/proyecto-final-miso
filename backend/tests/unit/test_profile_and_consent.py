"""Pruebas unitarias de asegurabilidad y consentimiento Open Finance (TC-S1-03, TC-S1-04)."""
import pytest
from datetime import date
from app.modules.profile.models import ClientIdentification, ConsentRequest
from app.modules.profile.service import profile_service


@pytest.mark.unit
def test_profile_service_raises_not_implemented():
    """Valida que los métodos del servicio de perfil lancen NotImplementedError antes de implementar HU-WEB-01 y 02."""
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

    consent_req = ConsentRequest(
        document_number="1020304050",
        channel="web",
        otp_code="982341",
        terms_accepted=True,
    )
    with pytest.raises(NotImplementedError):
        profile_service.register_consent(consent_req)


@pytest.mark.unit
@pytest.mark.skip(reason="TDD: Se habilitará al implementar HU-WEB-02 (Captura de datos e identificación)")
def test_insurable_age_validation():
    """TC-S1-03: Valida que solicitantes menores de 18 o mayores de 75 años no sean elegibles."""
    pass


@pytest.mark.unit
@pytest.mark.skip(reason="TDD: Se habilitará al implementar HU-WEB-01 (Consentimiento Open Finance)")
def test_consent_hash_generation():
    """TC-S1-04: Valida la generación de hash SHA-256 inalterable para auditoría de consentimiento."""
    pass
