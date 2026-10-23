# Security and privacy assessment · HU-FIX-01

## 1. Data inventory and classification

| ID | Data | Classification | Personal | Sensitive | Purpose |
|---|---|---|---|---|---|
| DATA-01 | Policy number and coverage | CONFIDENTIAL | YES | NO | Show the holder their policies |
| DATA-02 | Access token | RESTRICTED | NO | NO | Authenticate the request |

## 2. Data lifecycle

### DATA-01 · Policy

| Question | Answer |
|---|---|
| What it contains | Number, plan, validity and coverage |
| Why it is needed | So the holder knows their coverage |
| Who can access it | The holder and the backend |
| Where it is captured | At issuance, outside this change |
| How it is transmitted | HTTPS with TLS 1.2 or higher |
| Where it is stored | PostgreSQL encrypted at rest |
| Copies, caches and backups | Database backups; no client cache |
| How long it is kept | As defined by the policy retention schedule |
| How access is audited | Access log without personal data |
| How it is deleted or anonymized | Per the retention schedule |
| What happens if it leaks | Incident plan and report to the authority |
| Transfers to third parties | Not transferred |

### DATA-02 · Token

| Question | Answer |
|---|---|
| What it contains | Holder identifier and expiry |
| Why it is needed | Authenticate every request |
| Who can access it | The client and the backend |
| Where it is captured | At sign-in |
| How it is transmitted | Authorization header over TLS |
| Where it is stored | Client memory |
| Copies, caches and backups | None |
| How long it is kept | 15 minutes |
| How access is audited | The token is never logged |
| How it is deleted or anonymized | It expires |
| What happens if it leaks | The signing key is rotated |
| Transfers to third parties | Not transferred |

## 3. Actors and roles

| Actor | Role | Trust level | What they can do |
|---|---|---|---|
| Insured | insured | Authenticated | Read their own policies |

## 4. Trust boundaries

| Boundary | Between | What is validated when crossing it |
|---|---|---|
| API | Client and backend | Token signature and expiry, resource ownership |

## 5. Data flows

| Source | Destination | Data | Channel | Protection |
|---|---|---|---|---|
| App | API | DATA-02 | HTTPS | CRY-01 |
| API | App | DATA-01 | HTTPS | CRY-01, CTL-01 |

## 6. Third-party services

N/A: the feature does not call external services.

## 7. Attack surface

| Surface | Exposure | Inputs the attacker controls |
|---|---|---|
| GET /policies/{number} | Authenticated | Policy number and token |

## 8. Threat model

| ID | STRIDE | Asset | Threat | Actor | Likelihood | Impact | Risk | Controls |
|---|---|---|---|---|---|---|---|---|
| THR-01 | I, E | DATA-01 | Read another insured's policy by changing the number | Malicious insured | MEDIUM | HIGH | HIGH | CTL-01, CTL-02 |
| THR-02 | I | DATA-01 | Personal data in error messages or logs | External attacker | LOW | MEDIUM | LOW | CTL-03 |
| THR-03 | S | DATA-02 | Reuse an expired or tampered token | External attacker | LOW | HIGH | MEDIUM | CTL-04 |

## 9. Controls

| ID | Control | Domain | Status | Mitigates | Tests | Tasks | References | Rationale |
|---|---|---|---|---|---|---|---|---|
| CTL-01 | The query filters by the token holder | BACKEND | EXISTING | THR-01 | TC-02 | T-01 | API1:2023, CWE-639 | — |
| CTL-02 | Another holder's resource answers 404 | API | EXISTING | THR-01 | TC-02 | T-01 | ASVS 5.0 V8 | — |
| CTL-03 | Generic errors and logs without personal data | BACKEND | EXISTING | THR-02 | TC-03 | T-02 | CWE-209, CWE-532 | — |
| CTL-04 | Token signature and expiry verified in the backend | API | EXISTING | THR-03 | TC-04, TC-05 | — | ASVS 5.0 V9 | — |
| CTL-05 | Tenant isolation | DATA | NOT APPLICABLE | — | — | — | — | Single channel, no tenants exist |

## 10. Cryptography

### CRY-01 · Transport

| Field | Value |
|---|---|
| Protects | DATA-01, DATA-02 |
| Type | TLS |
| Algorithm or service | TLS 1.2 or higher at the load balancer |
| Rationale | Protects the request on untrusted networks |
| Key management | Certificate managed by the cloud provider |
| Permissions | Infrastructure team only |
| Rotation | Automatic for the managed certificate |
| Recovery | Certificate reissue |
| Failure behavior | The client refuses the connection |
| Tests | TC-05 |

### CRY-02 · Token signature

| Field | Value |
|---|---|
| Protects | DATA-02 |
| Type | MAC |
| Algorithm or service | HMAC-SHA256 (HS256) |
| Rationale | Integrity and authenticity of a token the same backend issues |
| Key management | Key in the environment's secrets manager |
| Permissions | Backend execution role only |
| Rotation | Every 90 days or on suspected leak |
| Recovery | New key; sessions sign in again |
| Failure behavior | Invalid token: 401 |
| Tests | TC-04 |

## 11. Secrets and keys

N/A: the change creates or uses no new secrets; the signing key is the existing one.

## 12. Authentication, authorization and sessions

| Check | Applies | Controls | Rationale |
|---|---|---|---|
| User identification | YES | CTL-04 | — |
| Secure authentication | NO | — | Authentication is unchanged |
| Session management | NO | — | Sessions are unchanged |
| Token expiration | YES | CTL-04 | — |
| Revocation | NO | — | Revocation is unchanged |
| Server-side permission checks | YES | CTL-01 | — |
| Per-resource access (ownership) | YES | CTL-01, CTL-02 | — |
| Roles | YES | CTL-04 | — |
| Privilege separation | NO | — | A single role |
| Brute-force protection | NO | — | No credentials in this flow |
| Rate limiting | NO | — | Unchanged; covered by the global limit |
| One-time code (OTP) handling | NO | — | No one-time codes |
| User enumeration prevention | NO | — | Takes no user identifiers |
| CSRF protection | NO | — | Token in a header, no cookies |

## 13. Data isolation and multi-tenancy

N/A: there are no clients, partners or organizations in this channel.

## 14. Dependencies

| ID | Dependency | Version | Component | Use | Criticality | Evaluation | Result | Status |
|---|---|---|---|---|---|---|---|---|
| DEP-01 | fastapi | 0.142.2 | backend | Router | HIGH | OSV.dev 2026-10-20 | No known vulnerabilities | EVALUATED |

## 15. Risk register and residual risk

| ID | Risk | Threats | Likelihood | Impact | Level | Treatment | Residual risk | Status |
|---|---|---|---|---|---|---|---|---|
| RISK-01 | Infer which policies exist from response timing | THR-01 | LOW | LOW | LOW | MITIGATE | Low: uniform 404 | MITIGATED |

## 16. Pending decisions

N/A: no pending decisions.
