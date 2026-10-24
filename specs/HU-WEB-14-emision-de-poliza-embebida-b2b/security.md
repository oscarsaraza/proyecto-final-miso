# Security and privacy assessment · HU-WEB-14

## 1. Data inventory and classification

| ID | Data | Classification | Personal | Sensitive | Purpose |
|---|---|---|---|---|---|
| DATA-01 | Datos de la póliza y asegurado: documento de identidad, beneficiarios, coberturas y primas | CONFIDENTIAL | YES | NO | Formalización jurídica del contrato de seguro digital y consulta de pólizas emitidas |
| DATA-02 | Credenciales del socio: Client ID, Secret y token JWT de acceso OAuth2 | RESTRICTED | NO | NO | Autenticación y autorización confinada del socio de distribución B2B |

## 2. Data lifecycle

### DATA-01 · Datos de póliza y asegurado

| Question | Answer |
|---|---|
| What it contains | Número de documento del asegurado (`insured_document`), nombres y parentesco de beneficiarios, condiciones del plan cotizado y prima |
| Why it is needed | Requerido para la emisión válida de la póliza digital y la asignación contractual de derechos |
| Who can access it | El socio de distribución que originó la póliza, el asegurado titular y los procesos internos de auditoría |
| Where it is captured | En el sistema del socio B2B y transmitido vía API en el cuerpo de emisión |
| How it is transmitted | HTTPS / TLS 1.2+ cifrado en tránsito hacia el backend |
| Where it is stored | En PostgreSQL tabla `policies` (columna `insured_document`, `beneficiaries` JSON, `conditions` JSON) |
| Copies, caches and backups | Encolado como evento `PolicyIssued` en la tabla `outbox_messages` y respaldado en backups periódicos de RDS |
| How long it is kept | Durante la vigencia de la póliza más el término legal de retención de contratos de seguros |
| How access is audited | Registros estructurados en logs de aplicación con severidad INFO/WARNING asociando `partner_id` |
| How it is deleted or anonymized | Según la política de retención legal y ejercicio de derechos de protección de datos |
| What happens if it leaks | Exposición de vinculación aseguradora de clientes; riesgo mitigado por aislamiento estricto multi-tenant |
| Transfers to third parties | Únicamente entre el socio de distribución acreditado y Solventa |

### DATA-02 · Credenciales y tokens del socio

| Question | Answer |
|---|---|
| What it contains | `client_id`, hash seguro de `client_secret` y tokens JWT firmados con rol partner |
| Why it is needed | Autenticar y confinar el acceso de cada socio en la API B2B de Quote Edge |
| Who can access it | El sistema de integración del socio y el módulo de seguridad del backend |
| Where it is captured | Header HTTP `Authorization: Bearer <token>` |
| How it is transmitted | HTTPS / TLS en tránsito |
| Where it is stored | El token JWT no se almacena en backend (stateless); el secret del socio se almacena con hash bcrypt en tabla `partners` |
| Copies, caches and backups | No hay copias de tokens en texto claro ni en logs |
| How long it is kept | Tokens JWT con expiración configurable (por defecto 60 minutos) |
| How access is audited | Eventos de auditoría de seguridad JSON (PARTNER_AUTH_SUCCESS, PARTNER_AUTH_FAILED) en stdout/CloudWatch |
| How it is deleted or anonymized | Expiración automática del token o revocación inmediata del socio cambiando su estado a `REVOKED` |
| What happens if it leaks | Suplantación del socio; mitigado por expiración corta y capacidad de revocación inmediata |
| Transfers to third parties | No se transfiere a terceros |

## 3. Actors and roles

| Actor | Role | Trust level | What they can do |
|---|---|---|---|
| Socio B2B | partner | Autenticado | Emitir pólizas a partir de sus propias cotizaciones y consultar únicamente sus pólizas |
| Asesor Comercial | advisor | Autenticado | Gestionar cotizaciones y pólizas del canal comercial interno |
| Asegurado | insured | Autenticado | Consultar sus pólizas personales desde la aplicación móvil |
| Atacante externo | Ninguno | No confiable | Intentar peticiones no autenticadas, manipular IDs o eludir el aislamiento multi-tenant |

## 4. Trust boundaries

| Boundary | Between | What is validated when crossing it |
|---|---|---|
| Borde API (Quote Edge) | Internet / Socio y Backend FastAPI | Firma del token JWT, rol partner, estado activo del socio y estructura del payload |
| Límite Multi-Tenant | BFF y PostgreSQL (Módulo Policy) | Pertenencia de la cotización y póliza al `partner_id` del token; exclusión total de datos ajenos |

## 5. Data flows

| Source | Destination | Data | Channel | Protection |
|---|---|---|---|---|
| Sistema del Socio | Quote Edge BFF | DATA-01, DATA-02 | HTTPS | CRY-01, CTL-01 |
| Quote Edge BFF | PostgreSQL (policies, outbox) | DATA-01 | Conexión interna de base de datos | CTL-02, CTL-03 |

## 6. Third-party services

N/A: no se utilizan servicios externos adicionales para la emisión B2B.

## 7. Attack surface

| Surface | Exposure | Inputs the attacker controls |
|---|---|---|
| `POST /api/v1/quote-edge/policies` | Autenticada (rol partner) | Token Bearer, `quote_id`, `tier`, lista de beneficiarios |
| `GET /api/v1/quote-edge/policies/{policy_number}` | Autenticada (rol partner) | Token Bearer, parámetro de ruta `policy_number` |
| `GET /api/v1/quote-edge/policies` | Autenticada (rol partner) | Token Bearer |

## 8. Threat model

| ID | STRIDE | Asset | Threat | Actor | Likelihood | Impact | Risk | Controls |
|---|---|---|---|---|---|---|---|---|
| THR-01 | S, E | DATA-01 | Un socio intenta emitir una póliza referenciando un `quote_id` perteneciente a otro socio o al canal asesor | Atacante externo | MEDIUM | HIGH | HIGH | CTL-02 |
| THR-02 | T | DATA-01 | Peticiones concurrentes idénticas intentan generar múltiples pólizas duplicadas para la misma cotización | Atacante externo | MEDIUM | MEDIUM | MEDIUM | CTL-03 |
| THR-03 | I | DATA-01 | Un socio intenta consultar el detalle o historial de pólizas emitidas por otro socio competidor | Atacante externo | MEDIUM | HIGH | HIGH | CTL-02 |
| THR-04 | T | DATA-01 | Un socio intenta emitir una póliza con una cotización vencida para evadir actualización de primas | Atacante externo | MEDIUM | MEDIUM | MEDIUM | CTL-04 |
| THR-05 | S | DATA-02 | Peticiones no autenticadas o con token expirado/revocado intentan acceder a los endpoints de pólizas | Atacante externo | HIGH | HIGH | CRITICAL | CTL-01 |

## 9. Controls

| ID | Control | Domain | Status | Mitigates | Tests | Tasks | References | Rationale |
|---|---|---|---|---|---|---|---|---|
| CTL-01 | Autenticación perimetral OAuth2 con rol partner y validación de socio activo | API | EXISTING | THR-05, DATA-02 | TC-01, TC-06 | T-03 | ASVS 5.0 V2, CWE-287 | Reutiliza get_current_partner implementado en HU-WEB-10 |
| CTL-02 | Aislamiento multi-tenant en consultas y emisión con respuesta 404 ante recursos ajenos | BACKEND | EXISTING | THR-01, THR-03, DATA-01 | TC-02, TC-04 | T-01, T-02 | ASVS 5.0 V4, CWE-639 | Impide acceso horizontal y previene enumeración de datos |
| CTL-03 | Emisión atómica e idempotente con restricción única sobre `quote_id` y `ON CONFLICT DO NOTHING` | BACKEND | EXISTING | THR-02, DATA-01 | TC-03 | T-02 | ASVS 5.0 V11, CWE-362 | Garantiza consistencia transaccional e imposibilita pólizas duplicadas |
| CTL-04 | Validación estricta de vigencia temporal de cotización (`quote.expires_at > now`) rechazando con 409 | BACKEND | EXISTING | THR-04, DATA-01 | TC-05 | T-02 | ASVS 5.0 V1, CWE-613 | Protege las reglas actuariales y vigencia de precios |

## 10. Cryptography

### CRY-01 · Cifrado en tránsito TLS

| Field | Value |
|---|---|
| Protects | DATA-01, DATA-02 |
| Type | TLS |
| Algorithm or service | TLS 1.2+ obligatorio en balanceador y CloudFront |
| Rationale | Cifra todas las comunicaciones API entre socios y el backend para prevenir interceptación |
| Key management | Certificados administrados por AWS ACM / CloudFront |
| Permissions | Administrado por infraestructura |
| Rotation | Automática por el proveedor de nube |
| Recovery | No aplica; reemplazo automático por AWS |
| Failure behavior | Conexiones inseguras en HTTP plano son rechazadas o redirigidas |
| Tests | TC-01 |

## 11. Secrets and keys

| Secret | Location | Access | Environments | Rotation | Revocation | Leak detection |
|---|---|---|---|---|---|---|
| SECRET_KEY (firma JWT de socios) | Variables de entorno / AWS Secrets Manager | Solo el backend en ejecución | DEV, STAGING, PROD | Rotación anual o ante sospecha de fuga | Modificación en Secrets Manager y reinicio de contenedores | Escaneo preventivo en CI con sdd scan secrets |

## 12. Authentication, authorization and sessions

| Check | Applies | Controls | Rationale |
|---|---|---|---|
| User identification | YES | CTL-01 | Identificación del socio mediante `client_id` y `partner_id` en claims de JWT |
| Secure authentication | YES | CTL-01 | Autenticación OAuth2 Client Credentials con secret hasheado en bcrypt |
| Session management | YES | CTL-01 | Tokens JWT de corta duración (60 min) con validación por petición |
| Token expiration | YES | CTL-01 | Expiración estricta de tokens validada por la librería de JWT |
| Revocation | YES | CTL-01 | Verificación en base de datos del estado ACTIVE del socio en cada invocación |
| Server-side permission checks | YES | CTL-01, CTL-02 | Verificación ineludible en el backend en FastAPI Depends |
| Per-resource access (ownership) | YES | CTL-02 | Comprobación de que `quote.partner_id == current_partner.partner_id` |
| Roles | YES | CTL-01 | Validación explícita de `role == "partner"` en el token |
| Privilege separation | YES | CTL-01, CTL-02 | El socio no puede ejecutar operaciones administrativas ni del canal asesor |
| Brute-force protection | NO | — | Autenticación basada en token firmado; emisión del token protegida por cuota |
| Rate limiting | YES | CTL-01 | Cuotas por socio gobernadas en modelo PartnerDB (`quota_limit`, `quota_used`) |
| One-time code (OTP) handling | NO | — | Flujo puramente máquina a máquina (M2M) sin usuario humano interactivo |
| User enumeration prevention | YES | CTL-02 | Respuestas 404 uniformes ante recursos no existentes o pertenecientes a otros socios |
| CSRF protection | NO | — | API REST sin estado basada en Bearer token, inmune a ataques basados en cookies |

## 13. Data isolation and multi-tenancy

| Check | Applies | Controls | Tests | Rationale |
|---|---|---|---|---|
| Tenant isolation | YES | CTL-02 | TC-02, TC-04 | Cada socio está confinado a sus cotizaciones y pólizas mediante `partner_id` |
| Server-side authorization | YES | CTL-01, CTL-02 | TC-01, TC-02 | El servidor extrae el `partner_id` del token validado y lo impone en la consulta |
| Horizontal access | YES | CTL-02 | TC-02, TC-04 | Intentos de consultar o emitir pólizas de otros socios devuelven 404 |
| Vertical access | YES | CTL-01 | TC-06 | Peticiones con tokens de otros roles (advisor, insured) son rechazadas |
| Resource identifiers | YES | CTL-02 | TC-02, TC-04 | Los identificadores de cotización y póliza no confieren acceso sin validar el tenant |
| Queries and filters | YES | CTL-02 | TC-04 | Todas las cláusulas SELECT incluyen filtro `partner_id == current_partner.partner_id` |
| Shared caches | NO | — | — | No se emplean memorias intermedias ni cachés compartidas |
| Storage and logs | YES | CTL-02 | TC-07 | Los eventos emitidos en outbox registran aggregate_id sin filtrar datos cruzados |
| Negative cross-tenant tests | YES | CTL-02 | TC-02, TC-04 | Pruebas explícitas verificando rechazo 404 al cruzar socios |

## 14. Dependencies

| ID | Dependency | Version | Component | Use | Criticality | Evaluation | Result | Status |
|---|---|---|---|---|---|---|---|---|
| DEP-01 | fastapi | 0.115.0 | backend | Enrutamiento HTTP, inyección de dependencias y OpenAPI | HIGH | OSV.dev 2026-10-24 | No known vulnerabilities | EVALUATED |
| DEP-02 | sqlalchemy | 2.0.35 | backend | ORM y persistencia relacional con PostgreSQL | HIGH | OSV.dev 2026-10-24 | No known vulnerabilities | EVALUATED |

## 15. Risk register and residual risk

| ID | Risk | Threats | Likelihood | Impact | Level | Treatment | Residual risk | Status |
|---|---|---|---|---|---|---|---|---|
| RISK-01 | Reintentos concurrentes masivos generan contención transaccional en PostgreSQL | THR-02 | LOW | MEDIUM | LOW | MITIGATE | Bajo: la atomicidad por índice único previene duplicados y la contención se resuelve por bloqueo optimista | MITIGATED |

## 16. Pending decisions

N/A: el equipo técnico acordó extender `PolicyDB` con `partner_id` indexado y reutilizar el modelo de seguridad de Quote Edge.
