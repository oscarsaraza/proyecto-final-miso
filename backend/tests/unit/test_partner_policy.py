"""Pruebas unitarias de emisión de pólizas B2B, aislamiento multi-tenant y vigencia (HU-WEB-14)."""
from datetime import datetime, timedelta, timezone
import pytest

from app.modules.policy.models import (
    PartnerPolicyIssueRequest,
    PlanTier,
)
from app.modules.policy.service import (
    PolicyService,
    QuoteExpiredError,
    QuoteNotFoundError,
)
from app.modules.rating.models import QuoteDB


def _make_quote(
    quote_id: str = "COT-2026-00001",
    partner_id: str = "banco-aliado-1",
    expires_delta_seconds: int = 3600,
) -> QuoteDB:
    now = datetime.now(timezone.utc)
    return QuoteDB(
        quote_id=quote_id,
        partner_id=partner_id,
        document_number="1020304050",
        status="active",
        score_applied=750.0,
        tiers=[
            {
                "tier": "basic",
                "monthly_premium": 50000.0,
                "annual_premium": 600000.0,
                "coverages": [],
                "breakdown": [],
            },
            {
                "tier": "standard",
                "monthly_premium": 80000.0,
                "annual_premium": 960000.0,
                "coverages": [],
                "breakdown": [],
            },
        ],
        created_at=now,
        expires_at=now + timedelta(seconds=expires_delta_seconds),
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_issue_partner_policy_success(test_db_session):
    """Verifica la emisión exitosa de una póliza digital vinculada al partner_id."""
    quote = _make_quote("COT-B2B-01", "banco-aliado-1")
    test_db_session.add(quote)

    service = PolicyService()
    req = PartnerPolicyIssueRequest(
        quote_id="COT-B2B-01",
        tier=PlanTier.STANDARD,
        beneficiaries=[{"name": "Ana Perez", "relationship": "Hija", "percentage": 100}],
    )

    policy = await service.issue_partner_policy(test_db_session, req, "banco-aliado-1")

    assert policy.policy_number.startswith("POL-")
    assert policy.quote_id == "COT-B2B-01"
    assert policy.partner_id == "banco-aliado-1"
    assert policy.insured_document == "1020304050"
    assert policy.status == "ISSUED"
    assert policy.valid_until.year == policy.issued_at.year + 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_issue_partner_policy_idempotency(test_db_session):
    """Verifica que reintentos con la misma cotización devuelvan la misma póliza sin duplicar."""
    quote = _make_quote("COT-B2B-IDEMPOTENT", "banco-aliado-1")
    test_db_session.add(quote)

    service = PolicyService()
    req = PartnerPolicyIssueRequest(
        quote_id="COT-B2B-IDEMPOTENT",
        tier=PlanTier.STANDARD,
    )

    first_policy = await service.issue_partner_policy(test_db_session, req, "banco-aliado-1")
    second_policy = await service.issue_partner_policy(test_db_session, req, "banco-aliado-1")

    assert first_policy.policy_number == second_policy.policy_number
    assert first_policy.issued_at == second_policy.issued_at


@pytest.mark.unit
@pytest.mark.asyncio
async def test_issue_partner_policy_rejects_foreign_or_missing_quote(test_db_session):
    """Verifica rechazo con QuoteNotFoundError si la cotización pertenece a otro socio o no existe."""
    quote = _make_quote("COT-OTHER-PARTNER", "socio-competidor")
    test_db_session.add(quote)

    service = PolicyService()
    req_foreign = PartnerPolicyIssueRequest(quote_id="COT-OTHER-PARTNER", tier=PlanTier.STANDARD)
    req_missing = PartnerPolicyIssueRequest(quote_id="COT-NONEXISTENT", tier=PlanTier.STANDARD)

    with pytest.raises(QuoteNotFoundError):
        await service.issue_partner_policy(test_db_session, req_foreign, "banco-aliado-1")

    with pytest.raises(QuoteNotFoundError):
        await service.issue_partner_policy(test_db_session, req_missing, "banco-aliado-1")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_issue_expired_quote_rejected(test_db_session):
    """TC-05: Verifica que una cotización expirada levante QuoteExpiredError."""
    expired_quote = _make_quote("COT-EXPIRED", "banco-aliado-1", expires_delta_seconds=-10)
    test_db_session.add(expired_quote)

    service = PolicyService()
    req = PartnerPolicyIssueRequest(quote_id="COT-EXPIRED", tier=PlanTier.STANDARD)

    with pytest.raises(QuoteExpiredError):
        await service.issue_partner_policy(test_db_session, req, "banco-aliado-1")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_issue_partner_policy_invalid_tier(test_db_session):
    """Verifica que solicitar un tier no existente en la cotización levante ValueError."""
    quote = _make_quote("COT-TIERS", "banco-aliado-1")
    test_db_session.add(quote)

    service = PolicyService()
    req = PartnerPolicyIssueRequest(quote_id="COT-TIERS", tier=PlanTier.PREMIUM)

    with pytest.raises(ValueError, match="no se encuentra en las opciones"):
        await service.issue_partner_policy(test_db_session, req, "banco-aliado-1")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_and_list_partner_policies_isolation(test_db_session):
    """Verifica aislamiento multi-tenant en consultas individuales y proyección de lectura CQRS."""
    quote_a = _make_quote("COT-A", "banco-aliado-1")
    quote_b = _make_quote("COT-B", "socio-dos")
    test_db_session.add(quote_a)
    test_db_session.add(quote_b)

    service = PolicyService()
    policy_a = await service.issue_partner_policy(
        test_db_session,
        PartnerPolicyIssueRequest(quote_id="COT-A", tier=PlanTier.STANDARD),
        "banco-aliado-1",
    )
    policy_b = await service.issue_partner_policy(
        test_db_session,
        PartnerPolicyIssueRequest(quote_id="COT-B", tier=PlanTier.STANDARD),
        "socio-dos",
    )

    # Socio 1 consulta su propia póliza -> OK
    own = await service.get_partner_policy(test_db_session, policy_a.policy_number, "banco-aliado-1")
    assert own is not None
    assert own.policy_number == policy_a.policy_number

    # Socio 1 intenta consultar la póliza del Socio 2 -> None (confinamiento multi-tenant)
    foreign = await service.get_partner_policy(test_db_session, policy_b.policy_number, "banco-aliado-1")
    assert foreign is None

    # Listado histórico CQRS confinado exclusivamente
    policies_partner_1 = await service.list_partner_policies(test_db_session, "banco-aliado-1")
    assert len(policies_partner_1) == 1
    assert policies_partner_1[0].policy_number == policy_a.policy_number
