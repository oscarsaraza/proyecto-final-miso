"""Motor actuarial: desglose de la prima, degradación por latencia del buró y registro de cotizaciones (HU-WEB-03 a 05, HU-WEB-10)."""
import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Awaitable, Callable, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.rating.models import (
    Coverage,
    PartnerDB,
    PartnerQuoteResponse,
    PlanTier,
    PremiumFactor,
    QuoteDB,
    QuoteRequest,
    QuoteResponse,
    QuoteTierDetail,
)

# Tasa mensual por peso asegurado del prototipo comercial (perfil de referencia: 31-40 años).
BASE_MONTHLY_RATE = 0.0002736
QUOTE_VALIDITY = timedelta(days=15)
NEUTRAL_SCORE = 700
# Recargo de la cotización con perfil parcial, el mismo de los prototipos web.
PARTIAL_PROFILE_SURCHARGE = 1.04

AGE_BANDS: List[Tuple[int, float]] = [(30, 0.92), (40, 1.0), (50, 1.18), (200, 1.42)]
OCCUPATION_MULTIPLIERS = {1: 1.0, 2: 1.1, 3: 1.25, 4: 1.45, 5: 1.7}
SCORE_BANDS: List[Tuple[int, float]] = [(800, 0.9), (650, 1.0), (500, 1.15), (0, 1.3)]
TIER_MULTIPLIERS = {PlanTier.BASIC: 0.75, PlanTier.STANDARD: 1.0, PlanTier.PREMIUM: 1.35}

ScoreProvider = Callable[[QuoteRequest, float], Awaitable[int]]


async def neutral_score_provider(request: QuoteRequest, simulated_delay: float) -> int:
    """Sustituto del buró: devuelve el puntaje neutro tras el retardo simulado."""
    if simulated_delay > 0:
        await asyncio.sleep(simulated_delay)
    return NEUTRAL_SCORE


def age_on(birth_date: date, today: date) -> int:
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def age_multiplier(age: int) -> float:
    return next(multiplier for limit, multiplier in AGE_BANDS if age <= limit)


def score_multiplier(score: int) -> float:
    return next(multiplier for floor, multiplier in SCORE_BANDS if score >= floor)


def build_breakdown(
    insured_amount: float,
    age: int,
    occupation_risk: int,
    score: int,
    tier: PlanTier,
    partial_profile: bool = False,
) -> List[PremiumFactor]:
    """Cada factor aporta lo que su multiplicador agrega sobre el subtotal acumulado; la suma es la prima."""
    base = round(insured_amount * BASE_MONTHLY_RATE)
    steps = [
        ("age", f"Ajuste por edad ({age} años)", age_multiplier(age)),
        ("occupation", f"Ajuste por riesgo de ocupación (nivel {occupation_risk})", OCCUPATION_MULTIPLIERS[occupation_risk]),
        ("payment_history", "Ajuste por historial de pago", score_multiplier(score)),
        ("plan", f"Ajuste por plan {tier.value}", TIER_MULTIPLIERS[tier]),
    ]
    if partial_profile:
        steps.append(("partial_profile", "Recargo por perfil parcial", PARTIAL_PROFILE_SURCHARGE))
    breakdown = [PremiumFactor(code="base_rate", label="Tarifa base actuarial", multiplier=1.0, amount=base)]
    subtotal = float(base)
    for code, label, multiplier in steps:
        amount = round(subtotal * (multiplier - 1))
        breakdown.append(PremiumFactor(code=code, label=label, multiplier=multiplier, amount=amount))
        subtotal += amount
    return breakdown


def coverages_for(tier: PlanTier, insured_amount: float) -> List[Coverage]:
    coverages = [Coverage(id="death", name="Muerte por cualquier causa", limit=insured_amount, deductible=0)]
    if tier in (PlanTier.STANDARD, PlanTier.PREMIUM):
        coverages.append(
            Coverage(id="disability", name="Incapacidad total y permanente", limit=insured_amount, deductible=0)
        )
    if tier == PlanTier.PREMIUM:
        coverages.append(
            Coverage(id="critical_illness", name="Enfermedades graves", limit=insured_amount * 0.5, deductible=0)
        )
    return coverages


class RatingService:
    """Motor actuarial en memoria con protección de latencia (ASR-01, ASR-02, HA-01, HA-05)."""

    def __init__(
        self,
        bureau_timeout: float = settings.BUREAU_TIMEOUT_SECONDS,
        score_provider: ScoreProvider = neutral_score_provider,
        today: Callable[[], date] = date.today,
    ):
        self.bureau_timeout = bureau_timeout
        self._score_provider = score_provider
        self._today = today

    async def calculate_quote(
        self,
        request: QuoteRequest,
        simulated_bureau_delay: float = 0.0,
    ) -> QuoteResponse:
        try:
            score = await asyncio.wait_for(self._score_provider(request, simulated_bureau_delay), self.bureau_timeout)
            degradation_reason = None
        except TimeoutError:
            score, degradation_reason = NEUTRAL_SCORE, "TIMEOUT_EXCEEDED"
        age = age_on(date.fromisoformat(request.birth_date), self._today())

        tiers = []
        for tier in PlanTier:
            breakdown = build_breakdown(
                request.insured_amount, age, request.occupation_risk, score, tier, partial_profile=bool(degradation_reason)
            )
            monthly = float(sum(factor.amount for factor in breakdown))
            tiers.append(
                QuoteTierDetail(
                    tier=tier,
                    monthly_premium=monthly,
                    annual_premium=monthly * 12,
                    coverages=coverages_for(tier, request.insured_amount),
                    breakdown=breakdown,
                )
            )

        created_at = datetime.now(timezone.utc)
        return QuoteResponse(
            quote_id=f"QUO-{uuid.uuid4().hex[:12].upper()}",
            document_number=request.document_number,
            status="degraded" if degradation_reason else "active",
            degradation_reason=degradation_reason,
            score_applied=score,
            tiers=tiers,
            created_at=created_at.isoformat(),
            expires_at=(created_at + QUOTE_VALIDITY).isoformat(),
        )

    async def create_quote(
        self,
        session: AsyncSession,
        request: QuoteRequest,
        simulated_bureau_delay: float = 0.0,
        partner_id: Optional[str] = None,
    ) -> QuoteResponse:
        """Calcula la cotización y la guarda para que la emisión compruebe su vigencia (HU-WEB-05, HU-WEB-10, HA-17)."""
        quote = await self.calculate_quote(request, simulated_bureau_delay)
        session.add(
            QuoteDB(
                quote_id=quote.quote_id,
                partner_id=partner_id,
                document_number=quote.document_number,
                status=quote.status,
                degradation_reason=quote.degradation_reason,
                score_applied=quote.score_applied,
                tiers=[tier.model_dump(mode="json") for tier in quote.tiers],
                created_at=datetime.fromisoformat(quote.created_at),
                expires_at=datetime.fromisoformat(quote.expires_at),
            )
        )
        if partner_id:
            await session.execute(
                update(PartnerDB)
                .where(PartnerDB.partner_id == partner_id)
                .values(quota_used=PartnerDB.quota_used + 1)
            )
        await session.commit()
        return quote

    async def get_partner_quote(
        self,
        session: AsyncSession,
        quote_id: str,
        partner_id: str,
    ) -> Optional[PartnerQuoteResponse]:
        """Obtiene una cotización solo si existe y pertenece al socio autenticado (HU-WEB-10)."""
        stmt = select(QuoteDB).where(QuoteDB.quote_id == quote_id)
        result = await session.execute(stmt)
        quote = result.scalars().first()
        if not quote or not quote.partner_id or quote.partner_id != partner_id:
            return None
        return PartnerQuoteResponse.from_db(quote)

    async def list_partner_quotes(
        self,
        session: AsyncSession,
        partner_id: str,
    ) -> List[PartnerQuoteResponse]:
        """Lista el histórico de cotizaciones del socio autenticado (HU-WEB-10)."""
        stmt = (
            select(QuoteDB)
            .where(QuoteDB.partner_id == partner_id)
            .order_by(QuoteDB.created_at.desc())
        )
        result = await session.execute(stmt)
        quotes = result.scalars().all()
        return [PartnerQuoteResponse.from_db(q) for q in quotes]


rating_service = RatingService()
