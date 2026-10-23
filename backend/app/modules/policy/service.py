"""Emisión de pólizas: una por cotización vigente, con su evento PolicyIssued en el outbox (HU-WEB-05)."""
from datetime import datetime, timezone
from typing import Callable, List, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.outbox import OutboxMessageDB
from app.modules.policy.models import (
    POLICY_NUMBER_SEQ,
    CardCoverage,
    InsuredPolicyCard,
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
    """Emisión atómica e idempotente: una sola póliza por cotización (HU-WEB-05, HA-11)."""

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


    async def active_for_holder(
        self, session: AsyncSession, document_number: str, holder_name: str
    ) -> List[InsuredPolicyCard]:
        """Pólizas pagadas y vigentes del titular, como tarjetas de la billetera (HU-MOV-04)."""
        policies = await session.scalars(
            select(PolicyDB)
            .where(
                PolicyDB.insured_document == document_number,
                PolicyDB.status == "ACTIVE",
                PolicyDB.valid_until > self.now(),
            )
            .order_by(PolicyDB.issued_at)
        )
        return [self.card(policy, holder_name) for policy in policies]

    @staticmethod
    def card(policy: PolicyDB, holder_name: str) -> InsuredPolicyCard:
        conditions = policy.conditions
        return InsuredPolicyCard(
            policy_number=policy.policy_number,
            plan=conditions["tier"],
            holder_name=holder_name,
            coverages=[
                CardCoverage(name=c["name"], limit=c["limit"])
                for c in conditions["coverages"]
                if c.get("included", True)
            ],
            valid_from=policy.issued_at,
            valid_until=policy.valid_until,
        )


policy_service = PolicyService()
