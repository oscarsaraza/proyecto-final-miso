# Frontend rules

> Web frontend rules. Load when editing browser code. Paths: `web/**`, `frontend/**`, `**/*.tsx`, `**/*.jsx`, `**/*.vue`, `**/*.svelte`.

- The server decides; guards only hide. Never rely on client-side checks for authorization or validation.
- No `innerHTML`, `dangerouslySetInnerHTML` or framework sanitizer bypasses with untrusted data; set a CSP.
- Access tokens in memory (or `sessionStorage` with short lifetimes); refresh tokens in `HttpOnly`,
  `Secure`, `SameSite` cookies; never `localStorage` or URLs. CSRF protection when sessions use cookies.
- Interceptors attach credentials only to the application's own origins.
- Minimal third-party scripts and fonts, pinned and with integrity where possible.
- No secrets in the bundle: anything shipped to the browser is public.

Interfaces follow `ui-ux` and `accessibility` (WCAG 2.2 AA). Language skills: `code-review-typescript`
and `secure-coding-typescript`.
