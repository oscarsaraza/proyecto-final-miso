---
name: code-review-python
description: Python conventions and review checklist — style, typing, hexagonal FastAPI structure (domain, ports, application services, adapters), Pydantic v2 validation, async I/O, SQLAlchemy 2 async repositories, errors, logging and pytest. Use when writing or reviewing Python code.
---

# Python — conventions and review

Applies to `*.py`. Follow it when writing Python; when reviewing, `code-review` gives the process and the
report format and this skill gives what to check. Secure patterns are in `secure-coding-python`.

## Style and naming

- PEP 8 (https://peps.python.org/pep-0008/). Use the formatter and linter the project configures; when
  none is configured, do not reformat untouched code. Adding one is a dependency change (`dependency-review`).
- Identifiers in English: `snake_case` functions and variables, `PascalCase` classes, `UPPER_CASE`
  module constants, a leading `_` for module-private helpers.
- Small functions with one purpose; early returns over nested conditionals; no mutable default arguments.
- Comments explain why, not what. Docstrings on public services and non-obvious functions.

## Typing

- Type hints on every function, including the return type of route handlers and dependencies.
- New code uses `X | None` and built-in generics (`list[str]`, `dict[str, int]`); match the module when
  it consistently uses the older `typing` forms.
- No `Any` or bare `dict` in public signatures without a reason; use a model, a `TypedDict` or a
  `Protocol`. External providers (SMS, payments, clocks) are `Protocol`s injected through constructors.

## Hexagonal structure (FastAPI)

- The domain (entities, value objects, pure rules, domain errors) imports no FastAPI, Pydantic or
  SQLAlchemy, so unit tests cover every branch without I/O.
- Application services hold the use cases and depend only on the domain and on ports (`Protocol`s for
  repositories, the unit of work and external providers); they never raise `HTTPException` or know about HTTP.
- Driving adapters (routers) are thin: parse the request, authorize, call a service, map domain errors
  to HTTP. No business rules or queries in routers.
- Driven adapters implement the ports: SQLAlchemy repositories and provider clients. Adapters are wired
  to ports in one place (dependency functions), never constructed inside services.
- A module uses another one only through its application service, never its adapters or tables.
- Request and response models (Pydantic) are separate from tables and from domain types. Every route
  declares `response_model` (or a return annotation); never return ORM objects or free-form dicts.
- Dependencies (`Depends`) for the session, the current user and roles; follow the style the module
  already uses (default-argument or `Annotated`), not a mix within one file.
- Time comes from an injected clock; datetimes are timezone-aware UTC (`datetime.now(UTC)`).
- Money and rates use `Decimal`, never `float`.

## Validation (Pydantic v2)

- Every request field is bounded: `Field(min_length=…, max_length=…, pattern=…, ge=…, le=…)`; lists have
  `max_length`; closed sets are `Literal` or `Enum`; dates are `date`, not `str`.
- Request models reject unknown fields (`model_config = ConfigDict(extra="forbid")`) unless the API
  promises otherwise.
- Validation that needs the database (exists, belongs to the caller) happens in the service, not in validators.

## Async and I/O

- No blocking calls inside `async def`: no `requests`, `time.sleep` or synchronous drivers. CPU-heavy work
  (password hashing, large exports) runs in `asyncio.to_thread`.
- Every outbound call has a timeout; `httpx.AsyncClient` is closed (`async with`) or shared through the lifespan.
- No fire-and-forget tasks without error handling; background work goes through the outbox or a queue.

## Persistence (SQLAlchemy 2, async)

- Queries live in repositories (driven adapters) that receive the request's `AsyncSession`. The
  application service decides when to commit through the unit-of-work port; roll back on error.
- No lazy loading in async code: load relations explicitly (`selectinload`) and avoid N+1 queries.
- Read-modify-write sequences that can race use `with_for_update()`, a unique constraint or an idempotency key.
- Queries that read scoped data always filter by owner or tenant (see `secure-coding-python`).
- Schema changes are versioned migrations once the project adopts them; never edit production tables by hand.

## Errors and logging

- Domain exceptions per module, subclassing a module base error; the router or an exception handler maps
  each to a status code and a fixed user message (Spanish in this product).
- Never send `str(exc)` or a stack trace to the client.
- `logging.getLogger(__name__)`, never `print`. Log events and identifiers, not personal data, tokens or bodies.

## Tests (pytest)

- Marker per test or module: `unit` (no I/O), `integration` (real database, HTTP through the ASGI app),
  `contract` (response shape consumed by the web or mobile app).
- One behavior per test; the name says the behavior and the spec or test case ID.
- Assert the status code and the body; for errors, assert the body reveals nothing extra.
- Fakes over mocks for providers and clocks; never real network calls or real personal data.

## Review checklist

- [ ] Domain without frameworks; services depend on ports only; router without business rules or
      queries; adapters wired in one place; pure rules unit-tested.
- [ ] Every request field bounded; unknown fields rejected; `response_model` declared.
- [ ] No blocking call in `async def`; timeouts on outbound calls.
- [ ] No lazy load in async; no N+1; races handled with locks, constraints or idempotency.
- [ ] `Decimal` for money; aware UTC datetimes from an injected clock.
- [ ] Domain errors mapped to fixed messages; no `str(exc)` to clients; no `print`.
- [ ] Type hints complete; no new `Any` without a reason.
- [ ] Tests at the right level with the right marker, including negative cases.

## In this repository

- Architecture: hexagonal per domain module — ADRs [0003](../../../docs/adr/0003-backend-hexagonal-architecture.md)
  (ports and adapters), [0004](../../../docs/adr/0004-backend-module-layout.md) (files per module),
  [0005](../../../docs/adr/0005-backend-bff-per-channel.md) (BFF routers),
  [0006](../../../docs/adr/0006-backend-persistence.md) (repositories and unit of work) and
  [0007](../../../docs/adr/0007-backend-errors-and-responses.md) (errors). Check new code against them. Services are module-level instances; their constructors accept clocks and providers for tests.
- Settings: one `pydantic-settings` object in `backend/app/core/config.py`.
- Tests: `backend/tests/unit/` and `backend/tests/integration/`; fixtures in `backend/tests/conftest.py`
  (`postgres_session` for a real PostgreSQL, `async_client`, `FakeClock`, `RecordingSmsSender`). Test
  names and docstrings are in Spanish and cite the story or test case ID.
- No formatter, linter or type checker is configured; SonarCloud runs in CI.
- Commands: `cd backend && poetry run pytest -m unit`, `poetry run pytest -m integration` (needs PostgreSQL), `poetry run pytest`.
