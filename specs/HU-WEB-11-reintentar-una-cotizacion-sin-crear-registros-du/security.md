# Security and privacy assessment · HU-WEB-11

## 1. Data inventory and classification

| ID | Data | Classification | Personal | Sensitive | Purpose |
|---|---|---|---|---|---|
| DATA-01 | Datos de cotización y solicitud (tipo y número de documento, año del vehículo, cobertura, tiers, score y primas calculadas) | CONFIDENTIAL | YES | NO | Tarificación de cotizaciones para clientes de socios B2B |
| DATA-02 | Claves de idempotencia (`Idempotency-Key`), hashes SHA-256 de peticiones y respuestas serializadas (`idempotency_records`) | INTERNAL | NO | NO | Control de reintentos, prevención de duplicados e integridad de transacciones B2B |

## 2. Data lifecycle

### DATA-01 · Datos de cotización y asegurado

| Question | Answer |
|---|---|
| What it contains | Tipo y número de documento de identidad del asegurado, características del vehículo, cobertura y tarifas de prima calculadas |
| Why it is needed | Es el insumo y resultado del cálculo de seguros de automóviles solicitado por el socio |
| Who can access it | El socio de distribución autenticado dueño de la cotización y procesos internos de backend |
| Where it is captured | En el cuerpo JSON de la petición HTTP recibida en el endpoint `POST /api/v1/quote-edge/quotes` |
| How it is transmitted | HTTPS / TLS 1.3 con cifrado en tránsito |
| Where it is stored | En la tabla `quotes` y en el campo `response_body` de la tabla `idempotency_records` en PostgreSQL |
| Copies, caches and backups | Respaldos periódicos cifrados de RDS PostgreSQL; no se cachea en medios públicos |
| How long it is kept | Los registros de idempotencia tienen vigencia de 24 horas; las cotizaciones se conservan según política comercial |
| How access is audited | Eventos de auditoría y logs estructurados en CloudWatch asociados al `partner_id` autenticado sin loguear datos personales en claro |
| How it is deleted or anonymized | Expiración lógica tras 24 horas en idempotencia y eliminación programada de cotizaciones no emitidas |
| What happens if it leaks | Exposición de identificaciones de prospectos y condiciones de pólizas cotizadas |
| Transfers to third parties | Consulta simulada al buró crediticio para la obtención del score del asegurado |

### DATA-02 · Claves de idempotencia y hashes de verificación

| Question | Answer |
|---|---|
| What it contains | Identificador de socio (`partner_id`), clave de idempotencia enviada por el cliente (`idempotency_key`), hash SHA-256 del payload y respuesta guardada |
| Why it is needed | Identificar peticiones repetidas, detectar conflictos de contenido y responder consistentemente sin duplicar registros |
| Who can access it | Exclusivamente el backend en el contexto del socio autenticado |
| Where it is captured | Encabezado HTTP `Idempotency-Key` y hash computado en memoria del cuerpo JSON |
| How it is transmitted | HTTPS / TLS 1.3 en el encabezado de la petición |
| Where it is stored | Tabla `idempotency_records` en PostgreSQL |
| Copies, caches and backups | En los respaldos transaccionales de la base de datos |
| How long it is kept | 24 horas de vigencia activa por clave |
| How access is audited | Logs de auditoría backend ante detección de conflictos (HTTP 409) o reintentos exitosos |
| How it is deleted or anonymized | Reemplazo al vencer la ventana de 24 horas o purga periódica |
| What happens if it leaks | Un atacante podría conocer el formato de claves del socio; no contiene contraseñas ni secretos |
| Transfers to third parties | Ninguna transferencia a terceros |

## 3. Actors and roles

| Actor | Role | Trust level | What they can do |
|---|---|---|---|
| Socio B2B | partner | Autenticado | Emitir cotizaciones y reintentar peticiones utilizando encabezados de idempotencia en Quote Edge |
| Atacante externo | Ninguno | No confiable | Intentar enviar peticiones sin autenticación o saturar el endpoint con peticiones sin clave |
| Socio B2B malicioso | partner | Autenticado | Intentar colisionar o adivinar claves de otros socios para interferir con sus operaciones |

## 4. Trust boundaries

| Boundary | Between | What is validated when crossing it |
|---|---|---|
| API Gateway / Quote Edge | Internet y backend de Solventa | Token OAuth2 JWT de socio (`partner_id`, rol `partner`, expiración) y presencia obligatoria de `Idempotency-Key` |
| Persistencia Multi-tenant | Capa de servicios y PostgreSQL | Confinamiento estricto por `partner_id` en las consultas de `idempotency_records` y `quotes` |

## 5. Data flows

| Source | Destination | Data | Channel | Protection |
|---|---|---|---|---|
| Socio B2B | Quote Edge API | DATA-01, DATA-02 | HTTPS / TLS 1.3 | CRY-01, CTL-01 |
| Quote Edge API | PostgreSQL (`idempotency_records`, `quotes`) | DATA-01, DATA-02 | Conexión privada con TLS | CTL-02, CTL-03, CTL-04 |

## 6. Third-party services

| Service | Use | Data shared | Location | Controls |
|---|---|---|---|---|
| Buró de crédito (simulado) | Obtención de score para ajuste de prima en cotización | DATA-01 (`document_number`) | Colombia / Local | CTL-05 |

## 7. Attack surface

| Surface | Exposure | Inputs the attacker controls |
|---|---|---|
| `POST /api/v1/quote-edge/quotes` | Autenticado (partner) | Encabezado `Idempotency-Key` y payload JSON `QuoteRequest` |

## 8. Threat model

| ID | STRIDE | Asset | Threat | Actor | Likelihood | Impact | Risk | Controls |
|---|---|---|---|---|---|---|---|---|
| THR-01 | T | Cuerpo de la solicitud | Reutilizar una Idempotency-Key vigente enviando un payload modificado para intentar alterar la cotización previa | Atacante o cliente defectuoso | MEDIUM | MEDIUM | MEDIUM | CTL-03 |
| THR-02 | D | Base de datos de cotizaciones | Omitir deliberadamente la Idempotency-Key para provocar duplicación masiva de cotizaciones y saturar cuotas | Atacante o cliente mal integrado | MEDIUM | MEDIUM | MEDIUM | CTL-01 |
| THR-03 | I | Cotizaciones de otros socios | Adivinar o reutilizar una Idempotency-Key de otro socio para acceder a su cotización o bloquear su transacción | Socio hostil | LOW | HIGH | MEDIUM | CTL-02 |
| THR-04 | T | Vigencia de la cotización | Reutilizar indefinidamente claves de idempotencia antiguas para forzar tarifas o condiciones vencidas | Socio de distribución | LOW | MEDIUM | LOW | CTL-04 |

## 9. Controls

| ID | Control | Domain | Status | Mitigates | Tests | Tasks | References | Rationale |
|---|---|---|---|---|---|---|---|---|
| CTL-01 | Validación obligatoria del encabezado `Idempotency-Key` en `POST /api/v1/quote-edge/quotes` con rechazo HTTP 400 ante omisión o valor vacío | API | MISSING | THR-02, DATA-02 | TC-03 | T-01 | OWASP API4:2023 | Protege la base de datos contra duplicación de registros por reintentos sin clave |
| CTL-02 | Confinamiento multi-tenant en tabla `idempotency_records` con clave primaria compuesta `(partner_id, idempotency_key)` derivada del token autenticado | DATA | EXISTING | THR-03, DATA-01 | TC-05 | — | OWASP API1:2023 | Impide colisiones y fugas de datos entre distintos socios |
| CTL-03 | Cálculo de hash canónico SHA-256 del cuerpo de la petición y rechazo con HTTP 409 Conflict ante colisión de clave con contenido diferente | API | EXISTING | THR-01, DATA-02 | TC-02 | T-01 | OWASP API8:2023 | Garantiza la inmutabilidad de la operación idempotente |
| CTL-04 | Ventana de vigencia temporal de 24 horas para claves de idempotencia, tratando registros con más de 24 horas como nuevas solicitudes | BACKEND | MISSING | THR-04, DATA-02 | TC-04 | T-01 | ASR-05, HA-11 | Evita que claves antiguas bloqueen recotizaciones o congelen tarifas obsoletas |
| CTL-05 | Simulación segura de llamadas a buró crediticio con timeouts y degradación controlada | BACKEND | EXISTING | THR-02 | TC-01 | — | HA-05 | Protege la disponibilidad del servicio ante lentitud externa |

## 10. Cryptography

### CRY-01 · Hash SHA-256 de verificación de idempotencia

| Field | Value |
|---|---|
| Protects | DATA-02 |
| Type | HASH |
| Algorithm or service | SHA-256 (`hashlib.sha256`) |
| Rationale | Detección determinista e inmutable de modificaciones en el cuerpo de peticiones reintentadas con la misma clave |
| Key management | N/A (función hash matemática sin clave secreta) |
| Permissions | Lectura y cálculo en memoria de la aplicación backend |
| Rotation | N/A (estándar criptográfico SHA-256) |
| Recovery | N/A (función unidireccional determinista) |
| Failure behavior | Si el hash no coincide con el guardado, se rechaza inmediatamente la petición con HTTP 409 |
| Tests | TC-02 |

## 11. Secrets and keys

| Secret | Location | Access | Environments | Rotation | Revocation | Leak detection |
|---|---|---|---|---|---|---|
| `JWT_SECRET_KEY` | Variables de entorno / AWS Secrets Manager | Backend API | dev, staging, prod | Semestral | Inmediata vía actualización de variable en ECS | Escaneo de código estático en CI |

## 12. Authentication, authorization and sessions

| Check | Applies | Controls | Rationale |
|---|---|---|---|
| User identification | YES | CTL-02 | Autenticación de socios vía token JWT con claim `partner_id` |
| Secure authentication | YES | CTL-02 | OAuth2 Client Credentials con `client_secret` validado mediante hash seguro |
| Session management | YES | CTL-02 | Tokens JWT de socio independientes sin estado |
| Token expiration | YES | CTL-02 | Expiración estricta de tokens de socio de 15 minutos |
| Revocation | YES | CTL-02 | Validación inmediata de `is_active` en cada consulta |
| Server-side permission checks | YES | CTL-02 | Dependencia `get_current_partner` obligatoria en FastAPI |
| Per-resource access (ownership) | YES | CTL-02 | Filtrado por `partner_id` en todas las consultas de base de datos |
| Roles | YES | CTL-02 | Validación estricta del claim `role == "partner"` en Quote Edge |
| Privilege separation | YES | CTL-02 | Rutas de Quote Edge desacopladas del portal web interno de asesores |
| Brute-force protection | YES | CTL-01 | Cuota mensual configurada por socio (`quota_limit`) |
| Rate limiting | YES | CTL-01 | Control de cuota mensual acumulada |
| One-time code (OTP) handling | NO | — | N/A: Flujo M2M entre sistemas B2B vía OAuth2 |
| User enumeration prevention | YES | CTL-02 | Errores genéricos 401 y 404 que no revelan existencia de recursos ajenos |
| CSRF protection | NO | — | N/A: API REST M2M con autenticación Bearer por encabezado HTTP |

## 13. Data isolation and multi-tenancy

| Check | Applies | Controls | Tests | Rationale |
|---|---|---|---|---|
| Tenant isolation | YES | CTL-02 | TC-05 | Clave primaria compuesta `(partner_id, idempotency_key)` en tabla `idempotency_records` |
| Server-side authorization | YES | CTL-02 | TC-05 | Extracción del `partner_id` del token firmado criptográficamente |
| Horizontal access | YES | CTL-02 | TC-05 | Prohibido consultar o sobrescribir claves o cotizaciones de otros socios |
| Vertical access | YES | CTL-02 | TC-05 | Rol partner restringido exclusivamente a las rutas `/quote-edge/*` |
| Resource identifiers | YES | CTL-02 | TC-05 | Claves UUID opacas generadas por el sistema |
| Queries and filters | YES | CTL-02 | TC-05 | Consultas SQL con filtro obligatorio `WHERE partner_id = :partner_id` |
| Shared caches | YES | CTL-02 | TC-05 | Persistencia en base de datos particionada por clave compuesta |
| Storage and logs | YES | CTL-02 | TC-05 | Registros de auditoría etiquetados con el socio emisor |
| Negative cross-tenant tests | YES | CTL-02 | TC-05 | Prueba automatizada verificando independencia de la misma clave usada por dos socios |

## 14. Dependencies

| ID | Dependency | Version | Component | Use | Criticality | Evaluation | Result | Status |
|---|---|---|---|---|---|---|---|---|
| DEP-01 | fastapi | 0.115.0 | backend | Framework Web API | HIGH | Poetry lock / Safety 2026-10-24 | 0 vulnerabilidades | EVALUATED |
| DEP-02 | sqlalchemy | 2.0.35 | backend | ORM y base de datos async | HIGH | Poetry lock / Safety 2026-10-24 | 0 vulnerabilidades | EVALUATED |

## 15. Risk register and residual risk

| ID | Risk | Threats | Likelihood | Impact | Level | Treatment | Residual risk | Status |
|---|---|---|---|---|---|---|---|---|
| RISK-01 | Acumulación progresiva de registros de idempotencia antiguos en PostgreSQL | THR-04 | LOW | LOW | LOW | MITIGATE | Bajo: expiración a 24 horas y volumen acotado por las cuotas de cada socio | OPEN |

## 16. Pending decisions

| ID | Decision | Options | Recommendation | Decider | Blocks gate | Status |
|---|---|---|---|---|---|---|
| DEC-01 | Política de retención física de registros de idempotencia tras vencer 24 horas | Mantener en BD con filtro temporal vs eliminación periódica asíncrona | Filtrado temporal en consultas y reemplazo seguro si la clave expiró | Architect | NO | APPROVED |
