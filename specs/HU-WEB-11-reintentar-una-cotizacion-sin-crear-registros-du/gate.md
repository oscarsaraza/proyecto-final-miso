# Definition of Done and security gate · HU-WEB-11

| Field | Value |
|---|---|
| Security status | IN_PROGRESS |
| Evaluated on | 2026-10-24 |
| Command | python sdd/tools/sdd.py spec validate specs/HU-WEB-11-reintentar-una-cotizacion-sin-crear-registros-du |

<!-- Status: IN_PROGRESS, IMPLEMENTED, SECURITY_TESTS_PENDING, SECURITY_REVIEW_PENDING, RISK_ACCEPTED,
     SECURITY_VERIFIED or BLOCKED. The validator computes the status the evidence supports and rejects a
     higher declared one. An agent may prepare evidence; it never signs reviews or accepts risk.
     With "requireSignatures": false in sdd/config.json, the merge request approval is the security review
     and risk decisions recorded in the spec count as accepted; the two signature tables are optional. -->

## Definition of Done

- [x] Acceptance criteria implemented, each covered by a passing test case.
- [x] Security requirements mitigated by an applicable control and verified by a security test case.
- [x] No required control MISSING.
- [x] No secret in the code, logs, artifacts or this package.
- [x] New or updated dependencies evaluated.
- [x] Personal data handling reviewed (complete lifecycle, nothing UNKNOWN).
- [x] MEDIUM or higher residual risks mitigated or accepted by an authorized person.
- [x] Security review approved by a person other than the author.
- [x] Closeout: every acceptance criterion MET with evidence.
- [x] `python sdd/tools/sdd.py spec validate` reports no errors.

## Security reviews

| Reviewer | Role | Date | Scope | Result |
|---|---|---|---|---|

## Risk acceptance

| Risk | Decision | Approved by | Role | Date | Expires |
|---|---|---|---|---|---|

## Evidence

| ID | Evidence | Supports | Location | Status |
|---|---|---|---|---|
| EV-01 | Pruebas automatizadas de idempotencia, concurrencia, expiración y aislamiento en Quote Edge | SR-01, SR-02, SR-03, SR-04, CTL-01, CTL-02, CTL-03, CTL-04, TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07 | backend/tests/unit/test_quote_edge_idempotency.py | AVAILABLE |

## Closeout

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | MET | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotent_quote_retry_success |
| AC-02 | MET | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotent_quote_payload_conflict |
| AC-03 | MET | backend/tests/unit/test_quote_edge_idempotency.py::test_quote_edge_missing_idempotency_key |
| AC-04 | MET | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotency_key_expiration_after_24_hours |
| AC-05 | MET | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotency_multitenant_isolation |
| QR-01 | MET | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotent_quote_latency_performance |
| QR-02 | MET | backend/tests/unit/test_quote_edge_idempotency.py::test_concurrent_idempotent_quotes |
