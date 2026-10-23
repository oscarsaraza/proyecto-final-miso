# Definition of Done and security gate · HOTFIX

| Field | Value |
|---|---|
| Security status | SECURITY_TESTS_PENDING |
| Evaluated on | 2026-10-22 |
| Command | python sdd/tools/sdd.py spec validate specs/HOTFIX-configuracion-de-produccion |

## Definition of Done

- [x] Acceptance criteria implemented, each covered by a passing test case (AC-03 also needs TC-12 after the deploy).
- [x] Security requirements mitigated by an applicable control and verified by a security test case.
- [x] No required control MISSING.
- [x] No secret in the code, logs, artifacts or this package.
- [x] New or updated dependencies evaluated.
- [x] Personal data handling reviewed (complete lifecycle, nothing UNKNOWN).
- [x] MEDIUM or higher residual risks mitigated or accepted (RISK-01 to RISK-03 accepted by the team on 2026-10-22, recorded in spec.md; RISK-04 mitigated).
- [ ] Security review approved by a person other than the author (the approval of PR #205).
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
| EV-01 | Pruebas de configuración (llaves, errores sin valores, CORS, documentación) | SR-01, SR-02, CTL-01, CTL-03, TC-01 | backend/tests/unit/test_config.py | AVAILABLE |
| EV-02 | Pruebas de integración del canal de socios, CORS y token con otra llave | SR-04, SR-05, CTL-06, CTL-07, TC-06 | backend/tests/integration/test_health_and_api.py | AVAILABLE |
| EV-03 | Prueba de arranque con production sin cuentas sembradas | SR-06, CTL-08, TC-08 | backend/tests/integration/test_lifespan.py | AVAILABLE |
| EV-04 | Variables de Terraform sin valor por defecto y validadas | SR-03, CTL-04, TC-10 | terraform/variables.tf | AVAILABLE |
| EV-05 | Despliegue verificado con los secretos de CI | SR-03, CTL-05, TC-12 | Workflow de despliegue tras fusionar a main | PENDING |

## Closeout

<!-- Filled by spec-close: one row per acceptance criterion (AC) and quality requirement (QR).
     Result: MET, NOT MET or PARTIAL, with file:line or path::test evidence.
     The spec cannot move to DONE while one is not MET. -->

| Criterion | Result | Evidence |
|---|---|---|
