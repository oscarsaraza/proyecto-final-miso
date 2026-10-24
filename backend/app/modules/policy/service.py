"""Emisión de pólizas: una por cotización vigente, con su evento PolicyIssued en el outbox (HU-WEB-05, HU-WEB-14)."""
from datetime import datetime, timezone
from typing import Callable, List, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.outbox import OutboxMessageDB
from app.modules.policy.models import (
    POLICY_NUMBER_SEQ,
    PartnerPolicyIssueRequest,
    PartnerPolicyResponse,
    PolicyDB,
    PolicyIssueRequest,
    PolicyRecord,
)
from app.modules.rating.models import QuoteDB


class QuoteNotFoundError(Exception):
    pass


class QuoteExpiredError(Exception):
    pass


class PolicyNotFoundError(Exception):
    pass


def one_year_after(moment: datetime) -> datetime:
    """Mismo día y hora del año siguiente; el 29 de febrero pasa al 28."""
    try:
        return moment.replace(year=moment.year + 1)
    except ValueError:
        return moment.replace(year=moment.year + 1, day=28)


class PolicyService:
    """Emisión atómica e idempotente: una sola póliza por cotización (HU-WEB-05, HU-WEB-14, HA-11, HA-14)."""

    def __init__(self, now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self.now = now

    async def issue_policy(self, session: AsyncSession, request: PolicyIssueRequest) -> PolicyRecord:
        """Emite la póliza de la cotización; si ya existe, la devuelve aunque la cotización haya vencido."""
        quote = await session.get(QuoteDB, request.quote_id)
        if quote is None:
            raise QuoteNotFoundError()
        policy = await self.find_by_quote(session, quote.quote_id) or await self.create(session, quote, request)
        return PolicyRecord.model_validate(policy)

    async def find_by_quote(self, session: AsyncSession, quote_id: str) -> Optional[PolicyDB]:
        return await session.scalar(select(PolicyDB).where(PolicyDB.quote_id == quote_id))

    async def create(self, session: AsyncSession, quote: QuoteDB, request: PolicyIssueRequest) -> PolicyDB:
        """Guarda la póliza y su evento en una transacción; si otra petición ganó la carrera, devuelve la suya."""
        issued_at = self.now()
        if quote.expires_at <= issued_at:
            raise QuoteExpiredError()
        sequence = await session.scalar(select(POLICY_NUMBER_SEQ.next_value()))
        policy = await session.scalar(
            insert(PolicyDB)
            .values(
                policy_number=f"POL-{issued_at.year}-{sequence:05d}",
                quote_id=quote.quote_id,
                partner_id=quote.partner_id,
                insured_document=quote.document_number,
                beneficiaries=request.beneficiaries,
                conditions=next(tier for tier in quote.tiers if tier["tier"] == request.tier),
                issued_at=issued_at,
                valid_until=one_year_after(issued_at),
            )
            .on_conflict_do_nothing(index_elements=["quote_id"])
            .returning(PolicyDB)
        )
        if policy:
            payload = PolicyRecord.model_validate(policy).model_dump(mode="json")
            session.add(OutboxMessageDB(aggregate_id=policy.policy_number, event_type="PolicyIssued", payload=payload))
        await session.commit()
        return policy or await self.find_by_quote(session, quote.quote_id)

    async def lock(self, session: AsyncSession, policy_number: str) -> PolicyDB:
        """Póliza bloqueada hasta que termine la transacción, para que sus cobros se atiendan de uno en uno."""
        policy = await session.scalar(
            select(PolicyDB).where(PolicyDB.policy_number == policy_number).with_for_update()
        )
        if policy is None:
            raise PolicyNotFoundError()
        return policy

    def activate(self, policy: PolicyDB) -> None:
        """La póliza pagada queda activa (S8: ACTIVA_PAGADA)."""
        policy.status = "ACTIVE"

    # -- Métodos B2B Quote Edge (HU-WEB-14) ----------------------------------------------------

    async def issue_partner_policy(
        self,
        session: AsyncSession,
        request: PartnerPolicyIssueRequest,
        partner_id: str,
    ) -> PartnerPolicyResponse:
        """
        Emite una póliza desde el canal del socio B2B de forma atómica e idempotente (HU-WEB-14, HA-11, HA-14).
        Asegura que la cotización pertenezca al socio autenticado; si pertenece a otro socio
        o no existe, eleva QuoteNotFoundError (se usa 404 Not Found para prevenir enumeración horizontal).
        """
        quote = await session.get(QuoteDB, request.quote_id)
        if quote is None or quote.partner_id != partner_id:
            raise QuoteNotFoundError()

        # Idempotencia: si la cotización ya fue emitida, devolvemos la póliza existente
        existing = await self.find_by_quote(session, quote.quote_id)
        if existing is not None:
            return PartnerPolicyResponse.model_validate(existing)

        issued_at = self.now()
        if quote.expires_at <= issued_at:
            raise QuoteExpiredError()

        tier_condition = next((tier for tier in quote.tiers if tier.get("tier") == request.tier), None)
        if not tier_condition:
            raise ValueError(f"El plan {request.tier} no se encuentra en las opciones cotizadas")

        sequence = await session.scalar(select(POLICY_NUMBER_SEQ.next_value()))
        policy = await session.scalar(
            insert(PolicyDB)
            .values(
                policy_number=f"POL-{issued_at.year}-{sequence:05d}",
                quote_id=quote.quote_id,
                partner_id=partner_id,
                insured_document=quote.document_number,
                beneficiaries=request.beneficiaries,
                conditions=tier_condition,
                issued_at=issued_at,
                valid_until=one_year_after(issued_at),
            )
            .on_conflict_do_nothing(index_elements=["quote_id"])
            .returning(PolicyDB)
        )
        if policy:
            payload = PolicyRecord.model_validate(policy).model_dump(mode="json")
            session.add(OutboxMessageDB(aggregate_id=policy.policy_number, event_type="PolicyIssued", payload=payload))
        await session.commit()

        final_policy = policy or await self.find_by_quote(session, quote.quote_id)
        return PartnerPolicyResponse.model_validate(final_policy)

    async def get_partner_policy(
        self,
        session: AsyncSession,
        policy_number: str,
        partner_id: str,
    ) -> Optional[PartnerPolicyResponse]:
        """Consulta el detalle de una póliza perteneciente al socio autenticado (HU-WEB-14)."""
        policy = await session.scalar(
            select(PolicyDB).where(
                PolicyDB.policy_number == policy_number,
                PolicyDB.partner_id == partner_id,
            )
        )
        if policy is None:
            return None
        return PartnerPolicyResponse.model_validate(policy)

    async def list_partner_policies(
        self,
        session: AsyncSession,
        partner_id: str,
    ) -> List[PartnerPolicyResponse]:
        """Proyección de lectura CQRS del histórico de pólizas emitidas por el socio B2B (HU-WEB-14, HA-04)."""
        result = await session.scalars(
            select(PolicyDB)
            .where(PolicyDB.partner_id == partner_id)
            .order_by(PolicyDB.issued_at.desc())
        )
        return [PartnerPolicyResponse.model_validate(p) for p in result.all()]


policy_service = PolicyService()
