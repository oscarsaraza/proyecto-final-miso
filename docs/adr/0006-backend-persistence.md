# ADR 0006 · Backend: persistence with async SQLAlchemy behind repository ports

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

- `core/database.py` creates one async engine (asyncpg, `pool_size=10`, `max_overflow=20`) and a session
  factory (`expire_on_commit=False`, `autoflush=False`). `get_db_session` yields one session per request
  and closes it; it never commits, so closing discards uncommitted work.
- Services receive that session, query it and call `commit()` themselves, sometimes several times in one
  use case. Some flows commit on purpose before rejecting: `identity/service.py` records the failed
  attempt and the lock and commits in `_register_failure` before `login` raises, and audits and commits in
  `_reject_if_locked`; `auth/service.py` commits `failed_attempts` before raising. `request_otp` rolls
  back when the SMS fails.
- PostgreSQL features in use: `insert(...).on_conflict_do_nothing()` (`identity/service.py`,
  `policy/service.py`, with `RETURNING`), `with_for_update()` (`identity/service.py` on accounts, locks and
  codes; `policy_service.lock()` for payments), `JSONB` (`core/idempotency.py`) and sequences
  (`policy_number_seq`, `receipt_number_seq`).
- The schema comes from `Base.metadata.create_all` in the lifespan of `main.py`, which creates missing
  tables and never alters existing ones; a failure is printed and startup continues. There is no
  migration tool in `pyproject.toml`.
- `core` owns two shared tables: `idempotency_records` (stored response per partner and key) and
  `outbox` (events written in the same transaction by `policy` and `payments`; nothing publishes them yet).
- Consents are kept in a dict in `ProfileService` (`profile/service.py`), not in PostgreSQL.
- Tests: `postgres_session` in `tests/conftest.py` recreates the tables in a `solventa_test` database;
  other tests use `InMemorySessionTestDouble`, which imitates a session by matching SQL text.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Repositories per aggregate behind ports; the service commits through a unit-of-work port | Services testable with fakes; transaction and lock boundaries named; data access per module in one file | Mapping between rows and domain types; more code |
| B. Services use `AsyncSession` directly (today) | Least code | Services tied to SQLAlchemy; fakes must imitate SQL; locks and commits scattered |
| C. Generic repository (`get`, `add`, `list`) for every table | Less code per module | Hides intent (locks, upserts); leaks query building into services |

## Decision

Option A.

1. Repositories per aggregate in `adapters.py` implement the module's ports and receive the request's
   session. They return domain objects, never table rows, and never commit.
2. The application service decides when to commit through the `UnitOfWork` port (`commit`, `rollback`)
   from `core/database.py`. One commit at the end of a use case is the default; a flow that must persist
   before rejecting (recording a failed sign-in and the lock) commits first, then raises.
3. Locks are repository methods named for their intent, such as `lock_for_charge(policy_number)`, not
   a `for_update` flag. A lock lasts until the unit of work commits or rolls back.
4. Idempotency and outbox stay in `core` as shared adapters and join the caller's session and commit.
5. PostgreSQL 16 is the only database. Repositories may use its features; there is no portability promise.
6. The composition root builds the repositories and the unit of work on the same request session.
7. Repositories are tested against real PostgreSQL; services are tested with fakes of the ports.
8. Adopting a migration tool is a separate ADR, required before the first schema change on data that
   must be preserved.

## Consequences

- Easier: services tested without a database or a fake session; lock and commit points visible by name.
- Harder: mapping code; a schema change on existing data is blocked until the migration ADR exists.
- Migration, when each module is next touched: queries move to repositories and `commit()` to the unit of
  work; `InMemorySessionTestDouble` goes once no test uses it. Persisting consents is a separate story.

## Security and privacy impact

Repositories are where per-resource filtering lives: a method that reads scoped data takes the owner or
tenant as a parameter (as `revoke_device` filters by `user_id` today) and returns nothing for others.
Queries are SQLAlchemy expressions only, never SQL built from strings. Security records (failed
attempts, locks, revoked tokens, audit rows) must still commit when a request is rejected; the tests in
`tests/unit/test_insured_auth.py` cover it. The `PolicyIssued` outbox payload copies the insured's
document number, so outbox rows need the same retention as the policy. That retention, and the default
values for the database URL and signing key in `core/config.py`, are each tracked for their own spec.
