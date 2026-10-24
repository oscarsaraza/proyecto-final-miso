# Security and privacy assessment · HOTFIX

## 1. Data inventory and classification

| ID | Data | Classification | Personal | Sensitive | Purpose |
|---|---|---|---|---|---|
| DATA-01 | Datos de clientes y asegurados en las solicitudes y respuestas de la API (nombre, documento, correo, teléfono, pólizas) | CONFIDENTIAL | YES | NO | Cotizar, emitir y consultar pólizas |
| DATA-02 | Credenciales, códigos de un solo uso y tokens en las solicitudes | RESTRICTED | NO | NO | Autenticar a asesores y asegurados |

## 2. Data lifecycle

### DATA-01, DATA-02 · Datos en tránsito por el borde

| Question | Answer |
|---|---|
| What it contains | Datos personales de clientes y asegurados, contraseñas, códigos y tokens |
| Why it is needed | Son el contenido de las solicitudes del portal y de la app |
| Who can access it | El cliente que los envía, CloudFront como intermediario y el backend |
| Where it is captured | En el portal y en la app |
| How it is transmitted | TLS hasta CloudFront; desde CloudFront al balanceador interno por la red privada de AWS (VPC origin) |
| Where it is stored | Este cambio no los almacena; el backend los guarda según sus propias historias |
| Copies, caches and backups | CloudFront no cachea /api/* (TTL 0) |
| How long it is kept | Solo durante la solicitud en el borde |
| How access is audited | Este cambio no agrega registros; los registros de CloudFront y del balanceador quedan pendientes |
| How it is deleted or anonymized | No persisten en el borde |
| What happens if it leaks | Exposición de datos personales y de sesiones; este cambio quita la exposición del tramo por internet |
| Transfers to third parties | AWS como proveedor de la nube |

## 3. Actors and roles

| Actor | Role | Trust level | What they can do |
|---|---|---|---|
| Asesor | advisor | Autenticado | Usar el portal por CloudFront |
| Asegurado | insured | Autenticado | Usar la app por CloudFront |
| Atacante externo | Ninguno | No confiable | Llamar endpoints públicos e intentar llegar al backend |
| Sitio web ajeno | Ninguno | No confiable | Intentar embeber el portal o inyectar contenido |

## 4. Trust boundaries

| Boundary | Between | What is validated when crossing it |
|---|---|---|
| CloudFront | Internet y la nube | TLS con el navegador; solo CloudFront entra al balanceador |
| VPC origin | CloudFront y la VPC | Grupo de seguridad con la lista de prefijos de CloudFront |
| Navegador | Portal y contenido ajeno | CSP, X-Frame-Options y nosniff |

## 5. Data flows

| Source | Destination | Data | Channel | Protection |
|---|---|---|---|---|
| Navegador o app | CloudFront | DATA-01, DATA-02 | HTTPS | CRY-01 |
| CloudFront | Balanceador interno | DATA-01, DATA-02 | VPC origin por la red privada de AWS | CTL-01, CTL-02 |

## 6. Third-party services

N/A: no se agregan servicios externos; AWS ya aloja el sistema.

## 7. Attack surface

| Surface | Exposure | Inputs the attacker controls |
|---|---|---|
| Distribución de CloudFront | Pública | Rutas, cabeceras y cuerpos |
| Balanceador | Antes público; ahora solo desde CloudFront | Ninguna directa |
| Portal en el navegador | Pública | Contenido inyectado si existiera una falla de XSS; intentos de embeberlo |

## 8. Threat model

| ID | STRIDE | Asset | Threat | Actor | Likelihood | Impact | Risk | Controls |
|---|---|---|---|---|---|---|---|---|
| THR-01 | I | DATA-01, DATA-02 | Interceptar tokens y datos personales en el tramo HTTP entre CloudFront y el balanceador | Atacante en la red | MEDIUM | HIGH | HIGH | CTL-01 |
| THR-02 | S, E | Backend | Llamar al balanceador directamente para saltarse CloudFront y leer /docs | Atacante externo | HIGH | MEDIUM | HIGH | CTL-02 |
| THR-03 | T, I | DATA-02 | Un script inyectado en el portal lee la sesión | Atacante externo | LOW | HIGH | MEDIUM | CTL-03 |
| THR-04 | T | Portal | Embeber el portal en un sitio ajeno para engañar al asesor | Sitio web ajeno | LOW | MEDIUM | LOW | CTL-04 |
| THR-05 | I | Respuestas de la API | Errores de la API convertidos en 200 con HTML ocultan 401, 403 y 404 a los clientes | Cualquiera | MEDIUM | MEDIUM | MEDIUM | CTL-05 |
| THR-06 | T | DATA-02 | Forzar al navegador a usar HTTP en una visita posterior | Atacante en la red | LOW | MEDIUM | LOW | CTL-06 |

## 9. Controls

| ID | Control | Domain | Status | Mitigates | Tests | Tasks | References | Rationale |
|---|---|---|---|---|---|---|---|---|
| CTL-01 | CloudFront llega al balanceador por un VPC origin, sin cruzar internet | INFRA | EXISTING | THR-01 | TC-01, TC-04 | T-02 | CWE-319 | — |
| CTL-02 | Balanceador interno con entrada solo desde la lista de prefijos de CloudFront | INFRA | EXISTING | THR-02 | TC-01, TC-04 | T-01 | CWE-284 | — |
| CTL-03 | Content Security Policy con script-src 'self' y build sin scripts inline | WEB | EXISTING | THR-03 | TC-03, TC-07 | T-03, T-05 | ASVS 5.0 V3, CWE-79 | — |
| CTL-04 | X-Frame-Options DENY, frame-ancestors 'none', nosniff y Referrer-Policy | WEB | EXISTING | THR-04 | TC-05 | T-03 | CWE-1021 | — |
| CTL-05 | Rutas del portal reescritas solo en el origen S3; la API conserva sus códigos | WEB, INFRA | EXISTING | THR-05 | TC-02, TC-06 | T-04 | CWE-755 | — |
| CTL-06 | HSTS de un año | WEB | EXISTING | THR-06 | TC-05 | T-03 | CWE-319 | — |
| CTL-07 | Aislamiento entre inquilinos | DATA | NOT APPLICABLE | — | — | — | — | No hay inquilinos en este cambio |

## 10. Cryptography

### CRY-01 · TLS entre el navegador y CloudFront

| Field | Value |
|---|---|
| Protects | DATA-01, DATA-02 |
| Type | TLS |
| Algorithm or service | TLS de CloudFront con el certificado por defecto de cloudfront.net |
| Rationale | Cifra el tramo que cruza internet desde el usuario |
| Key management | AWS administra el certificado por defecto |
| Permissions | Solo AWS |
| Rotation | Automática por AWS |
| Recovery | No aplica; lo reemplaza AWS |
| Failure behavior | El navegador rechaza la conexión; HTTP redirige a HTTPS |
| Tests | TC-05 |

## 11. Secrets and keys

| Secret | Location | Access | Environments | Rotation | Revocation | Leak detection |
|---|---|---|---|---|---|---|
| AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY (sin cambios; aplican este cambio) | Secretos de GitHub | Administradores del repositorio y el job de despliegue | AWS | Manual desde IAM | Desactivar la llave en IAM | sdd scan secrets en cada pull request |

## 12. Authentication, authorization and sessions

N/A: la autenticación, los permisos y las sesiones no cambian.

## 13. Data isolation and multi-tenancy

N/A: no hay inquilinos en este cambio.

## 14. Dependencies

| ID | Dependency | Version | Component | Use | Criticality | Evaluation | Result | Status |
|---|---|---|---|---|---|---|---|---|
| DEP-01 | hashicorp/aws (proveedor de Terraform) | 5.100.0 | terraform | VPC origin, encabezados y función de CloudFront | HIGH | OSV.dev 2026-10-22 | No known vulnerabilities | EVALUATED |

## 15. Risk register and residual risk

| ID | Risk | Threats | Likelihood | Impact | Level | Treatment | Residual risk | Status |
|---|---|---|---|---|---|---|---|---|
| RISK-01 | Sin dominio propio, CloudFront usa su certificado por defecto y no se puede exigir una versión mínima de TLS a los navegadores | THR-06 | LOW | MEDIUM | LOW | ACCEPT | Bajo: los navegadores actuales negocian TLS 1.2 o 1.3; se cierra con un dominio y ACM | ACCEPTED |
| RISK-02 | La CSP permite estilos inline porque Angular inyecta los estilos de los componentes | THR-03 | LOW | MEDIUM | LOW | ACCEPT | Bajo: los scripts siguen limitados al propio origen | ACCEPTED |

## 16. Pending decisions

N/A: el equipo decidió el VPC origin sin dominio el 2026-10-22.
