"""Servicio de perfil de tomador y validación de consentimiento Open Finance (Placeholder para HU-WEB-01 y HU-WEB-02)."""
from app.modules.profile.models import ClientIdentification, ConsentRequest, ConsentRecord


class ProfileService:
    def validate_insurable_age(self, client: ClientIdentification) -> bool:
        """Verifica que la edad esté en el rango asegurable de 18 a 75 años (HU-WEB-02 / TC-S1-03).

        A ser implementado durante HU-WEB-02.
        """
        raise NotImplementedError("validate_insurable_age pendiente de implementación en HU-WEB-02")

    def register_consent(self, request: ConsentRequest) -> ConsentRecord:
        """Genera registro auditable de consentimiento con hash SHA-256 (HU-WEB-01 / TC-S1-04).

        A ser implementado durante HU-WEB-01.
        """
        raise NotImplementedError("register_consent pendiente de implementación en HU-WEB-01")


profile_service = ProfileService()
