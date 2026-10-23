# Definition of Done and security gate · HOTFIX

| Field | Value |
|---|---|
| Security status | SECURITY_TESTS_PENDING |
| Evaluated on | 2026-10-22 |
| Command | python sdd/tools/sdd.py spec validate specs/HOTFIX-transporte-y-borde |

## Definition of Done

- [x] Acceptance criteria implemented, each covered by a test case (TC-04 to TC-07 run after the deploy).
- [x] Security requirements mitigated by an applicable control and verified by a security test case.
- [x] No required control MISSING.
- [x] No secret in the code, logs, artifacts or this package.
- [x] New or updated dependencies evaluated.
- [x] Personal data handling reviewed (complete lifecycle, nothing UNKNOWN).
- [x] MEDIUM or higher residual risks mitigated or accepted.
- [ ] Security review: the approval of the pull request.
- [ ] Closeout: every acceptance criterion MET with evidence.
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
| EV-01 | Balanceador interno y entrada solo desde CloudFront | SR-02, CTL-02, TC-01 | terraform/modules/alb/main.tf | AVAILABLE |
| EV-02 | VPC origin, encabezados y función de rutas | SR-01, CTL-01, CTL-03, TC-01 | terraform/modules/web_hosting/main.tf | AVAILABLE |
| EV-03 | Build sin scripts inline | SR-03, CTL-03, TC-03 | web/angular.json | AVAILABLE |
| EV-04 | Verificación tras el despliegue | SR-01, SR-02, TC-04 | URL de CloudFront después de fusionar a main | PENDING |

## Closeout

<!-- Filled by spec-close: one row per acceptance criterion (AC) and quality requirement (QR).
     Result: MET, NOT MET or PARTIAL, with file:line or path::test evidence.
     The spec cannot move to DONE while one is not MET. -->

| Criterion | Result | Evidence |
|---|---|---|
