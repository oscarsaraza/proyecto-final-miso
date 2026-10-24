# Test cases · HU-WEB-11

## Scenarios

| ID | From | Scenario | Disposition |
|---|---|---|---|
| SC-01 | UC-01, AC-01 | Dada una solicitud con Idempotency-Key nueva y payload válido, cuando el socio la envía, entonces recibe 200 OK y se registra en base de datos | TC-01 |
| SC-02 | UC-02, AC-01 | Dada una solicitud ya procesada, cuando el socio la reenvía con la misma clave y mismo contenido, entonces recibe 200 OK con la misma cotización sin crear duplicados | TC-01 |
| SC-03 | UC-02, AC-02 | Dada una clave ya usada dentro de las 24 horas, cuando se envía con un payload diferente, entonces se rechaza con 409 Conflict y mensaje descriptivo | TC-02 |
| SC-04 | UC-01, AC-03 | Dada una solicitud B2B al endpoint de cotizaciones sin encabezado Idempotency-Key o vacío, cuando llega, entonces se rechaza con 400 Bad Request | TC-03 |
| SC-05 | UC-03, AC-04 | Dada una clave usada hace más de 24 horas, cuando se reutiliza, entonces se trata como una solicitud nueva calculando y registrando una nueva cotización | TC-04 |
| SC-06 | UC-01, AC-05 | Dados dos socios distintos que utilizan coincidentemente la misma Idempotency-Key, cuando envían sus solicitudes, entonces cada uno procesa su cotización de forma aislada sin conflicto | TC-05 |
| SC-07 | UC-02, QR-01 | Dado un reintento de cotización con clave existente, cuando se procesa, entonces la respuesta se entrega de forma inmediata sin re-ejecutar el cálculo de tarifas ni el buró | TC-07 |
| SC-08 | UC-02, QR-02 | Dadas múltiples peticiones concurrentes enviadas con la misma clave y payload idéntico, cuando se ejecutan en paralelo, entonces devuelven la misma cotización y se crea un único registro | TC-06 |

## Scenario coverage

| Kind | Applies | Scenarios | Rationale |
|---|---|---|---|
| Main flow | YES | SC-01, SC-02 | Flujo principal de emisión inicial y reintento exitoso idempotente |
| Alternate flows | YES | SC-05 | Reutilización de clave tras ventana de vigencia de 24 horas |
| Invalid input and errors | YES | SC-03, SC-04 | Clave ausente (400) y discrepancia de payload (409) |
| Limits and boundaries | YES | SC-05 | Límite temporal de vigencia de 24 horas para claves |
| Related flows before and after | YES | SC-01, SC-02 | Relación entre cálculo de cotización, consumo de cuota y persistencia |
| Several users, sessions, devices or roles | YES | SC-06 | Múltiples socios B2B operando en la plataforma de manera concurrente |
| State and time (expiry, retries, interruptions, going back, offline) | YES | SC-02, SC-05, SC-08 | Expiración a 24 horas, reintentos y concurrencia |

## Test cases

### TC-01 · Reintento idempotente exitoso con la misma clave y contenido idéntico

| Field | Value |
|---|---|
| Covers | AC-01 |
| Kind | FUNCTIONAL |
| Risk covered | — |
| Level | INTEGRATION |
| Preconditions | Socio B2B autenticado con token JWT y cuota disponible |
| Procedure | 1. Enviar POST /api/v1/quote-edge/quotes con encabezado Idempotency-Key y payload válido. 2. Guardar quote_id y cuota consumida. 3. Reenviar la petición con la misma clave y mismo payload. 4. Comparar respuestas y validar base de datos. |
| Expected result | Retorna 200 OK con la misma cotización calculada previamente, no se crea un nuevo registro en `quotes` y `quota_used` no se incrementa adicionalmente |
| Tool or method | pytest backend/tests/unit/test_quote_edge_idempotency.py::test_idempotent_quote_retry_success |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotent_quote_retry_success |
| Status | PASS |

### TC-02 · Detección de conflicto ante reuso de clave con payload diferente (409 Conflict)

| Field | Value |
|---|---|
| Covers | AC-02, SR-03 |
| Kind | SECURITY |
| Risk covered | THR-01 |
| Level | INTEGRATION |
| Preconditions | Socio B2B autenticado que ya registró una cotización con una clave específica |
| Procedure | 1. Enviar cotización inicial con Idempotency-Key "key-conflict-1" y payload A. 2. Enviar segunda solicitud con la misma clave "key-conflict-1" y payload B modificado. |
| Expected result | Retorna HTTP 409 Conflict explicando la discrepancia de contenido para la clave de idempotencia. La cotización previa permanece inalterada. |
| Tool or method | pytest backend/tests/unit/test_quote_edge_idempotency.py::test_idempotent_quote_payload_conflict |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotent_quote_payload_conflict |
| Status | PASS |

### TC-03 · Rechazo de cotización B2B sin encabezado Idempotency-Key (400 Bad Request)

| Field | Value |
|---|---|
| Covers | AC-03, SR-01 |
| Kind | SECURITY |
| Risk covered | THR-02 |
| Level | UNIT |
| Preconditions | Socio B2B autenticado con token JWT válido |
| Procedure | 1. Enviar POST /api/v1/quote-edge/quotes omitiendo el encabezado Idempotency-Key. 2. Enviar POST /api/v1/quote-edge/quotes con encabezado Idempotency-Key compuesto únicamente por espacios en blanco. |
| Expected result | Ambas solicitudes son rechazadas con HTTP 400 Bad Request indicando que el encabezado Idempotency-Key es obligatorio |
| Tool or method | pytest backend/tests/unit/test_quote_edge_idempotency.py::test_quote_edge_missing_idempotency_key |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_quote_edge_idempotency.py::test_quote_edge_missing_idempotency_key |
| Status | PASS |

### TC-04 · Expiración de clave de idempotencia tras 24 horas

| Field | Value |
|---|---|
| Covers | AC-04, SR-04 |
| Kind | SECURITY |
| Risk covered | THR-04 |
| Level | UNIT |
| Preconditions | Registro de idempotencia en base de datos con antigüedad superior a 24 horas |
| Procedure | 1. Insertar un registro de prueba en `idempotency_records` con `created_at` fijado a hace 25 horas. 2. Ejecutar consulta de idempotencia para la misma clave. 3. Reenviar la petición a Quote Edge. |
| Expected result | El sistema reconoce la expiración de la clave, no reutiliza la respuesta anterior y permite registrar una nueva cotización exitosamente |
| Tool or method | pytest backend/tests/unit/test_quote_edge_idempotency.py::test_idempotency_key_expiration_after_24_hours |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotency_key_expiration_after_24_hours |
| Status | PASS |

### TC-05 · Aislamiento multi-tenant de claves de idempotencia entre socios distintos

| Field | Value |
|---|---|
| Covers | AC-05, SR-02 |
| Kind | SECURITY |
| Risk covered | THR-03 |
| Level | INTEGRATION |
| Preconditions | Dos socios B2B configurados independientemente en base de datos con sus respectivos tokens de acceso |
| Procedure | 1. Socio A emite cotización con Idempotency-Key "key-shared-99" y payload del Socio A. 2. Socio B emite cotización con la misma Idempotency-Key "key-shared-99" y payload del Socio B. |
| Expected result | Ambas peticiones responden 200 OK. No ocurre colisión ni error 409 entre socios. Cada respuesta queda aislada y consultable únicamente por su respectivo socio. |
| Tool or method | pytest backend/tests/unit/test_quote_edge_idempotency.py::test_idempotency_multitenant_isolation |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotency_multitenant_isolation |
| Status | PASS |

### TC-06 · Concurrencia de reintentos simultáneos con la misma clave

| Field | Value |
|---|---|
| Covers | AC-01, QR-02 |
| Kind | FUNCTIONAL |
| Risk covered | — |
| Level | INTEGRATION |
| Preconditions | Socio B2B autenticado con token JWT |
| Procedure | 1. Ejecutar concurrentemente mediante asyncio múltiples llamadas al endpoint de cotización con la misma Idempotency-Key y payload idéntico. 2. Evaluar códigos de respuesta y verificar registros generados en la base de datos. |
| Expected result | Todas las peticiones completan exitosamente (200 OK) retornando la misma cotización, y la tabla `quotes` almacena exactamente un registro. |
| Tool or method | pytest backend/tests/unit/test_quote_edge_idempotency.py::test_concurrent_idempotent_quotes |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_quote_edge_idempotency.py::test_concurrent_idempotent_quotes |
| Status | PASS |

### TC-07 · Rendimiento y baja latencia en reintentos idempotentes

| Field | Value |
|---|---|
| Covers | QR-01 |
| Kind | QUALITY |
| Risk covered | — |
| Level | PERFORMANCE |
| Preconditions | Cotización ya registrada y guardada en idempotencia |
| Procedure | 1. Enviar reintentos continuos con la clave y payload de la cotización previa midiendo la latencia de respuesta. 2. Verificar que el tiempo de respuesta sea inferior a 50 ms en condiciones locales. |
| Expected result | El reintento se resuelve inmediatamente desde el registro de idempotencia sin recálculos ni demoras |
| Tool or method | pytest backend/tests/unit/test_quote_edge_idempotency.py::test_idempotent_quote_latency_performance |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_quote_edge_idempotency.py::test_idempotent_quote_latency_performance |
| Status | PASS |

## Security test coverage

| Category | Applies | Test cases | Rationale |
|---|---|---|---|
| Unauthenticated user | YES | TC-03 | Peticiones sin autenticación son rechazadas antes de evaluar la clave |
| User without permissions | YES | TC-05 | Restricción de permisos y roles en Quote Edge |
| Access to another user's resources | YES | TC-05 | Aislamiento estricto de cotizaciones y claves entre socios |
| Cross-tenant access | YES | TC-05 | La colisión o acceso a claves de otros socios está prevenida por diseño |
| Malicious input | YES | TC-02 | Detección y rechazo de payloads alterados bajo la misma clave |
| Expired tokens | YES | TC-03 | Verificación de validez temporal de tokens de socio |
| Revoked sessions | YES | TC-03 | Socios inactivos son rechazados con 401 |
| Tampered data | YES | TC-02 | El hash SHA-256 detecta cualquier discrepancia en los datos |
| Wrong keys | YES | TC-03 | Clave ausente o con espacios en blanco rechazada con 400 |
| External service failures | YES | TC-01 | Resiliencia ante caídas de red o lentitud en buró |
| Race conditions | YES | TC-06 | Pruebas de concurrencia simultánea con la misma clave |
| Information exposure | YES | TC-05 | Las respuestas de error no exponen datos de otros socios |
| Secrets in code | YES | TC-03 | Escaneo de código libre de credenciales en claro |
| Insecure configuration | YES | TC-03 | Validación de configuraciones seguras por defecto |
| Vulnerable dependencies | YES | TC-03 | Verificación de dependencias libres de vulnerabilidades |
