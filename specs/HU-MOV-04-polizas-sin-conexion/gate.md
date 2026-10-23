# Definition of Done and security gate · HU-MOV-04

| Field | Value |
|---|---|
| Security status | IN_PROGRESS |
| Evaluated on | 2026-10-23 |
| Command | python sdd/tools/sdd.py spec validate specs/HU-MOV-04-polizas-sin-conexion |

<!-- Status: IN_PROGRESS, IMPLEMENTED, SECURITY_TESTS_PENDING, SECURITY_REVIEW_PENDING, RISK_ACCEPTED,
     SECURITY_VERIFIED or BLOCKED. The validator computes the status the evidence supports and rejects a
     higher declared one. An agent may prepare evidence; it never signs reviews or accepts risk.
     With "requireSignatures": false in sdd/config.json, the merge request approval is the security review
     and risk decisions recorded in the spec count as accepted; the two signature tables are optional. -->

## Definition of Done

- [ ] Acceptance criteria implemented, each covered by a passing test case.
- [ ] Security requirements mitigated by an applicable control and verified by a security test case.
- [ ] No required control MISSING.
- [ ] No secret in the code, logs, artifacts or this package.
- [ ] New or updated dependencies evaluated.
- [ ] Personal data handling reviewed (complete lifecycle, nothing UNKNOWN).
- [ ] MEDIUM or higher residual risks mitigated or accepted by an authorized person.
- [ ] Security review approved by a person other than the author.
- [ ] Closeout: every acceptance criterion MET with evidence.
- [ ] `python sdd/tools/sdd.py spec validate` reports no errors.

## Security reviews

| Reviewer | Role | Date | Scope | Result |
|---|---|---|---|---|

## Risk acceptance

| Risk | Decision | Approved by | Role | Date | Expires |
|---|---|---|---|---|---|
| RISK-01 | ACCEPT | Juan Camilo Peña | Owner | 2026-10-23 | — |
| RISK-02 | ACCEPT | Juan Camilo Peña | Owner | 2026-10-23 | — |
| RISK-03 | ACCEPT | Juan Camilo Peña | Owner | 2026-10-23 | — |

## Evidence

| ID | Evidence | Supports | Location | Status |
|---|---|---|---|---|
| EV-01 | Pruebas del endpoint de pólizas del asegurado | SR-01, SR-02, CTL-01, CTL-02, TC-01, TC-02, TC-03 | backend/tests/integration/test_insured_policies_api.py | AVAILABLE |
| EV-02 | Pruebas de la billetera, del almacén y del borrado | SR-02, SR-04, CTL-02, CTL-04, TC-03, TC-04, TC-05, TC-07 | movil/app/src/test/java/com/solventa/app/ui/wallet/ | AVAILABLE |
| EV-03 | Prueba instrumentada del cifrado (hecha) y prueba manual de la entrada con huella (pendiente) | SR-03, SR-05, CTL-03, CTL-05, TC-06, TC-08 | Merge request de HU-MOV-04 | PENDING |
| EV-04 | Revisión de accesibilidad con TalkBack y Accessibility Scanner | QR-01, TC-09 | Merge request de HU-MOV-04 | PENDING |
| EV-05 | Consulta en OSV.dev de las dependencias nuevas | SR-03, TC-10 | security.md, sección 14 | AVAILABLE |

## Closeout

<!-- Filled by spec-close: one row per acceptance criterion (AC) and quality requirement (QR).
     Result: MET, NOT MET or PARTIAL, with file:line or path::test evidence.
     The spec cannot move to DONE while one is not MET. -->

| Criterion | Result | Evidence |
|---|---|---|
