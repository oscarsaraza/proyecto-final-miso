"""Motor actuarial de cotización en memoria con desglose de la prima por factor (HU-WEB-03 / ESC-SEG-06)."""
import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Awaitable, Callable, List, Tuple

from app.core.config import settings
from app.modules.rating.models import (
    Coverage,
    PlanTier,
    PremiumFactor,
    QuoteRequest,
    QuoteResponse,
    QuoteTierDetail,
)

# Tasa mensual por peso asegurado del prototipo comercial (perfil de referencia: 31-40 años).
BASE_MONTHLY_RATE = 0.0002736
QUOTE_VALIDITY = timedelta(days=15)
NEUTRAL_SCORE = 700

AGE_BANDS: List[Tuple[int, float]] = [(30, 0.92), (40, 1.0), (50, 1.18), (200, 1.42)]
OCCUPATION_MULTIPLIERS = {1: 1.0, 2: 1.1, 3: 1.25, 4: 1.45, 5: 1.7}
SCORE_BANDS: List[Tuple[int, float]] = [(800, 0.9), (650, 1.0), (500, 1.15), (0, 1.3)]
TIER_MULTIPLIERS = {PlanTier.BASIC: 0.75, PlanTier.STANDARD: 1.0, PlanTier.PREMIUM: 1.35}

ScoreProvider = Callable[[QuoteRequest, float], Awaitable[int]]


async def neutral_score_provider(request: QuoteRequest, simulated_delay: float) -> int:
    """Sustituto del buró hasta HU-WEB-04, que agrega el timeout y la degradación."""
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
) -> List[PremiumFactor]:
    """Cada factor aporta lo que su multiplicador agrega sobre el subtotal acumulado; la suma es la prima."""
    base = round(insured_amount * BASE_MONTHLY_RATE)
    steps = [
        ("age", f"Ajuste por edad ({age} años)", age_multiplier(age)),
        ("occupation", f"Ajuste por riesgo de ocupación (nivel {occupation_risk})", OCCUPATION_MULTIPLIERS[occupation_risk]),
        ("payment_history", "Ajuste por historial de pago", score_multiplier(score)),
        ("plan", f"Ajuste por plan {tier.value}", TIER_MULTIPLIERS[tier]),
    ]
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
        score = await self._score_provider(request, simulated_bureau_delay)
        age = age_on(date.fromisoformat(request.birth_date), self._today())

        tiers = []
        for tier in PlanTier:
            breakdown = build_breakdown(request.insured_amount, age, request.occupation_risk, score, tier)
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
            status="active",
            score_applied=score,
            tiers=tiers,
            created_at=created_at.isoformat(),
            expires_at=(created_at + QUOTE_VALIDITY).isoformat(),
        )


rating_service = RatingService()
