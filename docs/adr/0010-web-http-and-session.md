# ADR 0010 · Web: HTTP through core services, one interceptor, session in core/auth

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-22 |
| Story | none |
| Deciders | The team (to be confirmed) |

## Context

Today in `web/src/app`:

- Only `core` services use `HttpClient` and return typed Observables. Six take the base URL from
  `API_BASE_URL` (default `/api/v1`), a token defined in `core/quotes/quote.service.ts`.
  `core/auth/auth.service.ts` hard-codes `/api/v1/experience/auth/login` and `/refresh`.
- `app.config.ts` registers one interceptor, `core/interceptors/jwt.interceptor.ts`. It adds
  `Authorization: Bearer` to every request except URLs containing `/auth/login` or `/auth/refresh`; it
  does not check the destination. On a 401 it refreshes once and retries once; if the refresh fails it
  signs out. Two requests that fail at the same time each start their own refresh.
- `core/guards/auth.guard.ts` refreshes silently when the access token has expired and a refresh token
  exists; otherwise it redirects to `/login` with a `returnUrl`.
- `AuthService` keeps the session in a signal and copies it to `sessionStorage`
  (`solventa_advisor_session`): access token, refresh token, role, advisor name and expiry. Sign-out
  clears both and does not call the backend: the experience BFF (`backend/app/bff/experience/router.py`)
  has login and refresh but no advisor logout, and the backend sets no cookies.
- `core/utils/http-error.ts` turns errors into messages in `client-data-step`, `consent-step` and the
  quote call in `cotizador`. `login.component.ts` (401, 423), `cotizador`'s policy issue (409) and
  `payment-step` (402) build their messages themselves.
- CloudFront serves the portal and routes `/api/*` to the backend on the same distribution
  (`terraform/modules/web_hosting/main.tf`), so the API is same-origin.

## Options considered

Where the tokens live:

| Option | Pros | Cons |
|---|---|---|
| A. Both tokens in `sessionStorage` (today) | Survives a reload; frontend only | Any script in the page can read both, including the refresh token, which lasts days |
| B. Access token in memory; refresh token in an `HttpOnly`, `Secure`, `SameSite` cookie set by the backend | Scripts cannot read the refresh token; a reload restores the session with one refresh call | Backend change on login, refresh and sign-out; CSRF protection for the cookie |
| C. Both in memory only | Nothing persisted | Every reload or new tab asks for password and TOTP again |

## Decision

1. HTTP happens only in `core` services, which return typed Observables and build URLs from
   `API_BASE_URL`, authentication included.
2. One interceptor attaches credentials, and only to requests for the API base URL. Today it attaches
   them to every request except login and refresh: a known gap.
3. On a 401 the interceptor refreshes once and retries once; if the refresh fails, the session ends.
4. `core/auth` owns the session. Only `AuthService` writes it; the rest read its read-only signal.
5. Errors become user messages only through `core/utils/http-error.ts`. Components may branch on a
   status (409 means re-quote) but do not build message text from the response.
6. Tokens: option B is the target. Today's `sessionStorage` of both tokens is a known gap. The change
   ships in its own spec together with the backend change.

## Consequences

- Easier: one place to review credentials and one to review error text.
- Harder: option B needs backend work (set, read and clear the cookie; a sign-out that revokes it) and
  coordinated tests.
- Migration when next touched: `AuthService` uses `API_BASE_URL`; the token moves out of
  `quote.service.ts` to its own file in `core/`; the interceptor checks the base URL and shares one
  refresh among concurrent 401s; login, policy issue and payment messages go through `http-error.ts`.

## Security and privacy impact

Known gaps, each tracked for its own spec:

- Both tokens and the advisor's name and role sit in `sessionStorage`, readable by any script in the
  page (an XSS or a compromised dependency). By default the refresh token lasts 7 days and the access
  token 15 minutes (`backend/app/core/config.py`).
- The interceptor would send the access token to any URL. Today every call is relative to `/api/v1`,
  so nothing leaks yet.
- Sign-out does not revoke the refresh token on the server; it stays valid until it expires.

Option B adds a cookie-authenticated refresh endpoint, which needs CSRF protection: `SameSite` plus a
token (`HttpClient` supports one with `withXsrfConfiguration`). The API is same-origin, so the cookie
does not need `SameSite=None`. `http-error.ts` shows the server's `detail` text, so the backend must
keep errors generic. `ConsentService.getConsent` puts a document number in the URL path, where access
logs can record it; no screen calls it today.
