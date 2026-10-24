# ADR 0002 · API contract between the backend and its clients

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

- **Prefix.** `API_V1_STR = "/api/v1"` (`backend/app/core/config.py`); `backend/app/main.py` mounts
  the three BFFs under it (ADR 0001). `/health` and `/` sit outside it.
- **Schema.** Routes declare `response_model` with Pydantic models from
  `backend/app/modules/<domain>/models.py` (`TokenPair`, `PolicyRecord`, `PaymentReceipt`…). One
  exception: `POST /experience/clients/validate` returns `Dict[str, Any]`. FastAPI serves the OpenAPI
  document at `/openapi.json`, with `/docs` and `/redoc`. JSON fields are snake_case.
- **Clients.** The web mirrors the DTOs by hand in `web/src/app/core/models/*.model.ts`, with snake_case
  fields (`auth.model.ts` maps them to a camelCase session model), and calls `/api/v1/...`. The mobile
  app's `movil/.../data/auth/HttpAuthApi.kt` calls `auth/...` relative to `BuildConfig.API_BASE_URL`
  with `HttpURLConnection` and parses with `org.json`.
- **Checks.** No tool generates clients from the schema and no test checks a client against it. Each side
  tests its own half (`backend/tests/integration`, web `*.spec.ts`, `HttpAuthApiTest.kt`).
- **Status codes in use.** 401 bad credentials or token, or a missing `X-Partner-Id`; 403 wrong role
  (`require_roles`); 404 quote, policy or consent not found; 409 expired quote, policy already paid,
  idempotency key reused, same password; 422 request validation, amount mismatch, weak password; 423
  locked account; 429 too many requests. The insured BFF sends `Retry-After` on 423 and 429; the
  advisors' 423 (`backend/app/modules/auth/service.py`) does not. Also used: 400 (ineligible client,
  invalid consent), 402 (declined payment), 501, 502 (gateway down), 503 (SMS down). Only device
  revocation filters by the token's user (`revoke_device` in `backend/app/modules/identity/service.py`),
  answering 204 whether or not the device was the caller's; quotes, policies and consents have no owner
  field yet.
- **Errors.** `HTTPException` returns `{"detail": "..."}`; FastAPI's 422 returns `detail` as a list; the
  insured 423 adds `locked_until` and `retry_after`. The web reads `detail`
  (`web/src/app/core/utils/http-error.ts`).
- **Idempotency.** `POST /api/v1/experience/payments/charge` requires `Idempotency-Key` (1–128
  characters). The web sends it (`web/src/app/core/payments/payment.service.ts`) and CloudFront forwards
  it (`terraform/modules/web_hosting/main.tf`). Policy issuance is idempotent per quote, without a header.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Hand-mirrored DTOs from the OpenAPI document | Matches the code; no new tooling; about twenty endpoints | Drift shows only in tests or at runtime; three hand-written copies |
| B. Clients generated from OpenAPI | Client types always match the schema | A generator in npm and Gradle, generated code to review, a stricter schema; needs dependency review and its own ADR |
| C. GraphQL | Clients pick their fields; one endpoint | New server and client libraries; rewrite of every router and both clients; no current need |

## Decision

Option A. Option B, through its own ADR, when the team adopts a generator.

1. REST with JSON bodies under `/api/v<N>/<channel>/`, snake_case field names.
2. The backend's Pydantic models and FastAPI's OpenAPI document are the source of truth. Every route
   declares a named `response_model`.
3. Clients mirror the DTOs by hand: the web in `web/src/app/core/models/<area>.model.ts`, the mobile app
   in its `data` layer. Each maps them to its own UI or domain types.
4. A contract change updates the backend schema, both clients that use it and their tests in the same
   story. A new request header is also added to CloudFront's forwarded headers.
5. Status codes: 401 not authenticated; 403 authenticated but the role does not allow it; 404 not found
   or out of the caller's scope; 409 conflict with the current state; 422 invalid request; 423 account
   locked, with `Retry-After`; 429 rate limited, with `Retry-After`. The other codes in use keep their
   meaning; ADR 0007 fixes the full error mapping.
6. Error body `{"detail": ...}`; fields may be added next to `detail`. Details in ADR 0007.
7. Writes that clients retry and must not repeat carry an `Idempotency-Key`: the same key and body
   return the first response; the same key with another body returns 409.
8. Additive changes (new endpoint, new optional field) stay in the current version; clients ignore
   unknown fields. Breaking changes (removed or renamed field, new type or meaning, new required field,
   different status code) go to a new prefix, served next to the old one until both clients move.

## Consequences

- Easier: one place to read the contract; one merge request shows backend and clients together.
- Harder: nothing checks a client against the schema automatically.
- When next touched: `POST /experience/clients/validate` gets a named response model; the advisors'
  423 gets `Retry-After`.

## Security and privacy impact

- 404 for out-of-scope resources does not confirm that another owner's resource exists, and
  `Idempotency-Key` keeps a retried charge from charging twice.
- Most error details are fixed messages; a few routes in `backend/app/bff/experience/router.py` return
  exception text (`str(exc)`). ADR 0007 covers it.
- `OtpResponse.debug_code` is part of the schema; the backend fills it only with the console SMS adapter
  outside production (`backend/app/bff/auth/router.py`; see ADR 0019).
- Known gaps, each tracked for its own spec: `/docs`, `/redoc` and `/openapi.json` are always enabled
  (`backend/app/main.py`) and reachable on the internet-facing load balancer; CORS allows any origin with
  credentials (`backend/app/main.py`); CloudFront replaces 403 and 404 with `/index.html` and status 200
  for the whole distribution, `/api/*` included (`terraform/modules/web_hosting/main.tf`).
