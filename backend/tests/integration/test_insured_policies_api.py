"""Billetera del asegurado contra PostgreSQL (HU-MOV-04: TC-01, TC-02, TC-03)."""
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.modules.identity.service import insured_auth_service
from app.modules.policy.models import PolicyDB
from app.modules.policy.service import policy_service
from app.modules.rating.models import QuoteDB

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("seeded_insured")]

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
MARIA_DOCUMENT = "1020304050"
OTHER_DOCUMENT = "9080706050"
URL = "/api/v1/insured/policies"
CARD_FIELDS = {"policy_number", "plan", "holder_name", "coverages", "valid_from", "valid_until"}


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setattr(policy_service, "now", lambda: NOW)


def tier(plan: str = "standard") -> dict:
    return {
        "tier": plan,
        "monthly_premium": 100000.0,
        "annual_premium": 1200000.0,
        "coverages": [
            {"id": "rc", "name": "Responsabilidad civil", "limit": 1e8, "deductible": 0.0},
            {"id": "pt", "name": "Pérdida total", "limit": 5e7, "deductible": 1e6, "optional": True, "included": False},
        ],
        "breakdown": [],
    }


async def add_policy(session, number: str, document: str, status: str, valid_until: datetime, plan: str = "standard"):
    quote_id = f"Q-{number[-5:]}"
    session.add(
        QuoteDB(
            quote_id=quote_id,
            document_number=document,
            status="active",
            score_applied=700.0,
            tiers=[tier(plan)],
            created_at=NOW - timedelta(days=30),
            expires_at=NOW - timedelta(days=29),
        )
    )
    await session.flush()
    session.add(
        PolicyDB(
            policy_number=number,
            quote_id=quote_id,
            insured_document=document,
            beneficiaries=[{"name": "Beneficiaria de prueba", "share": 100}],
            conditions=tier(plan),
            status=status,
            issued_at=valid_until - timedelta(days=365),
            valid_until=valid_until,
        )
    )
    await session.commit()


def insured_headers(user_id: str = "ins-0001", ver: int = 0, **kwargs) -> dict:
    token = create_access_token(
        subject=user_id, role="insured", claims={"channel": "mobile", "type": "access", "ver": ver}, **kwargs
    )
    return {"Authorization": f"Bearer {token}"}


async def test_tc_01_devuelve_solo_las_polizas_activas_y_vigentes_del_titular(async_client: AsyncClient, postgres_session):
    await add_policy(postgres_session, "POL-2026-00001", MARIA_DOCUMENT, "ACTIVE", NOW + timedelta(days=200), "premium")
    await add_policy(postgres_session, "POL-2026-00002", MARIA_DOCUMENT, "ACTIVE", NOW + timedelta(days=10))
    await add_policy(postgres_session, "POL-2026-00003", MARIA_DOCUMENT, "ISSUED", NOW + timedelta(days=300))
    await add_policy(postgres_session, "POL-2025-00004", MARIA_DOCUMENT, "ACTIVE", NOW - timedelta(days=1))
    await add_policy(postgres_session, "POL-2026-00005", MARIA_DOCUMENT, "CANCELLED", NOW + timedelta(days=100))
    await add_policy(postgres_session, "POL-2025-00006", MARIA_DOCUMENT, "ACTIVE", NOW)

    response = await async_client.get(URL, headers=insured_headers())

    assert response.status_code == 200
    policies = response.json()["policies"]
    assert [p["policy_number"] for p in policies] == ["POL-2026-00002", "POL-2026-00001"]
    premium = policies[1]
    assert premium["plan"] == "premium"
    assert premium["holder_name"] == "María Ruiz"
    assert premium["coverages"] == [{"name": "Responsabilidad civil", "limit": 1e8}]
    assert datetime.fromisoformat(premium["valid_until"]) == NOW + timedelta(days=200)
    assert datetime.fromisoformat(premium["valid_from"]) == NOW + timedelta(days=200) - timedelta(days=365)


async def test_tc_01_sin_polizas_vigentes_devuelve_una_lista_vacia(async_client: AsyncClient):
    response = await async_client.get(URL, headers=insured_headers())

    assert response.status_code == 200
    assert response.json() == {"policies": []}


async def test_tc_02_ignora_identificadores_del_cliente_y_no_devuelve_polizas_ajenas(
    async_client: AsyncClient, postgres_session
):
    await insured_auth_service.register(
        postgres_session,
        user_id="ins-0002",
        email="otro.asegurado@example.com",
        full_name="Asegurado de Prueba",
        document_number=OTHER_DOCUMENT,
        phone="+573000000000",
        password="Prueba2026!",
    )
    await add_policy(postgres_session, "POL-2026-00011", MARIA_DOCUMENT, "ACTIVE", NOW + timedelta(days=50))
    await add_policy(postgres_session, "POL-2026-00012", OTHER_DOCUMENT, "ACTIVE", NOW + timedelta(days=50))

    response = await async_client.get(
        URL, params={"document_number": OTHER_DOCUMENT, "user_id": "ins-0002"}, headers=insured_headers()
    )

    assert response.status_code == 200
    assert [p["policy_number"] for p in response.json()["policies"]] == ["POL-2026-00011"]


@pytest.mark.parametrize(
    "headers",
    [
        {},
        insured_headers(expires_delta=timedelta(seconds=-1)),
        {"Authorization": insured_headers()["Authorization"][:-2] + "xx"},
        insured_headers(ver=1),
        insured_headers(user_id="ins-9999"),
    ],
    ids=["sin-token", "vencido", "alterado", "sesion-revocada", "cuenta-inexistente"],
)
async def test_tc_02_sin_sesion_valida_responde_401(async_client: AsyncClient, headers: dict):
    response = await async_client.get(URL, headers=headers)

    assert response.status_code == 401
    assert "policies" not in response.json()


async def test_tc_02_token_de_asesor_responde_403(async_client: AsyncClient):
    token = create_access_token(subject="asesor@solventa.com", role="advisor")

    response = await async_client.get(URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


async def test_tc_03_la_tarjeta_no_incluye_documento_beneficiarios_ni_prima(async_client: AsyncClient, postgres_session):
    await add_policy(postgres_session, "POL-2026-00021", MARIA_DOCUMENT, "ACTIVE", NOW + timedelta(days=50))

    response = await async_client.get(URL, headers=insured_headers())

    card = response.json()["policies"][0]
    assert set(card) == CARD_FIELDS
    assert set(card["coverages"][0]) == {"name", "limit"}
    assert MARIA_DOCUMENT not in response.text
    assert "Beneficiaria" not in response.text and "premium\":" not in response.text
