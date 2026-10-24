# Control catalog

Starting point for the controls table in `security.md`. Take what the feature needs; record as NOT
APPLICABLE what a reviewer might expect but does not apply. How to build each control, with code, is in
the `secure-coding-python`, `secure-coding-typescript`, `secure-coding-kotlin` and
`secure-coding-terraform` skills. Identifiers are verified in
[references.md](references.md): ASVS 5.0.0 chapters, MASVS 2.1.0 controls, API Security Top 10 2023,
Top 10:2025 and CWE.

## Backend and APIs

| Control | References |
|---|---|
| Server-side validation of every input: types, maximum lengths, formats, ranges, including headers and identifiers | ASVS V1, V2 · CWE-20 |
| Authorization on every endpoint, per function and per object: the resource belongs to the caller | ASVS V8 · API1:2023, API5:2023 · A01:2025 · CWE-639, CWE-862 |
| Responses expose only the properties the client needs | API3:2023 · CWE-213 |
| Parameterized queries; no SQL built from strings | ASVS V1 · A05:2025 · CWE-89 |
| No outbound requests to client-controlled URLs, or an allow-list | API7:2023 · CWE-918 |
| Size, rate and cost limits per user, per trusted client IP and per sensitive flow | API4:2023, API6:2023 · CWE-770 |
| Generic errors for clients; details only in logs without personal data | ASVS V16 · A10:2025 · CWE-209, CWE-532 |
| No partial external side effects (payments, SMS) when the transaction fails | A10:2025 · CWE-460 |
| Third-party calls with timeouts, without trusting the response, with credentials from the secrets manager | API10:2023 · CWE-20 |
| Endpoint inventory; interactive documentation disabled in production | API9:2023 · ASVS V13 |
| Secure defaults: no default keys or passwords, no development mode or test data outside development | ASVS V13 · A02:2025 · CWE-798, CWE-1188 |

## Authentication, sessions and one-time codes

| Control | References |
|---|---|
| Passwords hashed with Argon2id (or legacy bcrypt with the 72-byte limit), minimum length and a blocklist | ASVS V6 · NIST SP 800-63B Rev. 4 · CWE-916, CWE-521 |
| Uniform responses and timing so account existence is not revealed | ASVS V6 · CWE-204, CWE-208 |
| Progressive lockout and attempt limits per account and per origin, computed in shared storage | ASVS V6 · API2:2023 · CWE-307 |
| One-time codes: cryptographically random, single use, short expiry, limited attempts, stored with a keyed MAC | ASVS V6 · NIST SP 800-63B Rev. 4 · CWE-330, CWE-640 |
| One-time codes never in HTTP responses or logs outside local development | CWE-200, CWE-532 |
| Tokens signed with a key from the secrets manager, a fixed algorithm, short expiry, audience and issuer when there are several consumers | ASVS V9 · CWE-347, CWE-798 |
| Revocation: rotated refresh tokens; access tokens invalidated on password change (token version) | ASVS V7 · CWE-613 |
| Roles verified on the server, never only in the client | ASVS V8 · CWE-602 |
| CSRF protection when sessions travel in cookies | ASVS V3 · CWE-352 |
| Client IP only from a trusted proxy list, never from client headers | CWE-348, CWE-290 |

## Mobile

| Control | References |
|---|---|
| Credentials in the platform keystore: non-exportable, user authentication, bound to the biometric prompt with a crypto object, invalidated on enrollment | MASVS-STORAGE-1, MASVS-CRYPTO-2, MASVS-AUTH-2 |
| One key per purpose, and per account when accounts share a device | MASVS-CRYPTO-2 |
| Nothing sensitive in plain preferences, saved UI state or logs | MASVS-STORAGE-1, MASVS-STORAGE-2 |
| Backups and device-to-device transfer exclude sensitive storage | MASVS-STORAGE-2 |
| Screenshot protection on screens with passwords, codes or personal data | MASVS-PLATFORM-3 |
| HTTPS only outside development, per build type; pinning when justified | MASVS-NETWORK-1, MASVS-NETWORK-2 |
| Release builds minified, not debuggable, signed, without server debug information | MASVS-RESILIENCE-2, MASVS-RESILIENCE-3, MASVS-RESILIENCE-4 · CWE-489 |
| Minimal exported components | MASVS-PLATFORM-1 |
| Device loss: local credentials need biometrics on every use and can be revoked on the server | MASVS-AUTH-2, MASVS-AUTH-3 |
| Device integrity checks when the risk justifies them | MASVS-RESILIENCE-1 |
| Dependencies without known vulnerabilities | MASVS-CODE-3 |

## Web frontend

| Control | References |
|---|---|
| No unsafe HTML sinks with untrusted data; a Content Security Policy | ASVS V3 · CWE-79 |
| Tokens in memory or short-lived session storage; never `localStorage` or URLs | ASVS V3, V7 · CWE-922 |
| Cookies, when used: `Secure`, `HttpOnly`, `SameSite` | ASVS V3 · CWE-614, CWE-1004 |
| Interceptors attach credentials only to own origins | CWE-201 |
| Every validation repeated on the server | CWE-602 |
| Minimal, pinned third-party scripts and fonts | A03:2025 · CWE-829 |

## Infrastructure and pipelines

| Control | References |
|---|---|
| HTTPS end to end (CDN and load balancer with certificates and redirects); origin reachable only from the CDN | ASVS V12 · A04:2025 · CWE-319 |
| Secrets in a secrets manager injected as secrets; never variables, Terraform defaults or state | ASVS V13 · CWE-798, CWE-522 |
| Least-privilege IAM for workloads and deploys; OIDC instead of static CI keys | A01:2025 · CWE-250 |
| Restricted egress; private databases | CWE-284 |
| Encryption at rest with KMS and rotation; backups with retention and deletion protection | ASVS V14 · CWE-311 |
| Log retention defined; no personal data or secrets in logs | ASVS V16 · CWE-532 |
| CI actions pinned by SHA, minimal `permissions`, approval for deploy and destroy | A03:2025, A08:2025 · CWE-494 |
| Pinned base images, non-root user, no baked-in secrets | A03:2025 · CWE-250 |
| Secret and dependency scanning on every merge request | A03:2025 · CWE-1104 |

## Multi-tenancy

| Control | References |
|---|---|
| The tenant comes from an authenticated credential, never from a header the client writes | API1:2023 · CWE-639 |
| Every query filters by tenant on the server | ASVS V8 · CWE-566 |
| Caches, queues, files and logs separated or labeled by tenant | CWE-200 |
| Negative tests: one tenant cannot read or modify another's resources | — |

A `Client-Id` or `X-Partner-Id` header alone does not prove isolation.
