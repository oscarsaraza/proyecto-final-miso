# Test cases · HOTFIX

## Scenarios

| ID | From | Scenario | Disposition |
|---|---|---|---|
| SC-01 | UC-02 | Dado el cambio desplegado, cuando el portal llama /api/* por CloudFront, entonces la solicitud llega al balanceador interno y responde | TC-04 |
| SC-02 | UC-02 | Dado alguien en internet, cuando intenta conectarse al DNS del balanceador, entonces resuelve a una IP privada y no conecta | TC-04 |
| SC-03 | UC-02 | Dado un endpoint inexistente, cuando se llama por CloudFront, entonces llega el 404 de la API y no index.html | TC-06 |
| SC-04 | UC-01 | Dado un asesor, cuando recarga /cotizador o abre /login directamente, entonces recibe el portal | TC-02, TC-06 |
| SC-05 | UC-01 | Dado un archivo del portal que no existe, cuando se pide, entonces CloudFront responde el error de S3 y no index.html | TC-02 |
| SC-06 | UC-01 | Dado el portal con la CSP, cuando el asesor inicia sesión y cotiza, entonces la consola no muestra bloqueos | TC-07 |
| SC-07 | UC-01 | Dado un sitio ajeno, cuando intenta mostrar el portal en un iframe, entonces el navegador lo bloquea | TC-05 |
| SC-08 | UC-03 | Dado el despliegue, cuando Terraform recrea el balanceador, entonces la API queda unos minutos sin servicio y vuelve sola | TC-04 |
| SC-09 | UC-03 | Dada la configuración, cuando se valida con Terraform, entonces el balanceador es interno y el origen es un VPC origin | TC-01 |
| SC-10 | UC-02 | Dadas varias tareas de ECS, cuando se recrea el balanceador, entonces todas se registran en el nuevo | OUT OF SCOPE: el grupo de destino no se recrea y ECS lo mantiene; se observa en TC-04 |
| SC-11 | UC-01 | Dado un navegador que visitó el portal, cuando vuelve a escribir la URL con http, entonces usa HTTPS | TC-05 |
| SC-12 | UC-01 | Dada una visita sin conexión estable, cuando falla una solicitud a la API, entonces el portal muestra su error y no una página en blanco | OUT OF SCOPE: depende del manejo de errores del portal, que no cambia aquí |

## Scenario coverage

| Kind | Applies | Scenarios | Rationale |
|---|---|---|---|
| Main flow | YES | SC-01, SC-06 | — |
| Alternate flows | YES | SC-04 | — |
| Invalid input and errors | YES | SC-03, SC-05 | — |
| Limits and boundaries | YES | SC-02, SC-07 | — |
| Related flows before and after | YES | SC-08, SC-09 | — |
| Several users, sessions, devices or roles | YES | SC-10 | — |
| State and time (expiry, retries, interruptions, going back, offline) | YES | SC-08, SC-11, SC-12 | — |

## Test cases

### TC-01 · Configuración de Terraform

| Field | Value |
|---|---|
| Covers | AC-01, AC-02, SR-01, SR-02 |
| Kind | SECURITY |
| Risk covered | THR-01, THR-02 |
| Level | STATIC |
| Preconditions | Copia temporal de terraform/ inicializada sin backend |
| Procedure | 1. terraform validate. 2. Revisar internal, subredes, ingreso del grupo de seguridad y vpc_origin_config |
| Expected result | La configuración es válida; balanceador interno en subredes privadas, ingreso solo desde la lista de CloudFront y origen por VPC origin |
| Tool or method | Terraform 1.14.9 en local |
| Automation | MANUAL |
| Environment | LOCAL |
| Evidence | Corrida local del 2026-10-22: Success! The configuration is valid; terraform fmt sin cambios en los archivos tocados |
| Status | PASS |

### TC-02 · Función de rutas del portal

| Field | Value |
|---|---|
| Covers | AC-04, AC-05, SR-05 |
| Kind | SECURITY |
| Risk covered | THR-05 |
| Level | UNIT |
| Preconditions | Node.js local |
| Procedure | 1. Ejecutar el handler con /, /login y /cotizador. 2. Ejecutarlo con /main.js, /favicon.ico y /assets/logo.svg |
| Expected result | Las rutas sin extensión van a /index.html; los archivos conservan su ruta |
| Tool or method | node con terraform/modules/web_hosting/spa-routing.js |
| Automation | MANUAL |
| Environment | LOCAL |
| Evidence | Corrida local del 2026-10-22: /login y /cotizador van a /index.html; los archivos conservan su ruta |
| Status | PASS |

### TC-03 · Build del portal sin scripts inline

| Field | Value |
|---|---|
| Covers | AC-06, SR-03 |
| Kind | SECURITY |
| Risk covered | THR-03 |
| Level | STATIC |
| Preconditions | Dependencias del portal instaladas |
| Procedure | 1. npm run build. 2. Buscar etiquetas script sin src en dist/web/browser/index.html |
| Expected result | Solo el script main con src; ninguno inline |
| Tool or method | npm run build y búsqueda en index.html |
| Automation | MANUAL |
| Environment | LOCAL |
| Evidence | Corrida local del 2026-10-22: un solo script con src=main y cero scripts inline |
| Status | PASS |

### TC-04 · Balanceador privado detrás de CloudFront

| Field | Value |
|---|---|
| Covers | AC-01, AC-02, SR-01, SR-02 |
| Kind | SECURITY |
| Risk covered | THR-01, THR-02 |
| Level | E2E |
| Preconditions | Cambio fusionado a main y desplegado |
| Procedure | 1. Resolver el DNS del balanceador. 2. Intentar conectar al puerto 80 desde fuera de AWS. 3. Llamar /health y /api/v1/experience/catalogs/cities por CloudFront |
| Expected result | El DNS resuelve a IP privadas y no hay conexión; por CloudFront /health responde 200 y la API responde |
| Tool or method | nslookup y un cliente HTTP |
| Automation | MANUAL |
| Environment | DEV |
| Evidence | PENDING |
| Status | PENDING |

### TC-05 · Encabezados de seguridad

| Field | Value |
|---|---|
| Covers | AC-03, SR-04, SR-06 |
| Kind | SECURITY |
| Risk covered | THR-04, THR-06 |
| Level | E2E |
| Preconditions | Cambio desplegado |
| Procedure | 1. Pedir / y /health por CloudFront. 2. Revisar los encabezados de la respuesta |
| Expected result | Strict-Transport-Security, Content-Security-Policy, X-Content-Type-Options, X-Frame-Options DENY y Referrer-Policy presentes |
| Tool or method | curl -I contra la URL de CloudFront |
| Automation | MANUAL |
| Environment | DEV |
| Evidence | PENDING |
| Status | PENDING |

### TC-06 · Códigos reales de la API y rutas del portal

| Field | Value |
|---|---|
| Covers | AC-04, AC-05, SR-05 |
| Kind | SECURITY |
| Risk covered | THR-05 |
| Level | E2E |
| Preconditions | Cambio desplegado |
| Procedure | 1. GET /api/v1/no-existe. 2. GET /cotizador |
| Expected result | 404 con cuerpo JSON de la API; /cotizador devuelve el portal |
| Tool or method | curl contra la URL de CloudFront |
| Automation | MANUAL |
| Environment | DEV |
| Evidence | PENDING |
| Status | PENDING |

### TC-07 · El portal funciona con la CSP

| Field | Value |
|---|---|
| Covers | AC-03, AC-06, SR-03 |
| Kind | SECURITY |
| Risk covered | THR-03 |
| Level | E2E |
| Preconditions | Cambio desplegado; cuenta de asesor de prueba |
| Procedure | 1. Abrir el portal con la consola del navegador abierta. 2. Iniciar sesión. 3. Hacer una cotización |
| Expected result | El portal se ve con sus estilos y fuentes, el flujo funciona y la consola no muestra bloqueos de la CSP |
| Tool or method | Navegador con herramientas de desarrollo |
| Automation | MANUAL |
| Environment | DEV |
| Evidence | PENDING |
| Status | PENDING |

### TC-08 · Sin secretos en el cambio

| Field | Value |
|---|---|
| Covers | SR-02 |
| Kind | SECURITY |
| Risk covered | THR-02 |
| Level | STATIC |
| Preconditions | Rama del hotfix |
| Procedure | 1. python sdd/tools/sdd.py scan secrets --diff origin/dev |
| Expected result | 0 posibles secretos |
| Tool or method | python sdd/tools/sdd.py scan secrets --diff origin/dev |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | Corrida local del 2026-10-22: 0 posibles secretos |
| Status | PASS |

## Security test coverage

| Category | Applies | Test cases | Rationale |
|---|---|---|---|
| Unauthenticated user | NO | — | La autenticación no cambia |
| User without permissions | NO | — | Los permisos no cambian |
| Access to another user's resources | NO | — | Sin cambios de autorización |
| Cross-tenant access | NO | — | No hay inquilinos |
| Malicious input | YES | TC-07 | — |
| Expired tokens | NO | — | Los tokens no cambian |
| Revoked sessions | NO | — | Las sesiones no cambian |
| Tampered data | NO | — | No hay datos firmados nuevos |
| Wrong keys | NO | — | No hay llaves nuevas |
| External service failures | NO | — | Sin servicios externos nuevos |
| Race conditions | NO | — | Sin estado compartido nuevo |
| Information exposure | YES | TC-04, TC-06 | — |
| Secrets in code | YES | TC-08 | — |
| Insecure configuration | YES | TC-01, TC-05 | — |
| Vulnerable dependencies | NO | — | Mismo proveedor bloqueado, evaluado en OSV.dev (DEP-01) |
