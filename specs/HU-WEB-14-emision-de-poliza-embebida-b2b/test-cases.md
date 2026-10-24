# Test cases · HU-WEB-14

## Scenarios

| ID | From | Scenario | Disposition |
|---|---|---|---|
| SC-01 | UC-01, AC-01 | Dado un socio autenticado con cotización vigente, cuando solicita emitir la póliza, entonces se crea la póliza y se devuelve 200 OK | TC-01 |
| SC-02 | UC-01, AC-02 | Dado un socio autenticado con cotización de otro socio o inexistente, cuando solicita emitir la póliza, entonces se devuelve 404 Not Found | TC-02 |
| SC-03 | UC-01, AC-04 | Dada una cotización que ya fue emitida, cuando el socio reintenta la emisión, entonces se devuelve la póliza existente sin duplicar registros | TC-03 |
| SC-04 | UC-02, AC-05 | Dado un socio que intenta consultar una póliza perteneciente a otro socio, cuando realiza la petición GET, entonces recibe 404 Not Found | TC-04 |
| SC-05 | UC-01, AC-03 | Dada una cotización cuya fecha de vencimiento ya pasó, cuando se solicita su emisión, entonces se rechaza con 409 Conflict | TC-05 |
| SC-06 | UC-01, AC-07 | Dada una petición a los endpoints de pólizas sin autenticación o con credencial no autorizada, cuando se procesa, entonces se rechaza con 401 Unauthorized | TC-06 |
| SC-07 | UC-03, AC-06 | Dado un socio con varias pólizas emitidas, cuando consulta el listado histórico, entonces recibe exclusivamente sus pólizas ordenadas | TC-07 |

## Scenario coverage

| Kind | Applies | Scenarios | Rationale |
|---|---|---|---|
| Main flow | YES | SC-01 | Emisión normal de póliza a partir de cotización vigente |
| Alternate flows | YES | SC-03 | Reintento idempotente sobre cotización ya emitida |
| Invalid input and errors | YES | SC-02, SC-05 | Rechazo por cotizaciones ajenas, inexistentes o vencidas |
| Limits and boundaries | YES | SC-05 | Validación de límite temporal de expiración de la cotización |
| Related flows before and after | YES | SC-01, SC-07 | Flujo que encadena la cotización previa con la posterior consulta de pólizas |
| Several users, sessions, devices or roles | YES | SC-02, SC-04, SC-06 | Pruebas de multi-tenancy entre múltiples socios y aislamiento con otros roles |
| State and time (expiry, retries, interruptions, going back, offline) | YES | SC-03, SC-05 | Manejo de vigencia temporal e idempotencia ante reintentos |

## Test cases

### TC-01 · Emisión exitosa de póliza digital desde el canal del socio

| Field | Value |
|---|---|
| Covers | AC-01, SR-01 |
| Kind | FUNCTIONAL |
| Risk covered | — |
| Level | INTEGRATION |
| Preconditions | Socio B2B autenticado con cotización vigente creada bajo su propio partner_id |
| Procedure | 1. Enviar POST /api/v1/quote-edge/policies con quote_id válido y tier cotizado. 2. Validar código de estado 200 OK y estructura de la respuesta. |
| Expected result | Póliza generada con consecutivo POL-YYYY-XXXXX, vigencia de un año, asociada al partner_id y evento en outbox |
| Tool or method | pytest backend/tests/integration/test_partner_policy_api.py::test_issue_partner_policy_success |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_partner_policy_api.py::test_issue_partner_policy_success |
| Status | PASS |

### TC-02 · Rechazo de emisión ante cotización ajena (aislamiento horizontal cross-tenant)

| Field | Value |
|---|---|
| Covers | AC-02, SR-02 |
| Kind | SECURITY |
| Risk covered | THR-01 |
| Level | INTEGRATION |
| Preconditions | Dos socios B2B configurados con cotizaciones independientes en base de datos |
| Procedure | 1. Socio A intenta emitir póliza enviando el quote_id perteneciente al Socio B. 2. Verificar código HTTP y cuerpo de error. |
| Expected result | Retorna 404 Not Found sin emitir póliza ni revelar la existencia de la cotización ajena |
| Tool or method | pytest backend/tests/integration/test_partner_policy_api.py::test_issue_policy_cross_tenant_forbidden |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_partner_policy_api.py::test_issue_policy_cross_tenant_forbidden |
| Status | PASS |

### TC-03 · Emisión idempotente y atómica ante reintentos de la misma cotización

| Field | Value |
|---|---|
| Covers | AC-04, SR-04 |
| Kind | SECURITY |
| Risk covered | THR-02 |
| Level | INTEGRATION |
| Preconditions | Cotización vigente del socio que ya fue formalizada y emitida previamente |
| Procedure | 1. Enviar una segunda solicitud de emisión POST /policies con el mismo quote_id. 2. Verificar código HTTP y datos retornados. |
| Expected result | Retorna 200 OK con los mismos datos de la póliza emitida originalmente sin generar un segundo registro en BD |
| Tool or method | pytest backend/tests/integration/test_partner_policy_api.py::test_issue_policy_idempotency |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_partner_policy_api.py::test_issue_policy_idempotency |
| Status | PASS |

### TC-04 · Aislamiento multi-tenant en consulta individual de póliza

| Field | Value |
|---|---|
| Covers | AC-05, SR-03 |
| Kind | SECURITY |
| Risk covered | THR-03 |
| Level | INTEGRATION |
| Preconditions | Póliza emitida perteneciente al Socio A |
| Procedure | 1. Socio B invoca GET /api/v1/quote-edge/policies/{policy_number} usando el número de póliza del Socio A. |
| Expected result | Retorna 404 Not Found protegiendo la confidencialidad de la información |
| Tool or method | pytest backend/tests/integration/test_partner_policy_api.py::test_get_policy_cross_tenant_not_found |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_partner_policy_api.py::test_get_policy_cross_tenant_not_found |
| Status | PASS |

### TC-05 · Rechazo de emisión para cotización vencida

| Field | Value |
|---|---|
| Covers | AC-03, SR-05 |
| Kind | SECURITY |
| Risk covered | THR-04 |
| Level | UNIT |
| Preconditions | Cotización del socio cuya fecha expires_at es anterior a la fecha actual |
| Procedure | 1. Invocar issue_partner_policy con la cotización expirada. |
| Expected result | Se eleva excepción de cotización expirada y la API responde 409 Conflict |
| Tool or method | pytest backend/tests/unit/test_partner_policy.py::test_issue_expired_quote_rejected |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_partner_policy.py::test_issue_expired_quote_rejected |
| Status | PASS |

### TC-06 · Control de acceso y rechazo ante token ausente, expirado o con rol inválido

| Field | Value |
|---|---|
| Covers | AC-07, SR-01 |
| Kind | SECURITY |
| Risk covered | THR-05 |
| Level | INTEGRATION |
| Preconditions | Endpoints de Quote Edge disponibles |
| Procedure | 1. Invocar POST y GET /policies sin token, con token expirado y con token de rol advisor. |
| Expected result | En todos los casos responde 401 Unauthorized impidiendo el acceso |
| Tool or method | pytest backend/tests/integration/test_partner_policy_api.py::test_policy_endpoints_unauthenticated |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_partner_policy_api.py::test_policy_endpoints_unauthenticated |
| Status | PASS |

### TC-07 · Listado histórico de pólizas confinado estrictamente al socio (CQRS)

| Field | Value |
|---|---|
| Covers | AC-06 |
| Kind | FUNCTIONAL |
| Risk covered | — |
| Level | INTEGRATION |
| Preconditions | Múltiples pólizas emitidas en la base de datos pertenecientes a diferentes socios |
| Procedure | 1. Invocar GET /api/v1/quote-edge/policies con token del socio. 2. Inspeccionar la lista de retorno. |
| Expected result | Retorna únicamente las pólizas cuyo partner_id coincide con el socio autenticado |
| Tool or method | pytest backend/tests/integration/test_partner_policy_api.py::test_list_partner_policies_isolated |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_partner_policy_api.py::test_list_partner_policies_isolated |
| Status | PASS |

### TC-08 · Rendimiento de emisión atómica y consulta CQRS bajo carga local

| Field | Value |
|---|---|
| Covers | QR-01, QR-02 |
| Kind | QUALITY |
| Risk covered | — |
| Level | PERFORMANCE |
| Preconditions | Base de datos local activa y poblada |
| Procedure | 1. Ejecutar batería de emisiones consecutivas y consultas CQRS midiendo los tiempos de respuesta. |
| Expected result | El percentil 95 de tiempo de respuesta es inferior a 200 ms en emisión y menor a 100 ms en lectura CQRS |
| Tool or method | pytest backend/tests/integration/test_partner_policy_api.py::test_policy_issue_performance |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_partner_policy_api.py::test_policy_issue_performance |
| Status | PASS |

## Security test coverage

| Category | Applies | Test cases | Rationale |
|---|---|---|---|
| Unauthenticated user | YES | TC-06 | Verificación de rechazo 401 sin credenciales |
| User without permissions | YES | TC-06 | Verificación de rechazo con rol no autorizado |
| Access to another user's resources | YES | TC-02, TC-04 | Pruebas de acceso horizontal a cotizaciones y pólizas ajenas |
| Cross-tenant access | YES | TC-02, TC-04 | Pruebas de aislamiento estricto entre socios distintos |
| Malicious input | YES | TC-05 | Validación de rechazo ante cotizaciones expiradas o datos inválidos |
| Expired tokens | YES | TC-06 | Rechazo de peticiones con tokens vencidos |
| Revoked sessions | YES | TC-06 | Rechazo de peticiones si el socio fue revocado |
| Tampered data | YES | TC-06 | Rechazo de tokens con firma adulterada |
| Wrong keys | YES | TC-06 | Rechazo de tokens firmados con clave secreta errónea |
| External service failures | NO | — | La emisión de pólizas opera sin dependencias síncronas de servicios externos |
| Race conditions | YES | TC-03 | Validación de idempotencia y consistencia ante emisiones concurrentes |
| Information exposure | YES | TC-02, TC-04 | Validación de respuestas 404 para evitar enumeración de recursos |
| Secrets in code | YES | TC-06 | Verificación de que no existan secretos hardcodeados en los componentes |
| Insecure configuration | YES | TC-06 | Verificación de configuraciones de seguridad de endpoints |
| Vulnerable dependencies | NO | — | No se agregan nuevas librerías en esta historia |
