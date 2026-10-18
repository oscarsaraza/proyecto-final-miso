"""Servicio de perfil de tomador y validación de consentimiento Open Finance (HU-WEB-01 / TC-S1-04)."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.profile.models import (
    CityDB,
    CityResponse,
    ClientIdentification,
    ConsentRecord,
    ConsentRequest,
    FinancialEntityDB,
    FinancialEntityResponse,
)


class ConsentError(ValueError):
    """Excepción para errores en el registro o validación de consentimiento."""
    pass


class IneligibleAgeError(ValueError):
    """Excepción cuando el solicitante está fuera del rango asegurable de 18 a 75 años (HU-WEB-02 / TC-S1-03)."""
    pass


class ProfileService:
    def __init__(self, now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self._now = now
        self._consents: Dict[str, ConsentRecord] = {}

    def validate_insurable_age(self, client: ClientIdentification) -> bool:
        """Verifica que la edad esté en el rango asegurable de 18 a 75 años (HU-WEB-02 / TC-S1-03)."""
        today = self._now().date()
        if client.birth_date > today:
            raise IneligibleAgeError("La fecha de nacimiento no puede ser una fecha futura.")
        age = today.year - client.birth_date.year - ((today.month, today.day) < (client.birth_date.month, client.birth_date.day))
        if not (18 <= age <= 75):
            raise IneligibleAgeError(
                f"El solicitante tiene {age} años. Debe tener entre 18 y 75 años para ser asegurable."
            )
        return True

    def register_consent(self, request: ConsentRequest) -> ConsentRecord:
        """Genera registro auditable de consentimiento con hash SHA-256 (HU-WEB-01 / TC-S1-04).

        Nota de simulación (Sprint 1):
        El backend valida el formato del código OTP recibido (6 dígitos numéricos) y
        simula el rechazo ante el código de prueba '000000'. En el alcance del Sprint 1
        no se emite ni se comprueba un OTP en tiempo real. La implementación del ciclo
        completo de OTP (generación criptográfica, envío multicanal, vencimiento/TTL y
        consumo de un solo uso) se gestionará como tarea de seguimiento en el Sprint 2.
        """
        if not request.terms_accepted:
            raise ConsentError("El cliente debe aceptar expresamente los términos y condiciones de tratamiento de datos.")

        # Validación de OTP: el código no puede ser inválido o nulo; '000000' simula OTP rechazado / expirado
        if request.otp_code == "000000":
            raise ConsentError("Código OTP de verificación incorrecto o expirado.")

        now = self._now()
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
        return self._now() < expires

    def clear(self):
        """Limpia el almacén de consentimientos en memoria."""
        self._consents.clear()

    async def seed_default_catalogs(self, session: AsyncSession) -> None:
        """Siembra de forma idempotente las entidades bancarias y las 100 ciudades principales de Colombia."""
        # 1. Entidades financieras supervisadas por la SFC
        existing_entity_codes = set((await session.execute(select(FinancialEntityDB.code))).scalars().all())
        for entity in DEFAULT_FINANCIAL_ENTITIES:
            if entity["code"] not in existing_entity_codes:
                session.add(FinancialEntityDB(code=entity["code"], name=entity["name"], is_active=True))

        # 2. Ciudades principales según DANE
        existing_city_codes = set((await session.execute(select(CityDB.code))).scalars().all())
        for city in DEFAULT_CITIES:
            if city["code"] not in existing_city_codes:
                session.add(CityDB(code=city["code"], name=city["name"], is_active=True))

        await session.commit()

    async def get_active_financial_entities(self, session: AsyncSession) -> List[FinancialEntityResponse]:
        """Obtiene el catálogo de entidades financieras activas ordenadas alfabéticamente."""
        stmt = (
            select(FinancialEntityDB)
            .where(FinancialEntityDB.is_active == True)  # noqa: E712
            .order_by(FinancialEntityDB.name.asc())
        )
        result = await session.execute(stmt)
        return [FinancialEntityResponse.model_validate(e) for e in result.scalars().all()]

    async def get_active_cities(self, session: AsyncSession) -> List[CityResponse]:
        """Obtiene el catálogo de ciudades activas ordenadas alfabéticamente."""
        stmt = (
            select(CityDB)
            .where(CityDB.is_active == True)  # noqa: E712
            .order_by(CityDB.name.asc())
        )
        result = await session.execute(stmt)
        return [CityResponse.model_validate(c) for c in result.scalars().all()]


# --- Catálogo inicial: Establecimientos bancarios vigilados por la SFC ---
DEFAULT_FINANCIAL_ENTITIES = [
    {"code": "BANCO_UNION", "name": "Banco Unión"},
    {"code": "BANCOLOMBIA", "name": "Bancolombia"},
    {"code": "BANCO_DE_BOGOTA", "name": "Banco de Bogotá"},
    {"code": "DAVIVIENDA", "name": "Davivienda"},
    {"code": "BBVA_COLOMBIA", "name": "BBVA Colombia"},
    {"code": "BANCO_DE_OCCIDENTE", "name": "Banco de Occidente"},
    {"code": "BANCO_POPULAR", "name": "Banco Popular"},
    {"code": "BANCO_AV_VILLAS", "name": "Banco AV Villas"},
    {"code": "BANCO_CAJA_SOCIAL", "name": "Banco Caja Social"},
    {"code": "SCOTIABANK_COLPATRIA", "name": "Scotiabank Colpatria"},
    {"code": "ITAU_COLOMBIA", "name": "Itaú Colombia"},
    {"code": "BANCO_GNB_SUDAMERIS", "name": "Banco GNB Sudameris"},
    {"code": "BANCO_AGRARIO", "name": "Banco Agrario de Colombia"},
    {"code": "BANCO_FALABELLA", "name": "Banco Falabella"},
    {"code": "BANCO_PICHINCHA", "name": "Banco Pichincha"},
    {"code": "BANCO_SANTANDER", "name": "Banco Santander Colombia"},
    {"code": "BANCAMIA", "name": "Bancamía"},
    {"code": "BANCO_W", "name": "Banco W"},
    {"code": "BANCO_MUNDO_MUJER", "name": "Banco Mundo Mujer"},
    {"code": "BANCO_SERFINANZA", "name": "Banco Serfinanza"},
    {"code": "BANCO_FINANDINA", "name": "Banco Finandina"},
    {"code": "BANCO_COOMEVA", "name": "Banco Coomeva"},
    {"code": "BANCO_COOPCENTRAL", "name": "Banco Cooperativo Coopcentral"},
    {"code": "BAN100", "name": "Ban100"},
    {"code": "BANCO_CONTACTAR", "name": "Banco Contactar"},
    {"code": "LULO_BANK", "name": "Lulo Bank"},
    {"code": "NU_COLOMBIA", "name": "Nu Colombia Compañía de Financiamiento"},
    {"code": "UALA", "name": "Ualá"},
    {"code": "BTG_PACTUAL", "name": "Banco BTG Pactual Colombia"},
    {"code": "CITIBANK", "name": "Citibank Colombia"},
    {"code": "JP_MORGAN", "name": "Banco J.P. Morgan Colombia"},
    {"code": "BNP_PARIBAS", "name": "BNP Paribas Colombia"},
]

# --- Catálogo inicial: 100 ciudades principales de Colombia (DANE) ---
DEFAULT_CITIES = [
    {"code": "BOGOTA", "name": "Bogotá, D.C."},
    {"code": "MEDELLIN", "name": "Medellín"},
    {"code": "CALI", "name": "Cali"},
    {"code": "BARRANQUILLA", "name": "Barranquilla"},
    {"code": "CARTAGENA", "name": "Cartagena de Indias"},
    {"code": "CUCUTA", "name": "Cúcuta"},
    {"code": "SOLEDAD", "name": "Soledad"},
    {"code": "IBAGUE", "name": "Ibagué"},
    {"code": "BUCARAMANGA", "name": "Bucaramanga"},
    {"code": "VILLAVICENCIO", "name": "Villavicencio"},
    {"code": "SANTA_MARTA", "name": "Santa Marta"},
    {"code": "SOACHA", "name": "Soacha"},
    {"code": "VALLEDUPAR", "name": "Valledupar"},
    {"code": "PEREIRA", "name": "Pereira"},
    {"code": "BELLO", "name": "Bello"},
    {"code": "MONTERIA", "name": "Montería"},
    {"code": "PASTO", "name": "Pasto"},
    {"code": "MANIZALES", "name": "Manizales"},
    {"code": "NEIVA", "name": "Neiva"},
    {"code": "BUENAVENTURA", "name": "Buenaventura"},
    {"code": "PALMIRA", "name": "Palmira"},
    {"code": "ARMENIA", "name": "Armenia"},
    {"code": "FLORIDABLANCA", "name": "Floridablanca"},
    {"code": "POPAYAN", "name": "Popayán"},
    {"code": "SINCELEJO", "name": "Sincelejo"},
    {"code": "ITAGUI", "name": "Itagüí"},
    {"code": "BARRANCABERMEJA", "name": "Barrancabermeja"},
    {"code": "RIOHACHA", "name": "Riohacha"},
    {"code": "ENVIGADO", "name": "Envigado"},
    {"code": "TULUA", "name": "Tuluá"},
    {"code": "DOSQUEBRADAS", "name": "Dosquebradas"},
    {"code": "TUMACO", "name": "Tumaco"},
    {"code": "TUNJA", "name": "Tunja"},
    {"code": "GIRON", "name": "Girón"},
    {"code": "APARTADO", "name": "Apartadó"},
    {"code": "FLORENCIA", "name": "Florencia"},
    {"code": "URIBIA", "name": "Uribia"},
    {"code": "IPIALES", "name": "Ipiales"},
    {"code": "TURBO", "name": "Turbo"},
    {"code": "MAICAO", "name": "Maicao"},
    {"code": "PIEDECUESTA", "name": "Piedecuesta"},
    {"code": "YOPAL", "name": "Yopal"},
    {"code": "OCANA", "name": "Ocaña"},
    {"code": "FUSAGASUGA", "name": "Fusagasugá"},
    {"code": "CARTAGO", "name": "Cartago"},
    {"code": "FACATATIVA", "name": "Facatativá"},
    {"code": "CHIA", "name": "Chía"},
    {"code": "MAGANGUE", "name": "Magangué"},
    {"code": "PITALITO", "name": "Pitalito"},
    {"code": "CAUCASIA", "name": "Caucasia"},
    {"code": "ZIPAQUIRA", "name": "Zipaquirá"},
    {"code": "MALAMBO", "name": "Malambo"},
    {"code": "RIONEGRO", "name": "Rionegro"},
    {"code": "LORICA", "name": "Lorica"},
    {"code": "JAMUNDI", "name": "Jamundí"},
    {"code": "QUIBDO", "name": "Quibdó"},
    {"code": "BUGA", "name": "Guadalajara de Buga"},
    {"code": "YUMBO", "name": "Yumbo"},
    {"code": "SOGAMOSO", "name": "Sogamoso"},
    {"code": "DUITAMA", "name": "Duitama"},
    {"code": "GIRARDOT", "name": "Girardot"},
    {"code": "CIENAGA", "name": "Ciénaga"},
    {"code": "MADRID", "name": "Madrid"},
    {"code": "SABANETA", "name": "Sabaneta"},
    {"code": "MOSQUERA", "name": "Mosquera"},
    {"code": "LA_ESTRELLA", "name": "La Estrella"},
    {"code": "FUNZA", "name": "Funza"},
    {"code": "EL_CARMEN_DE_BOLIVAR", "name": "El Carmen de Bolívar"},
    {"code": "SAHAGUN", "name": "Sahagún"},
    {"code": "CERETE", "name": "Cereté"},
    {"code": "ARJONA", "name": "Arjona"},
    {"code": "CALDAS", "name": "Caldas"},
    {"code": "COPACABANA", "name": "Copacabana"},
    {"code": "SAN_ANDRES_SOTAVENTO", "name": "San Andrés de Sotavento"},
    {"code": "TIERRALTA", "name": "Tierralta"},
    {"code": "SAMPUES", "name": "Sampués"},
    {"code": "EL_CARMEN_DE_VIBORAL", "name": "El Carmen de Viboral"},
    {"code": "GUARNE", "name": "Guarne"},
    {"code": "SIBATE", "name": "Sibaté"},
    {"code": "ACACIAS", "name": "Acacías"},
    {"code": "PRADERA", "name": "Pradera"},
    {"code": "FLORIDA", "name": "Florida"},
    {"code": "ZARZAL", "name": "Zarzal"},
    {"code": "SEVILLA", "name": "Sevilla"},
    {"code": "LA_CEJA", "name": "La Ceja"},
    {"code": "BARBOSA", "name": "Barbosa"},
    {"code": "CAREPA", "name": "Carepa"},
    {"code": "CHIGORODO", "name": "Chigorodó"},
    {"code": "EL_BAGRE", "name": "El Bagre"},
    {"code": "SANTA_ROSA_DE_CABAL", "name": "Santa Rosa de Cabal"},
    {"code": "LA_VIRGINIA", "name": "La Virginia"},
    {"code": "CHINCHINA", "name": "Chinchiná"},
    {"code": "VILLAMARIA", "name": "Villamaría"},
    {"code": "GARZON", "name": "Garzón"},
    {"code": "LA_PLATA", "name": "La Plata"},
    {"code": "PUERTO_ASIS", "name": "Puerto Asís"},
    {"code": "SAN_VICENTE_CAGUAN", "name": "San Vicente del Caguán"},
    {"code": "AGUACHICA", "name": "Aguachica"},
    {"code": "AGUSTIN_CODAZZI", "name": "Agustín Codazzi"},
    {"code": "EL_BANCO", "name": "El Banco"},
]

profile_service = ProfileService()
