# Backend and API rules

> Backend and API rules. Load when editing server code. Paths: `backend/**`, `server/**`, `api/**`, `services/**`.

Adapt the stack-specific lines to the project; keep the security lines.

- Every route authenticates and authorizes on the server, per function and per resource (owner or tenant
  is a parameter of every query that reads scoped data). Out-of-scope resources answer 404.
- Validate every input with explicit types, lengths, formats and ranges — including emails, headers and
  identifiers — before touching the database or a third party. Unbounded input is a denial-of-service.
- Parameterized queries only; no SQL built from strings. No outbound requests to client-controlled URLs.
- Rate limits and costs per user, per trusted client IP (from a trusted proxy list, never raw headers) and per sensitive flow.
- Errors are generic for the client; details go to logs without personal data or secrets.
- Side effects on third parties (payments, SMS, email) happen in a way that leaves no partial state if the
  transaction fails; idempotency keys for operations that can be retried.
- Configuration is secure by default: no default keys or passwords, no debug or test data outside
  development, documentation endpoints off in production, CORS restricted to known origins.
- Mutating routes and routes that read personal data emit an audit event without the data itself.

Language skills: `code-review-python` and `secure-coding-python`.
