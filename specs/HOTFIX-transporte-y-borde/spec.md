# HOTFIX · Transporte y borde

| Field | Value |
|---|---|
| ID | HOTFIX |
| Title | Transporte y borde |
| User story | none: hotfix de la revisión de cumplimiento del 2026-10-22 |
| Owner | Juan Camilo Peña |
| Status | IN_REVIEW |
| Created | 2026-10-22 |
| Security profile | HIGH |

## 1. Requirements

### User story

Reporte del incidente (revisión de cumplimiento del 2026-10-22):

- Entre CloudFront y el balanceador todo viaja por HTTP público: tokens, contraseñas, códigos y datos personales.
- El balanceador es público, con un grupo de seguridad abierto a internet en 80 y 443, así que cualquiera lo llama sin pasar por CloudFront y llega a `/docs`.
- CloudFront no envía encabezados de seguridad y el portal no tiene Content Security Policy.
- CloudFront convierte los 403 y 404 de toda la distribución, incluida `/api/*`, en `index.html` con 200.

Decisión del equipo (Juan Camilo Peña, 2026-10-22): sin dominio propio por ahora; el balanceador pasa a ser interno y CloudFront llega a él con un VPC origin.

### Problem and outcome

Los datos sensibles cruzan internet sin cifrar y el backend se puede llamar saltándose CloudFront. Resultado: el balanceador es privado y solo CloudFront llega a él por la red de AWS; todas las respuestas llevan encabezados de seguridad; la API entrega sus códigos reales y el portal sigue funcionando con enlaces directos.

### Goals and non-goals

Objetivos: quitar el tramo HTTP por internet y la entrada pública al balanceador; encabezados de seguridad y CSP; códigos de error reales de la API.

Fuera de alcance: dominio propio con certificado ACM y TLS 1.2 mínimo para los navegadores; restringir la salida de los grupos de seguridad; protección contra borrado y registros de acceso del balanceador.

### Affected paths

| Path | Change |
|---|---|
| terraform/main.tf | El balanceador recibe las subredes privadas; CloudFront recibe su ARN |
| terraform/modules/alb/** | Balanceador interno y entrada solo desde la lista de prefijos de CloudFront |
| terraform/modules/web_hosting/** | VPC origin, política de encabezados, función de rutas del portal, sin conversión de errores |
| web/angular.json | Build de producción sin CSS crítico inline, para que la CSP no bloquee scripts |
| docs/adr/** | ADR 0020 y notas en la ADR 0018 y el índice |
| AGENTS.md | Rango de ADR de Terraform |

### Use cases

| ID | Actor | Use case | Main flow | Alternate flows |
|---|---|---|---|---|
| UC-01 | Asesor | Usar el portal | 1. Abre la URL de CloudFront. 2. El navegador recibe el portal con sus encabezados. 3. Navega a /login o /cotizador | Recarga o enlace directo a una ruta del portal: recibe index.html |
| UC-02 | Portal o app | Llamar la API | 1. Llama /api/* en CloudFront. 2. CloudFront la envía al balanceador interno por el VPC origin. 3. Recibe la respuesta con su código real | Error de la API: recibe el 4xx o 5xx real, no index.html |
| UC-03 | Pipeline de despliegue | Aplicar el cambio | 1. Push a main. 2. Terraform recrea el balanceador como interno y crea el VPC origin. 3. ECS registra las tareas en el balanceador nuevo | Fallo al aplicar: la distribución conserva su configuración anterior |

### Abuse cases

| ID | Abuse case | Actor | Threat | Expected response | Test case |
|---|---|---|---|---|---|
| AB-01 | Llamar al balanceador directamente para saltarse CloudFront y leer /docs | Atacante externo | THR-02 | Sin dirección pública: no hay conexión | TC-04 |
| AB-02 | Interceptar tokens entre CloudFront y el backend | Atacante en la red | THR-01 | El tramo no pasa por internet | TC-04 |
| AB-03 | Inyectar un script en el portal para robar la sesión | Atacante externo | THR-03 | La CSP bloquea scripts que no son del propio origen | TC-07 |

### Acceptance criteria

| ID | Criterion | Source |
|---|---|---|
| AC-01 | THE balanceador SHALL ser interno, en subredes privadas, y aceptar tráfico solo desde CloudFront | STATED |
| AC-02 | THE CloudFront SHALL llegar al balanceador mediante un VPC origin, sin cruzar internet | STATED |
| AC-03 | THE CloudFront SHALL responder con HSTS, Content Security Policy, nosniff, X-Frame-Options DENY y Referrer-Policy | STATED |
| AC-04 | WHEN la API responde un error, THE CloudFront SHALL entregar ese código y ese cuerpo sin reemplazarlos por index.html | STATED |
| AC-05 | WHEN se pide una ruta del portal sin extensión o se recarga, THE CloudFront SHALL servir index.html | DERIVED: quitar la conversión global de errores rompería los enlaces directos del portal |
| AC-06 | THE build de producción del portal SHALL no tener scripts inline | DERIVED: la CSP estricta bloquearía el script que Angular inserta para el CSS crítico y el portal quedaría sin estilos |

### Quality requirements

N/A: no cambia latencia, disponibilidad esperada ni pantallas; el despliegue deja unos minutos sin API, que se anotan en Configuration and deployment.

### Security triggers

| Trigger | Applies | Rationale |
|---|---|---|
| Personal data (identifies or can identify a person) | YES | Los datos de clientes y asegurados viajan por el tramo que se protege |
| Sensitive data (special categories, biometrics, health, financial, minors) | NO | No hay categorías especiales en las solicitudes |
| Authentication, sessions, credentials or one-time codes | NO | La autenticación no cambia; solo el transporte de lo que ya existe |
| Authorization or access to other users' resources | NO | Los permisos no cambian |
| Payments or money movement | NO | No toca pagos |
| Third-party services or integrations | NO | Sin servicios externos nuevos |
| Infrastructure, network, IAM, CI/CD or secrets | YES | Balanceador, grupos de seguridad y CloudFront |
| Multiple tenants, partners or organizations | NO | No hay inquilinos |
| Storage or processing on a mobile device | NO | La app no cambia |
| Web UI or data exposed in the browser | YES | Encabezados de seguridad, CSP y rutas del portal |
| New or updated dependencies | NO | Mismo proveedor de AWS bloqueado (5.100.0) |
| Critical paths (sdd/security/critical-paths.md) | YES | terraform/** |

### Security requirements

| ID | Requirement | Source | Controls | Priority |
|---|---|---|---|---|
| SR-01 | Los datos personales, las credenciales y los tokens no cruzan internet sin cifrar entre CloudFront y el backend | DATA-01, DATA-02, THR-01 | CTL-01 | HIGH |
| SR-02 | El backend solo se alcanza a través de CloudFront | THR-02 | CTL-02 | HIGH |
| SR-03 | El portal no ejecuta scripts que no vengan de su propio origen | THR-03 | CTL-03 | MEDIUM |
| SR-04 | El portal no se puede embeber en sitios ajenos y el navegador no reinterpreta los tipos de contenido | THR-04 | CTL-04 | LOW |
| SR-05 | La API conserva sus códigos de estado a través de CloudFront | THR-05 | CTL-05 | MEDIUM |
| SR-06 | El navegador vuelve siempre por HTTPS | THR-06 | CTL-06 | LOW |

## 2. Design

### Components

- `terraform/modules/alb`: `internal = true` en las subredes privadas; entrada en 80 solo desde la lista administrada `com.amazonaws.global.cloudfront.origin-facing`.
- `terraform/modules/web_hosting`:
  - `aws_cloudfront_vpc_origin` hacia el balanceador;
  - `aws_cloudfront_response_headers_policy` en los tres comportamientos;
  - `aws_cloudfront_function` (`spa-routing.js`) en el comportamiento de S3;
  - se eliminan los `custom_error_response`.
- `web/angular.json`: `inlineCritical: false` en producción.

### Data flows

Navegador o app → CloudFront (TLS) → VPC origin por la red privada de AWS → balanceador interno → tareas de ECS. El portal se sirve desde S3 por OAC. El límite de confianza es CloudFront: ya no hay otra entrada al backend.

### Data contract

Las rutas de la API no cambian. Cambian tres cosas:

- Los errores de `/api/*` llegan con su código real en lugar de 200 con HTML.
- Las rutas del portal sin extensión se sirven como index.html.
- Todas las respuestas traen HSTS, CSP, X-Content-Type-Options, X-Frame-Options y Referrer-Policy.

### Security design decisions

| Decision | Implements | Rejected alternative and why |
|---|---|---|
| Balanceador interno con VPC origin | CTL-01, CTL-02 | Dominio con ACM: el equipo no tiene dominio aún; queda para una ADR posterior |
| Entrada solo desde la lista de prefijos de CloudFront | CTL-02 | Abierto a internet: permitía saltarse CloudFront |
| CSP con script-src 'self' y build sin scripts inline | CTL-03 | script-src 'unsafe-inline': anulaba la protección contra inyección de scripts |
| Función de rutas solo en el comportamiento de S3 | CTL-05 | Respuestas de error personalizadas: aplican a toda la distribución, API incluida |
| HSTS sin includeSubDomains ni preload | CTL-06 | Preload: no aplica a un subdominio de cloudfront.net |

### Architecture decisions

docs/adr/0020-private-load-balancer-behind-cloudfront.md

### Configuration and deployment

- Aplicar el cambio recrea el balanceador: unos minutos sin API mientras ECS registra las tareas en el nuevo.
- La VPC conserva su internet gateway, que los VPC origins requieren.
- El balanceador ya no se puede llamar desde fuera de la VPC; las pruebas van por la URL de CloudFront.

## 3. Tasks

| ID | Task | Traces to | Controls | Status | Evidence |
|---|---|---|---|---|---|
| T-01 | Balanceador interno en subredes privadas con entrada solo desde CloudFront | AC-01, SR-02 | CTL-02 | DONE | terraform/modules/alb/main.tf |
| T-02 | VPC origin de CloudFront hacia el balanceador | AC-02, SR-01 | CTL-01 | DONE | terraform/modules/web_hosting/main.tf |
| T-03 | Política de encabezados de seguridad con CSP en los tres comportamientos | AC-03, SR-03, SR-04, SR-06 | CTL-03, CTL-04, CTL-06 | DONE | terraform/modules/web_hosting/main.tf |
| T-04 | Función de rutas del portal y fin de la conversión global de errores | AC-04, AC-05, SR-05 | CTL-05 | DONE | terraform/modules/web_hosting/spa-routing.js |
| T-05 | Build de producción del portal sin scripts inline | AC-06, SR-03 | CTL-03 | DONE | web/angular.json |
| T-06 | ADR 0020 | AC-01, AC-02 | — | DONE | docs/adr/0020-private-load-balancer-behind-cloudfront.md |
