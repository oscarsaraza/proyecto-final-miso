# Test cases · {{ID}}

<!-- Every acceptance criterion (AC), quality requirement (QR) and security requirement (SR) is covered by
     at least one test case. Kind: FUNCTIONAL, QUALITY or SECURITY; a SECURITY test cites the threat (THR)
     or risk (RISK) it covers. Level: UNIT, INTEGRATION, CONTRACT, E2E, PERFORMANCE, ACCESSIBILITY or
     STATIC (scans, linters, configuration checks); the test-design skill says when to use each.
     Status: PENDING, PASS, FAIL, BLOCKED or N/A. PASS needs evidence; when evidence cites path::test or
     path::"test name", the validator checks it exists. Environment: LOCAL, CI, DEV or STAGING.
     PRODUCTION needs an Authorization row. Never test against production or third parties without
     written authorization. -->

## Scenarios

<!-- Derive what can happen around this story before writing test cases — not only what it says. Start
     from its own elements (actors, data, rules, states, steps, dependencies, what comes before and after,
     time) and look at each one through the kinds in the coverage table; the method is in the test-design
     skill. Disposition: the test case that covers it (TC-NN), or OUT OF SCOPE: <why, or the story that
     covers it>. A scenario in scope that the story does not state becomes a DERIVED criterion in spec.md.
     Only a LOW profile may write: N/A: <rationale>. -->

| ID | From | Scenario | Disposition |
|---|---|---|---|
| SC-01 | <fill: UC-NN or AC-NN> | <fill: Given …, when …, then …> | <fill: TC-NN or OUT OF SCOPE: why> |

## Scenario coverage

<!-- Review every kind. YES needs scenarios; NO needs a rationale. Authentication requires related flows
     and state and time; authorization or tenants require several users. -->

| Kind | Applies | Scenarios | Rationale |
|---|---|---|---|
| Main flow | <fill> | <fill> | <fill> |
| Alternate flows | <fill> | <fill> | <fill> |
| Invalid input and errors | <fill> | <fill> | <fill> |
| Limits and boundaries | <fill> | <fill> | <fill> |
| Related flows before and after | <fill> | <fill> | <fill> |
| Several users, sessions, devices or roles | <fill> | <fill> | <fill> |
| State and time (expiry, retries, interruptions, going back, offline) | <fill> | <fill> | <fill> |

## Test cases

### TC-01 · <fill: name>

| Field | Value |
|---|---|
| Covers | <fill: AC-NN, SR-NN> |
| Kind | <fill: FUNCTIONAL, QUALITY or SECURITY> |
| Risk covered | <fill: THR-NN or RISK-NN for SECURITY; — for FUNCTIONAL> |
| Level | <fill: UNIT, INTEGRATION, CONTRACT, E2E, PERFORMANCE, ACCESSIBILITY or STATIC> |
| Preconditions | <fill> |
| Procedure | <fill: 1. … 2. …> |
| Expected result | <fill> |
| Tool or method | <fill: e.g. pytest tests/test_x.py::test_y> |
| Automation | <fill: AUTOMATED or MANUAL> |
| Environment | <fill: LOCAL, CI, DEV or STAGING> |
| Evidence | PENDING |
| Status | PENDING |

## Security test coverage

<!-- Review every category. YES needs test cases; NO needs a rationale. -->

| Category | Applies | Test cases | Rationale |
|---|---|---|---|
| Unauthenticated user | <fill> | <fill> | <fill> |
| User without permissions | <fill> | <fill> | <fill> |
| Access to another user's resources | <fill> | <fill> | <fill> |
| Cross-tenant access | <fill> | <fill> | <fill> |
| Malicious input | <fill> | <fill> | <fill> |
| Expired tokens | <fill> | <fill> | <fill> |
| Revoked sessions | <fill> | <fill> | <fill> |
| Tampered data | <fill> | <fill> | <fill> |
| Wrong keys | <fill> | <fill> | <fill> |
| External service failures | <fill> | <fill> | <fill> |
| Race conditions | <fill> | <fill> | <fill> |
| Information exposure | <fill> | <fill> | <fill> |
| Secrets in code | <fill> | <fill> | <fill> |
| Insecure configuration | <fill> | <fill> | <fill> |
| Vulnerable dependencies | <fill> | <fill> | <fill> |
