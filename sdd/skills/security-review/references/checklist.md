# Review checklist

Identifiers are verified in `sdd/security/references.md`.

## Vulnerability classes

| Class | Look for | References |
|---|---|---|
| Broken access control | Missing per-resource checks, IDOR/BOLA, function-level gaps, 403 that reveals existence | A01:2025, API1:2023, API5:2023, CWE-639, CWE-862 |
| Authentication failures | Weak password storage, missing lockout or rate limits, enumeration by message or timing, OTP in responses or logs, tokens that survive password changes | A07:2025, API2:2023, CWE-307, CWE-204, CWE-208, CWE-613, CWE-640 |
| Cryptographic failures | Plaintext transport hops, default or shared keys, key reuse across purposes, weak or custom algorithms, unauthenticated encryption | A04:2025, CWE-319, CWE-321, CWE-327, CWE-798 |
| Injection | String-built SQL/NoSQL/OS commands, template injection, XSS sinks | A05:2025, CWE-89, CWE-78, CWE-79 |
| Security misconfiguration | Debug or development defaults in production, open CORS with credentials, exposed docs, missing security headers, permissive IAM or security groups | A02:2025, API8:2023, CWE-1188 |
| Supply chain | Unpinned or unevaluated dependencies, unmaintained packages, actions pinned by tag, unverified image bases | A03:2025, CWE-1104, CWE-494 |
| Integrity failures | Unsigned updates, deserialization of untrusted data, CI that runs untrusted input | A08:2025, CWE-502 |
| Logging and alerting | Secrets or personal data in logs; no audit of security events; no retention | A09:2025, CWE-532, CWE-778 |
| Exceptional conditions | 500s that roll back counters, partial side effects (SMS sent, payment charged) when a transaction fails, fail-open checks | A10:2025, CWE-755 |
| Resource consumption | Unbounded inputs, missing pagination, costly flows without limits (SMS, email) | API4:2023, API6:2023, CWE-770 |
| SSRF | Outbound requests to client-controlled URLs | API7:2023, CWE-918 |
| Unsafe consumption | Trusting third-party responses, missing timeouts | API10:2023 |

## Mobile (MASVS 2.1)

STORAGE-1/2 (keystore, no plaintext preferences, backups, saved state), CRYPTO-1/2 (algorithms, keys per
purpose and account), AUTH-1/2/3 (server-side auth, biometric binding with a crypto object), NETWORK-1/2
(HTTPS per build type, pinning), PLATFORM-1/3 (exported components, `FLAG_SECURE`), CODE-1/3/4 (platform
version, dependencies, input validation), RESILIENCE (debuggable or unminified release builds).

## Blind spots

- **Cross-tenant and horizontal access** through any identifier the client sends.
- **Client-supplied identity**: `X-Forwarded-For`, `CF-Connecting-IP`, tenant or partner headers trusted
  without a trusted-proxy list or a credential.
- **Business logic**: skipping steps, replaying one-time artifacts, amounts or prices from the client.
- **Races** on value-bearing operations (payments, codes, counters, unique records).
- **Alternate routes** to the same handler without the guard (old versions, admin routes, direct origin access bypassing the CDN).
- **Defaults that reach production**: environment flags that default to development, test accounts
  loaded by default, debug data in responses.
- **Session invalidation**: access tokens that survive logout or a password reset.
