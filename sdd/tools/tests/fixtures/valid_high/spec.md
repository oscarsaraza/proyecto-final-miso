# HU-FIX-01 · View own policies

| Field | Value |
|---|---|
| ID | HU-FIX-01 |
| Title | View own policies |
| User story | none (fictitious scenario for the validator tests) |
| Owner | Owner Person |
| Status | IN_REVIEW |
| Created | 2026-10-20 |
| Security profile | HIGH |

## 1. Requirements

### User story

**HU-FIX-01 · Ver mis pólizas.** Como asegurado quiero ver mis pólizas vigentes para conocer mi cobertura.
Criterio de la historia: el asegurado ve solo sus pólizas.

### Problem and outcome

The insured needs to see their active policies through the API.

### Goals and non-goals

Read-only access to the authenticated holder's policies. No payments and no editing.

### Affected paths

| Path | Change |
|---|---|
| backend/app/modules/policy/query.py | New query endpoint |

### Use cases

| ID | Actor | Use case | Main flow | Alternate flows |
|---|---|---|---|---|
| UC-01 | Insured | List my policies | 1. Signs in. 2. Requests the list. 3. Receives their policies | No policies: empty list |

### Abuse cases

| ID | Abuse case | Actor | Threat | Expected response | Test case |
|---|---|---|---|---|---|
| AB-01 | Change the policy number to read another insured's policy | Malicious insured | THR-01 | 404 with no data | TC-02 |

### Acceptance criteria

| ID | Criterion | Source |
|---|---|---|
| AC-01 | WHEN an authenticated insured requests their policies, THE API SHALL return only the policies they own | STATED |
| AC-02 | IF the policy number is malformed, THE API SHALL answer 422 with a generic message | DERIVED: the story does not say how invalid input is answered |

### Quality requirements

| ID | Category | Requirement | Target and conditions |
|---|---|---|---|
| QR-01 | PERFORMANCE | Listing policies stays responsive at the expected peak | p95 under 300 ms and under 1% errors at 20 requests/s for 5 minutes in the test environment |

### Security triggers

| Trigger | Applies | Rationale |
|---|---|---|
| Personal data (identifies or can identify a person) | YES | A policy identifies its holder |
| Sensitive data (special categories, biometrics, health, financial, minors) | NO | No health or detailed financial data is exposed |
| Authentication, sessions, credentials or one-time codes | NO | Reuses the existing authentication unchanged |
| Authorization or access to other users' resources | YES | Each insured must only see their own policies |
| Payments or money movement | NO | Read-only |
| Third-party services or integrations | NO | No external calls |
| Infrastructure, network, IAM, CI/CD or secrets | NO | No infrastructure change |
| Multiple tenants, partners or organizations | NO | Single insured channel |
| Storage or processing on a mobile device | NO | API only |
| Web UI or data exposed in the browser | NO | API only |
| New or updated dependencies | NO | No dependency change |
| Critical paths (sdd/security/critical-paths.md) | NO | The path is not in the registry |

### Security requirements

| ID | Requirement | Source | Controls | Priority |
|---|---|---|---|---|
| SR-01 | Only the holder can read their policies | DATA-01, THR-01 | CTL-01, CTL-02 | HIGH |
| SR-02 | Errors and logs do not expose personal data | DATA-01, THR-02 | CTL-03 | MEDIUM |
| SR-03 | Only valid, unexpired tokens are accepted, over encrypted transport | DATA-02, THR-03 | CTL-04 | HIGH |

## 2. Design

### Components

Query router and policy service in backend/app/modules/policy.

### Data flows

Insured app → API (TLS) → service → PostgreSQL. The trust boundary is the API.

### Data contract

GET /policies returns 200 with a list of {number, plan, valid_until}; 401 without a valid token.

### Security design decisions

| Decision | Implements | Rejected alternative and why |
|---|---|---|
| The query filters by the token subject | CTL-01 | Filtering on the client: not trustworthy |
| Another holder's resource answers 404 | CTL-02 | 403: reveals that it exists |
| Transport over TLS 1.2 or higher | CRY-01 | None |

### Architecture decisions

N/A: no architectural decision is introduced by this change.

### Configuration and deployment

No new variables.

## 3. Tasks

| ID | Task | Traces to | Controls | Status | Evidence |
|---|---|---|---|---|---|
| T-01 | Query endpoint filtered by holder | AC-01, SR-01 | CTL-01, CTL-02 | DONE | tests/test_policies.py::test_other_user_gets_404 |
| T-02 | Generic errors and logs without personal data | SR-02 | CTL-03 | DONE | commit 1a2b3c4 |
