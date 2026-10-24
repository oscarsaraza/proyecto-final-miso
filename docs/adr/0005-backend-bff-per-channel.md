# ADR 0005 · Backend: one BFF router per client channel as driving adapters

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

[ADR 0001](0001-system-separated-applications.md) gives each client channel its own BFF. This ADR fixes
what a BFF router does inside the backend. `app/main.py` mounts three under `settings.API_V1_STR`
(`/api/v1`):

| Router | Prefix | Client | Authorization today |
|---|---|---|---|
| `bff/auth/router.py` | `/api/v1/auth` | insured mobile app (`movil/.../data/auth/HttpAuthApi.kt`) | `require_roles(["insured"])` on `/devices`; the session, code and password routes are open |
| `bff/experience/router.py` | `/api/v1/experience` | advisors' web portal (`web/src/app/core/*`) | `require_roles(["advisor"])` on clients, consent, quotes, policies and payments; `/auth/*` and `/catalogs/*` have no role |
| `bff/quote_edge/router.py` | `/api/v1/quote-edge` | partners (placeholder) | only checks that an `X-Partner-Id` header is present |

Routers already call services and hold no queries; `experience` uses the services of five modules
(`auth`, `profile`, `rating`, `policy`, `payments`). But they also receive the `AsyncSession` and pass it
on, map errors with `try`/`except` per route, and import an adapter's error (`GatewayUnavailableError`
from `payments/gateway.py`). `bff/auth/router.py` reads `insured_auth_service.sms.exposes_code`, an
adapter attribute, to decide whether to return `debug_code`.

`core/middleware.py` (`TenantContextMiddleware`) copies `X-Partner-Id` into a context variable that no
application code reads; payments always use the partner `"default"`.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. One BFF router per client channel (today) | Responses shaped for each client; one role per channel; a channel's security review reads one file | Some repetition between channels |
| B. One general-purpose API for every client | One contract to maintain | Clients over-fetch or make many calls; roles mixed per route; one change affects all clients |
| C. A GraphQL gateway | Clients choose fields | New runtime and tooling; per-field authorization; harder caching and rate limiting |

## Decision

Option A. Each `bff/<channel>/router.py` is the driving adapter for one client channel
([ADR 0003](0003-backend-hexagonal-architecture.md)):

1. It adapts use cases to its client: it validates input with module schemas, calls one or more modules'
   application services, and shapes the response for that client.
2. It authenticates and authorizes with the `core/security` dependencies: the channel's role
   (`insured`, `advisor`, later the partner's) on every route except those that start, renew or end a
   session or recover access.
3. It takes the user or tenant from verified credentials (the token claims, as `claims["sub"]` in
   `/devices` today) and passes it to the service, never from the body or a plain header.
4. It maps domain errors to HTTP with one mapping ([ADR 0007](0007-backend-errors-and-responses.md)).
5. It holds no business rules, repositories, sessions or queries, and reads no adapter attribute.
   Services come from the composition root's dependency functions
   ([ADR 0004](0004-backend-module-layout.md)).
6. A new client channel gets its own `bff/<channel>/router.py`; channels do not share routes.

## Consequences

- Easier: each client gets the shape it needs; a channel's routes, roles and error mapping are in one file.
- Harder: a use case exposed to two channels has a route in each.
- Migration, when each router is next touched: stop passing `AsyncSession` to services; move the
  `debug_code` decision out of `bff/auth/router.py` into the composition root; import
  `GatewayUnavailableError` from `payments/domain.py`; give the `experience` catalog routes the advisor
  role or record why they are public.

## Security and privacy impact

Routers are the trust boundary: `require_roles` checks signature, expiry, token type and role before a
service runs. Advisor and insured tokens share one signing key and are told apart by the `role` claim, so
the per-channel role check keeps each token in its channel. Services and repositories must filter every
read of scoped data by the owner passed from the claims; another user's resource answers 404.

Known gaps, each tracked for its own spec:

- The `X-Partner-Id` header in `core/middleware.py` and `bff/quote_edge/router.py` is not proof of
  identity; the partner channel has no authentication yet.
- `client_ip` in `identity/policy.py` trusts `CF-Connecting-IP` and `X-Forwarded-For` as sent.
- `main.py` allows any CORS origin with credentials.
- Quotes, policies and consents have no owner field, so no `experience` route filters them by advisor.
- `GET /api/v1/experience/consent/{document_number}` puts a document number in the URL, where access
  logs record it.
