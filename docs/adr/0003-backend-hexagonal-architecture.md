# ADR 0003 · Backend: hexagonal architecture (ports and adapters) per domain module

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

The backend (`backend/app`) is FastAPI. Today all modules run in one FastAPI application (`app/main.py`)
and one container (`backend/Dockerfile`). The code has `core/` (shared infrastructure),
`bff/<channel>/router.py` (one router per client) and `modules/<domain>/` (`auth`, `identity`,
`payments`, `policy`, `profile`, `rating`, and `claims`, which is empty). Claims, partners and more
providers (email, storage, a real gateway and bureau) are coming; a module may later run on its own.

`README.md` and `backend/README.md` call the backend hexagonal (ports and adapters). The code follows it
only at some external boundaries:

- Ports today: the `SmsSender` Protocol in `core/sms.py` (console and Twilio adapters) and the
  `ScoreProvider` callable type in `rating/service.py` (a neutral stand-in for the credit bureau).
  `PaymentService` takes a gateway in its constructor, but `payments/gateway.py` has no Protocol, only
  `SimulatedGateway`. Clocks are injected in `identity`, `policy`, `profile` and `rating`.
- Services build SQLAlchemy queries on the `AsyncSession` they receive and call `commit()` themselves.
  Rules and persistence are mixed; only `identity/policy.py` holds pure rules.
- Modules reach into each other's tables: `policy/service.py` reads `rating`'s `QuoteDB`, and
  `payments/service.py` gets `policy`'s `PolicyDB` rows from `policy_service.lock()` and reads them.
- Services are created at import time (`payment_service = PaymentService(SimulatedGateway())`) and
  routers import them. Tests swap collaborators with `monkeypatch` or constructor arguments.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Full hexagonal per module: domain, application service, ports for repositories, unit of work and providers, adapters | Rules testable without a database or FastAPI; one way to add a provider; explicit module boundaries, so a module can be extracted | More files; mapping between domain types, tables and schemas; migration work |
| B. Ports only for external providers (today) | Fewer files; matches most of the code | Services depend on SQLAlchemy; rules tested only through a database; shared tables block extraction |
| C. Layered routers with the logic | Fewest files | Rules in routers and repeated per channel; hard to test; loses the BFF separation |

## Decision

Option A. Each domain module is a hexagon:

1. **Domain** at the center: entities and value objects (dataclasses), pure rules and domain errors
   ([ADR 0007](0007-backend-errors-and-responses.md)). It imports no FastAPI, Pydantic or SQLAlchemy.
2. **Application service**: the module's use cases. It depends only on its domain and on ports.
3. **Driven ports** (`typing.Protocol`): repositories, a unit of work (`commit`, `rollback`) and
   external providers (SMS, payment gateway, credit bureau, email, storage).
4. **Driving adapters**: the BFF routers ([ADR 0005](0005-backend-bff-per-channel.md)). **Driven
   adapters**: SQLAlchemy repositories ([ADR 0006](0006-backend-persistence.md)) and provider clients.
5. **Composition in one place** ([ADR 0004](0004-backend-module-layout.md)): FastAPI dependency
   functions build the adapters from settings and pass them to the services. No other code creates one.
6. **Dependencies point inward**: adapters → application service → domain.
7. **Modules are separated by domain.** A module uses another only through its application service and
   the domain types it returns, never through its adapters or tables. So a module can be extracted into
   its own service later.
8. **Tests**: domain and services are unit tests with fakes of the ports; adapters are integration tests
   against a real PostgreSQL.

## Consequences

- Easier: unit tests without a database; a new provider is a new adapter behind a port; a forbidden
  import between modules is visible in review.
- Harder: mapping code between domain types, tables and schemas; one more step when reading a use case.
- Cross-module foreign keys stay for now (`policies.quote_id`, `payment_transactions.policy_number`);
  extracting a module would replace them.
- Migration, when each module is next touched, not as a rewrite:
  - `policy` gets quotes from `rating`'s service instead of `QuoteDB`; `payments` gets a policy domain
    object from `policy`'s service instead of `PolicyDB`.
  - The payment gateway gets a Protocol. Services are built in the composition root, not at import time.
  - Queries and `commit()` move from services to repositories and the unit of work.

## Security and privacy impact

The trust boundary stays at the driving adapters: routers authenticate and authorize before any service
runs. Services apply per-resource rules and must pass the owner or tenant to every repository query that
reads scoped data. Provider credentials are read from settings only by the adapter that uses them, as
`core/sms.py` does for Twilio today; domain and services never see them. Development stand-ins that
live in `app/` (the console SMS sender, the simulated gateway) are chosen in the composition root, the
one place to check that production does not select them. Test fakes live only in `backend/tests`.
