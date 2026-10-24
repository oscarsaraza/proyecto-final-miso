# Security and privacy assessment · {{ID}}

<!-- Proportional to the profile in spec.md. A section that does not apply is replaced by
     "N/A: <rationale>" (no table). The validator rejects N/A when a trigger requires the section.
     Write UNKNOWN when you do not know: it is not an error, but it keeps the gate at IMPLEMENTED.
     Never write secrets or real personal data in this file. -->

## 1. Data inventory and classification

<!-- Classification: PUBLIC, INTERNAL, CONFIDENTIAL (personal data) or RESTRICTED (credentials, secrets,
     special-category data, detailed financial data). Collect only what the purpose needs. -->

| ID | Data | Classification | Personal | Sensitive | Purpose |
|---|---|---|---|---|---|
| DATA-01 | <fill> | <fill> | <fill: YES or NO> | <fill: YES or NO> | <fill: why it is needed> |

## 2. Data lifecycle

<!-- One block per CONFIDENTIAL or RESTRICTED item. One block may cover several: ### DATA-01, DATA-02 · Name -->

### DATA-01 · <fill: name>

| Question | Answer |
|---|---|
| What it contains | <fill> |
| Why it is needed | <fill> |
| Who can access it | <fill> |
| Where it is captured | <fill> |
| How it is transmitted | <fill> |
| Where it is stored | <fill> |
| Copies, caches and backups | <fill> |
| How long it is kept | <fill> |
| How access is audited | <fill> |
| How it is deleted or anonymized | <fill> |
| What happens if it leaks | <fill> |
| Transfers to third parties | <fill> |

## 3. Actors and roles

| Actor | Role | Trust level | What they can do |
|---|---|---|---|
| <fill> | <fill> | <fill> | <fill> |

## 4. Trust boundaries

| Boundary | Between | What is validated when crossing it |
|---|---|---|
| <fill> | <fill> | <fill> |

## 5. Data flows

| Source | Destination | Data | Channel | Protection |
|---|---|---|---|---|
| <fill> | <fill> | <fill: DATA-NN> | <fill> | <fill: CRY-NN, CTL-NN> |

## 6. Third-party services

| Service | Use | Data shared | Location | Controls |
|---|---|---|---|---|
| <fill> | <fill> | <fill: DATA-NN> | <fill: country or region> | <fill: CTL-NN> |

## 7. Attack surface

| Surface | Exposure | Inputs the attacker controls |
|---|---|---|
| <fill: endpoint, screen, file, queue> | <fill: public, authenticated, internal> | <fill> |

## 8. Threat model

<!-- STRIDE: S spoofing, T tampering, R repudiation, I information disclosure, D denial of service,
     E elevation of privilege. Risk = likelihood (LOW, MEDIUM, HIGH) × impact (LOW, MEDIUM, HIGH, CRITICAL);
     the validator rejects a risk below the matrix. Every MEDIUM or higher threat needs an applicable control. -->

| ID | STRIDE | Asset | Threat | Actor | Likelihood | Impact | Risk | Controls |
|---|---|---|---|---|---|---|---|---|
| THR-01 | <fill> | <fill> | <fill> | <fill> | <fill> | <fill> | <fill> | <fill: CTL-NN> |

## 9. Controls

<!-- Status: EXISTING (implemented and verifiable), MISSING (required, not yet implemented: needs a task) or
     NOT APPLICABLE (with rationale). Domain: BACKEND, API, WEB, MOBILE, INFRA, DATA, CRYPTO, SECRETS or PROCESS.
     Every control that is not NOT APPLICABLE needs at least one test case. -->

| ID | Control | Domain | Status | Mitigates | Tests | Tasks | References | Rationale |
|---|---|---|---|---|---|---|---|---|
| CTL-01 | <fill> | <fill> | <fill> | <fill: THR-NN, DATA-NN> | <fill: TC-NN> | <fill: T-NN or —> | <fill: ASVS, MASVS, API Top 10, CWE> | <fill or —> |

## 10. Cryptography

<!-- One block per mechanism. Type: TLS, AT_REST, APP_LEVEL, PASSWORD_HASH, MAC, SIGNATURE, TOKENIZATION or HASH.
     Do not mix concepts: a hash is not decrypted, HMAC is not a digital signature, tokenization is not encryption. -->

### CRY-01 · <fill: name>

| Field | Value |
|---|---|
| Protects | <fill: DATA-NN> |
| Type | <fill> |
| Algorithm or service | <fill> |
| Rationale | <fill> |
| Key management | <fill> |
| Permissions | <fill> |
| Rotation | <fill> |
| Recovery | <fill> |
| Failure behavior | <fill> |
| Tests | <fill: TC-NN> |

## 11. Secrets and keys

<!-- Names, never values. -->

| Secret | Location | Access | Environments | Rotation | Revocation | Leak detection |
|---|---|---|---|---|---|---|
| <fill> | <fill> | <fill> | <fill> | <fill> | <fill> | <fill> |

## 12. Authentication, authorization and sessions

| Check | Applies | Controls | Rationale |
|---|---|---|---|
| User identification | <fill> | <fill: CTL-NN> | <fill when NO> |
| Secure authentication | <fill> | <fill> | <fill> |
| Session management | <fill> | <fill> | <fill> |
| Token expiration | <fill> | <fill> | <fill> |
| Revocation | <fill> | <fill> | <fill> |
| Server-side permission checks | <fill> | <fill> | <fill> |
| Per-resource access (ownership) | <fill> | <fill> | <fill> |
| Roles | <fill> | <fill> | <fill> |
| Privilege separation | <fill> | <fill> | <fill> |
| Brute-force protection | <fill> | <fill> | <fill> |
| Rate limiting | <fill> | <fill> | <fill> |
| One-time code (OTP) handling | <fill> | <fill> | <fill> |
| User enumeration prevention | <fill> | <fill> | <fill> |
| CSRF protection | <fill> | <fill> | <fill> |

## 13. Data isolation and multi-tenancy

<!-- If the multi-tenant trigger is NO: "N/A: <rationale>". If YES, every check needs a control and a negative
     test. A Client-Id or Partner-Id header alone does not prove isolation. -->

| Check | Applies | Controls | Tests | Rationale |
|---|---|---|---|---|
| Tenant isolation | <fill> | <fill> | <fill> | <fill> |
| Server-side authorization | <fill> | <fill> | <fill> | <fill> |
| Horizontal access | <fill> | <fill> | <fill> | <fill> |
| Vertical access | <fill> | <fill> | <fill> | <fill> |
| Resource identifiers | <fill> | <fill> | <fill> | <fill> |
| Queries and filters | <fill> | <fill> | <fill> | <fill> |
| Shared caches | <fill> | <fill> | <fill> | <fill> |
| Storage and logs | <fill> | <fill> | <fill> | <fill> |
| Negative cross-tenant tests | <fill> | <fill> | <fill> | <fill> |

## 14. Dependencies

<!-- Every new or updated dependency, and the critical ones this change relies on. Evaluation: method and date
     (e.g. "OSV.dev 2026-10-21"). Status: EVALUATED, PENDING or REJECTED. -->

| ID | Dependency | Version | Component | Use | Criticality | Evaluation | Result | Status |
|---|---|---|---|---|---|---|---|---|
| DEP-01 | <fill> | <fill> | <fill> | <fill> | <fill: CRITICAL, HIGH, MEDIUM or LOW> | <fill> | <fill> | <fill> |

## 15. Risk register and residual risk

<!-- Treatment: MITIGATE, ACCEPT, TRANSFER or AVOID. Status: OPEN, MITIGATED or ACCEPTED.
     ACCEPTED only counts with an authorized person's approval in gate.md. An AI agent never accepts risk. -->

| ID | Risk | Threats | Likelihood | Impact | Level | Treatment | Residual risk | Status |
|---|---|---|---|---|---|---|---|---|
| RISK-01 | <fill> | <fill: THR-NN> | <fill> | <fill> | <fill> | <fill> | <fill> | <fill> |

## 16. Pending decisions

| ID | Decision | Options | Recommendation | Decider | Blocks gate | Status |
|---|---|---|---|---|---|---|
| DEC-01 | <fill> | <fill> | <fill> | <fill: role of the person> | <fill: YES or NO> | <fill: PENDING, APPROVED or REJECTED> |
