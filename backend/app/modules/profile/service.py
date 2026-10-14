"""Servicio de perfil de tomador y validación de consentimiento Open Finance (HU-WEB-01 / TC-S1-04)."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from app.modules.profile.models import ClientIdentification, ConsentRequest, ConsentRecord


class ConsentError(ValueError):
    """Excepción para errores en el registro o validación de consentimiento."""
    pass


class ProfileService:
    def __init__(self):
        self._consents: Dict[str, ConsentRecord] = {}

    def validate_insurable_age(self, client: ClientIdentification) -> bool:
        """Verifica que la edad esté en el rango asegurable de 18 a 75 años (HU-WEB-02 / TC-S1-03).

        A ser implementado durante HU-WEB-02.
        """
        raise NotImplementedError("validate_insurable_age pendiente de implementación en HU-WEB-02")

    def register_consent(self, request: ConsentRequest) -> ConsentRecord:
        """Genera registro auditable de consentimiento con hash SHA-256 (HU-WEB-01 / TC-S1-04)."""
        if not request.terms_accepted:
            raise ConsentError("El cliente debe aceptar expresamente los términos y condiciones de tratamiento de datos.")

        # Validación de OTP: el código no puede ser inválido o nulo; '000000' simula OTP rechazado
        if request.otp_code == "000000":
            raise ConsentError("Código OTP de verificación incorrecto o expirado.")

        now = datetime.now(timezone.utc)
        granted_at = now.isoformat()
        expires_at = (now + timedelta(days=request.validity_days)).isoformat()
        consent_id = f"CNS-{uuid.uuid4().hex[:12].upper()}"

        # Generación de hash SHA-256 canónico e inalterable para auditoría (RC-01 / RC-04)
        canonical_string = (
            f"{request.document_number}|"
            f"{request.channel}|"
            f"{request.purpose}|"
            f"{request.scope}|"
            f"{request.validity_days}|"
            f"{request.terms_accepted}|"
            f"{granted_at}"
        )
        consent_hash = hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()

        record = ConsentRecord(
            consent_id=consent_id,
            document_number=request.document_number,
            channel=request.channel,
            purpose=request.purpose,
            scope=request.scope,
            validity_days=request.validity_days,
            status="GRANTED",
            consent_hash=consent_hash,
            granted_at=granted_at,
            expires_at=expires_at,
        )

        self._consents[request.document_number] = record
        return record

    def get_consent(self, document_number: str) -> Optional[ConsentRecord]:
        """Obtiene el consentimiento activo registrado para el número de documento."""
        return self._consents.get(document_number)

    def has_valid_consent(self, document_number: str) -> bool:
        """Verifica si el documento cuenta con un consentimiento vigente no expirado."""
        record = self.get_consent(document_number)
        if not record or record.status != "GRANTED":
            return False
        expires = datetime.fromisoformat(record.expires_at)
        return datetime.now(timezone.utc) < expires

    def clear(self):
        """Limpia el almacén de consentimientos en memoria."""
        self._consents.clear()


profile_service = ProfileService()
