# ADR 0007 · Backend: domain errors and HTTP error responses

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

[ADR 0002](0002-api-contract.md) fixes what each status code means and the `{"detail": ...}` body. This
ADR fixes how errors are raised and mapped to them. Today:

- Error classes are defined in each `service.py` (`identity`, `payments`, `policy`, `profile`), plus
  `GatewayUnavailableError` in `payments/gateway.py` and `IdempotencyConflictError` in
  `core/idempotency.py`. There is no base error per module. `auth/service.py` raises `HTTPException`
  itself, and `payments/service.py` stores HTTP statuses (200, 402) in the idempotency record.
- Routers map errors with `try`/`except` per route, with helpers in `bff/auth/router.py` (`_locked`,
  `_rate_limited`, `_sms_unavailable`) and a `PAYMENT_ERRORS` dict in `bff/experience/router.py`.
- `str(exc)` reaches the client in `bff/experience/router.py` (age check, consent, which catches any
  `ValueError`, quotes, payment decline) and `bff/quote_edge/router.py`. The age message includes the
  applicant's age. One class gets different messages per route: `InvalidTokenError` has three.
- The body is `{"detail": "<message>"}`. The insured's 423 adds `locked_until` and `retry_after` and the
  `Retry-After` header (`LockedResponse` in `identity/models.py`); 429 sends `detail` and `Retry-After`;
  the advisors' 423 sends `detail` only. Request validation returns FastAPI's 422
  (`{"detail": [{"loc", "msg", "type"}]}`); weak password and amount mismatch return 422 with a string.
- No exception handler is registered: an unexpected error returns a plain-text 500, with no correlation id.
- Clients: the web portal reads `detail` as a string or as the 422 list
  (`web/src/app/core/utils/http-error.ts`, also `login.component.ts` and `payment-step.component.ts`).
  The mobile app (`movil/.../data/auth/HttpAuthApi.kt`) reads only status codes and `Retry-After`.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. One mapping per BFF plus one global handler for unexpected errors | Routes without `try`/`except`; one place per channel for statuses; messages fixed per error | Each new error must be mapped, or it becomes a 500 |
| B. `try`/`except` in each route (today) | Mapping next to the call | Repeated; messages drift; `str(exc)` slips in; unmapped errors become plain-text 500s |
| C. RFC 9457 problem details | Standard fields | Changes the shape the web portal parses, with no gain for the mobile app; rejected for now |

## Decision

Option A.

1. Domain errors live in the module's `domain.py` and subclass the module's base error. Each class
   carries a fixed public message in Spanish. Extra data is allowed only where documented
   (`locked_until`, `retry_after`); a decline reason is chosen from a fixed list by the gateway adapter,
   never copied from the provider's text.
2. Services raise domain errors only: no `HTTPException`, no status codes.
3. Each BFF has one mapping from error class to status code in its `router.py`, applied to every route of
   that router in one place:

   ```python
   ERRORS = {InvalidCredentialsError: 401, AccountLockedError: 423, RateLimitedError: 429}
   ```

4. One response shape, `{"detail": "<public message>"}`, plus extra fields only where the route's
   `responses` declare them: 423 adds `locked_until` and `retry_after`; 423 and 429 send `Retry-After`.
5. Never `str(exc)`, exception names, SQL, provider text or stack traces in a response. Two different
   public messages mean two error classes.
6. Anything unmapped reaches one global handler in `main.py`: a generic 500 in Spanish, logged with the
   exception and a correlation id assigned per request in `core/middleware.py`, without personal data.
7. Request validation keeps FastAPI's 422 shape, which the web portal already parses.
8. Status codes are part of the contract: the mobile app depends on them.

## Consequences

- Easier: short routes; one place per channel to review statuses and messages; tests check the mapping.
- Harder: a missing mapping shows up as a 500.
- Migration, when each module or router is next touched: move errors to `domain.py`; remove
  `HTTPException` from `auth/service.py`; split `InvalidTokenError` and `InvalidCredentialsError` where
  routes use different messages; stop catching `ValueError` and `NotImplementedError` in routers;
  `payments` stores the outcome, not an HTTP status, in its idempotency record and the BFF maps it.

## Security and privacy impact

Messages do not reveal whether an account exists: identity answers unknown email, wrong password and
wrong code with the same class and message, and locks unknown emails too, so 423 and `Retry-After` reveal
nothing. The advisors' sign-in can reveal existing usernames, since only those lock (`auth/service.py`).
Fixed messages remove personal data from responses (the age today). Logs keep the correlation id and
exception, never tokens, codes or request bodies; `core/sms.py` logs Twilio's error text, which can
contain the phone number. The advisors' sign-in and the SMS log are each tracked for their own spec.
