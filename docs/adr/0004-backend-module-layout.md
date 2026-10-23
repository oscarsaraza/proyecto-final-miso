# ADR 0004 · Backend: fixed file layout per module

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

[ADR 0003](0003-backend-hexagonal-architecture.md) makes each module a hexagon. Today the layout varies:
`models.py` mixes Pydantic models and tables in `auth`, `payments`, `policy`, `profile` and `rating`;
`identity` splits them into `models.py` and `db_models.py` and keeps pure rules in `policy.py`; errors
live in each `service.py`; `payments` adds `gateway.py`; `identity/service.py` has 512 lines. Test fakes
live in `backend/tests/conftest.py` (`InMemorySessionTestDouble`, `FakeClock`, `RecordingSmsSender`),
plus a copy of the session double in `tests/unit/test_auth_service.py`.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Five fixed files per module, split only by size | Code lands in a known place; small; reviews check one layout | Large modules need the split rule |
| B. A folder per layer (`entities/`, `use_cases/`, `repositories/`) | Familiar from hexagonal examples | Many near-empty files; a use case scattered across folders |
| C. Free layout per module | No migration | The drift we have today |

## Decision

Option A.

```
backend/app/
  main.py, dependencies.py   composition root: app, middleware, routers, lifespan; dependency
                             functions that build adapters and services (routers import these)
  core/                      shared infrastructure; imports no module
    config.py                settings
    database.py              engine, session factory, get_db_session, UnitOfWork port and adapter
    security.py              hashing, tokens, require_roles dependencies
    middleware.py, idempotency.py, outbox.py, sms.py (shared SmsSender port and adapters)
  bff/<channel>/router.py    driving adapter per client channel (ADR 0005)
  modules/<domain>/
    domain.py                entities, value objects, pure rules, domain errors
    ports.py                 Protocols for this module's repositories and providers
    service.py               application service: the use cases
    schemas.py               Pydantic request and response models: the module's API contract
    adapters.py              SQLAlchemy tables, repositories, provider clients
```

Rules:

1. These five files are the whole module: no `repositories/`, `use_cases/` or `entities/` folders.
2. `domain.py` imports nothing from the app. `service.py` imports `domain.py`, `ports.py` and shared
   ports in `core`, never `schemas.py` or `adapters.py`. Routers convert between schemas and domain types.
3. Only the composition root and tests import `adapters.py`. Another module imports only `service.py`
   and `domain.py`.
4. When a file passes about 400 lines: `adapters.py` becomes `adapters/` with `db.py` and
   `<provider>.py`; `service.py` splits by use case into `service_<use_case>.py`. No other split.
5. Fakes of ports live in `backend/tests`, never in `app/`: shared fakes in `tests/conftest.py`, a fake
   used by one file in that file. `tests/unit` uses fakes; `tests/integration` uses real PostgreSQL.

## Consequences

- Easier: one place for each kind of code; reviews check imports against rules 2 and 3.
- Harder: small modules carry five files.
- Migration, when each module is next touched:

| Today | Target |
|---|---|
| Pydantic part of `models.py`; all of `identity/models.py` | `schemas.py` |
| Tables and sequences in `models.py`; `identity/db_models.py`; `UserDB` re-exported by `auth/__init__.py` | `adapters.py`; no re-export of tables |
| Exceptions in `service.py`; `HTTPException` in `auth/service.py` | `domain.py` (ADR 0007) |
| `identity/policy.py`; pure functions in `rating/service.py`; `ensure_chargeable` in `payments/service.py` | `domain.py`, except `client_ip`, which reads HTTP headers and moves to `bff/auth/router.py` |
| `ScoreProvider` and `neutral_score_provider` in `rating/service.py` | `rating/ports.py` and `rating/adapters.py` |
| `payments/gateway.py` | `PaymentGateway` in `ports.py`; `SimulatedGateway` in `adapters.py`; `GatewayUnavailableError` in `domain.py` |
| `core/sms.py` | stays in `core`: port and adapters shared by modules |
| Services created at import (`payment_service = …`) | built in `dependencies.py` |
| `identity/service.py` (512 lines) | queries to `adapters.py`; if still over 400 lines, `service_<use_case>.py` |
| `tests/unit/test_insured_auth.py`, `test_insured_logout.py` (marked `integration`, use PostgreSQL) | fakes in `tests/unit`, or move to `tests/integration` |
| `claims/` (only `__init__.py`) | gets its files with its first story |

## Security and privacy impact

A module's tables, queries and provider credentials sit only in its `adapters.py` (shared ones in
`core`), so a review of a module's data access and secrets reads one file. A route with a response
schema returns only the fields that schema declares, so a table column with personal data does not
reach a client by accident.
