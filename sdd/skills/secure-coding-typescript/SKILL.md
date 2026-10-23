---
name: secure-coding-typescript
description: Secure coding patterns for TypeScript and Angular in the browser — output encoding and sanitizer bypasses, open redirects, token storage, interceptors limited to the own API, CSRF, Content Security Policy, secrets in the bundle, data in URLs, randomness and third-party code. Use when writing or reviewing web frontend code.
---

# Secure coding — TypeScript and Angular

Everything shipped to the browser is public and can be modified by the user: the server decides,
the client only presents. Each pattern names the weakness it prevents (CWE) and the test that proves it.

## Output encoding (CWE-79)

Angular escapes interpolation and sanitizes `[innerHTML]`, `[src]` and `[href]` by default. Keep it that way.

- Prefer `{{ value }}`; use `[innerHTML]` only for content the application controls.
- Never call `DomSanitizer.bypassSecurityTrust*` with data that came from a user or an API.
- Never write to `nativeElement.innerHTML`, use `document.write`, `eval` or `new Function`.

Test: a value with `<img src=x onerror=…>` renders as text.

## Redirects after sign-in (CWE-601)

```ts
export function safeReturnUrl(value: string | null): string {
  if (!value || !value.startsWith('/') || value.startsWith('//') || value.startsWith('/\\')) {
    return '/';
  }
  return value;
}
```

Test: `returnUrl=https://evil.example` and `returnUrl=//evil.example` land on `/`.

## Credentials only to the own API (CWE-201)

```ts
function isOwnApi(url: string, apiBase: string): boolean {
  const target = new URL(url, window.location.origin);
  const api = new URL(apiBase, window.location.origin);
  return target.origin === api.origin && target.pathname.startsWith(api.pathname);
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).accessToken();
  if (!token || !isOwnApi(req.url, inject(API_BASE_URL))) {
    return next(req);
  }
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
```

Test: a request to another origin carries no `Authorization` header.

## Token storage (CWE-922)

- Access token in memory (a signal in the auth service), short-lived.
- Refresh token in an `HttpOnly`, `Secure`, `SameSite` cookie set by the server, sent only to the refresh
  endpoint. With cookies, enable CSRF protection (`withXsrfConfiguration`) and validate it on the server (CWE-352).
- Never `localStorage`, never in URLs. `sessionStorage` is a documented, accepted risk at most: any
  script injected into the page can read it.
- Sign-out clears memory and storage and revokes the refresh token on the server.

## Content Security Policy and headers (CWE-1021, CWE-693)

Set at the hosting layer (CDN or server), not in the app:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'nonce-…';
  connect-src 'self'; img-src 'self' data:; font-src 'self'; object-src 'none'; base-uri 'self';
  frame-ancestors 'none'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

Angular adds component styles at runtime: give them a nonce (`ngCspNonce` attribute or the `CSP_NONCE`
token) instead of `'unsafe-inline'`. Self-host fonts or allow their exact origins.

## Secrets and configuration (CWE-798, CWE-540)

No API keys, signing keys or credentials in the code, the environment files or the bundle. Runtime
configuration served to the browser is public by definition.

## Data in URLs and logs (CWE-598, CWE-532)

No personal data, tokens or codes in paths or query strings: they end up in history, CDN logs and
referrers. No `console.log` of responses or forms in production code.

## Randomness (CWE-338)

`crypto.randomUUID()` or `crypto.getRandomValues()` for idempotency keys and nonces; never `Math.random()`.

## Third-party code (CWE-829)

Dependencies pinned through the lockfile and installed with `npm ci`; new packages evaluated with
`dependency-review`. No scripts from CDNs; when unavoidable, pinned with Subresource Integrity.

## Client checks are not controls (CWE-602)

Guards, hidden buttons and form validators improve the experience; the server repeats every check.
Never send prices, roles or permissions from the client as facts.

## Review checklist

- [ ] No sanitizer bypass, `innerHTML` with external data, `eval` or `document.write`.
- [ ] Redirect targets validated as internal paths.
- [ ] Interceptor attaches credentials only to the own API.
- [ ] Tokens not in `localStorage` or URLs; sign-out clears and revokes.
- [ ] CSP and security headers configured at the hosting layer.
- [ ] No secrets in the code or bundle; no personal data in URLs or console logs.
- [ ] Secure randomness; third-party code pinned and evaluated.
- [ ] Every client-side check repeated on the server.
