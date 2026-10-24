# Test cases · HU-FIX-01

## Scenarios

| ID | From | Scenario | Disposition |
|---|---|---|---|
| SC-01 | UC-01 | Given an insured with two policies, when they list them, then both appear and nothing else | TC-01 |
| SC-02 | UC-01 | Given an insured who changes the number to another holder's policy, when they request it, then 404 with no data | TC-02 |
| SC-03 | UC-01 | Given a malformed policy number, when it is requested, then 422 with a generic message | TC-03 |
| SC-04 | AC-01 | Given 20 requests per second for 5 minutes, when insured list policies, then p95 stays under 300 ms | TC-06 |
| SC-05 | UC-01 | Given an expired session, when the insured lists policies, then 401 and the app asks to sign in again | TC-04 |
| SC-06 | UC-01 | Given a policy cancelled today, when the holder lists policies, then it appears as cancelled with its date | OUT OF SCOPE: cancelled policies are shown by the cancellation story, not by this one |

## Scenario coverage

| Kind | Applies | Scenarios | Rationale |
|---|---|---|---|
| Main flow | YES | SC-01 | — |
| Alternate flows | YES | SC-06 | — |
| Invalid input and errors | YES | SC-03 | — |
| Limits and boundaries | YES | SC-04 | — |
| Related flows before and after | NO | — | Read-only listing; sign-in and sign-out are unchanged and belong to their own stories |
| Several users, sessions, devices or roles | YES | SC-02 | — |
| State and time (expiry, retries, interruptions, going back, offline) | YES | SC-05 | — |

## Test cases

### TC-01 · The holder lists their policies

| Field | Value |
|---|---|
| Covers | AC-01 |
| Kind | FUNCTIONAL |
| Risk covered | — |
| Level | INTEGRATION |
| Preconditions | One fictitious insured with two policies |
| Procedure | 1. Sign in. 2. Request the list |
| Expected result | 200 with both policies |
| Tool or method | pytest tests/test_policies.py::test_owner_lists_policies |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | tests/test_policies.py::test_owner_lists_policies in the CI run |
| Status | PASS |

### TC-02 · Another insured's policy

| Field | Value |
|---|---|
| Covers | SR-01 |
| Kind | SECURITY |
| Risk covered | THR-01 |
| Level | INTEGRATION |
| Preconditions | Two fictitious insureds with one policy each |
| Procedure | 1. Insured A requests B's policy. 2. Inspect the response |
| Expected result | 404 with no policy data |
| Tool or method | pytest tests/test_policies.py::test_other_user_gets_404 |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | tests/test_policies.py::test_other_user_gets_404 in the CI run |
| Status | PASS |

### TC-03 · Errors without personal data

| Field | Value |
|---|---|
| Covers | AC-02, SR-02 |
| Kind | SECURITY |
| Risk covered | THR-02 |
| Level | INTEGRATION |
| Preconditions | A malformed policy number |
| Procedure | 1. Request a policy with an invalid number. 2. Inspect the body and the log |
| Expected result | Generic message; the log has no personal data |
| Tool or method | pytest tests/test_policies.py::test_error_hides_personal_data |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | tests/test_policies.py::test_error_hides_personal_data in the CI run |
| Status | PASS |

### TC-04 · Expired or tampered token

| Field | Value |
|---|---|
| Covers | SR-03 |
| Kind | SECURITY |
| Risk covered | THR-03 |
| Level | INTEGRATION |
| Preconditions | One expired token and one with a tampered signature |
| Procedure | 1. Call with the expired token. 2. Call with the tampered token |
| Expected result | 401 in both cases |
| Tool or method | pytest tests/test_policies.py::test_expired_token_gets_401 |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | tests/test_policies.py::test_expired_token_gets_401 in the CI run |
| Status | PASS |

### TC-05 · Encrypted transport

| Field | Value |
|---|---|
| Covers | SR-03 |
| Kind | SECURITY |
| Risk covered | THR-03 |
| Level | E2E |
| Preconditions | Staging environment deployed |
| Procedure | 1. Call the API over HTTP. 2. Check it redirects to HTTPS. 3. Check the negotiated TLS version |
| Expected result | Redirect to HTTPS and TLS 1.2 or higher |
| Tool or method | Manual check with an HTTP client |
| Automation | MANUAL |
| Environment | STAGING |
| Evidence | EV-02 |
| Status | PASS |

### TC-06 · Listing under load

| Field | Value |
|---|---|
| Covers | QR-01 |
| Kind | QUALITY |
| Risk covered | — |
| Level | PERFORMANCE |
| Preconditions | Test environment with fictitious policies; third parties stubbed |
| Procedure | 1. Ramp to 20 requests/s over 1 minute. 2. Hold for 5 minutes. 3. Read p95 latency and error rate |
| Expected result | p95 under 300 ms and under 1% errors |
| Tool or method | Load test script run against the test environment |
| Automation | AUTOMATED |
| Environment | STAGING |
| Evidence | Load test summary of 2026-10-20 attached to the merge request: p95 210 ms, 0.1% errors |
| Status | PASS |

## Security test coverage

| Category | Applies | Test cases | Rationale |
|---|---|---|---|
| Unauthenticated user | YES | TC-04 | — |
| User without permissions | YES | TC-02 | — |
| Access to another user's resources | YES | TC-02 | — |
| Cross-tenant access | NO | — | No tenants |
| Malicious input | YES | TC-03 | — |
| Expired tokens | YES | TC-04 | — |
| Revoked sessions | NO | — | Sessions are unchanged |
| Tampered data | YES | TC-04 | — |
| Wrong keys | NO | — | No keys in this flow |
| External service failures | NO | — | No external services |
| Race conditions | NO | — | Read-only |
| Information exposure | YES | TC-03 | — |
| Secrets in code | NO | — | No new secrets; the gate scans the diff |
| Insecure configuration | YES | TC-05 | — |
| Vulnerable dependencies | NO | — | No new dependencies; DEP-01 evaluated |
