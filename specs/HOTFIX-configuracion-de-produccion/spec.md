# HOTFIX · Configuracion de produccion

| Field | Value |
|---|---|
| ID | HOTFIX |
| Title | Configuracion de produccion |
| User story | none: hotfix de la revisión de cumplimiento del 2026-10-22 |
| Owner | Juan Camilo Peña |
| Status | IN_REVIEW |
| Created | 2026-10-22 |
| Security profile | HIGH |

## 1. Requirements

### User story

Reporte del incidente (revisión de cumplimiento del 2026-10-22, repositorio público y backend desplegado en AWS desde `main`):

- El backend en AWS firma los tokens con la llave escrita en `backend/app/core/config.py`, publicada en el repositorio; el MAC de los códigos de un solo uso usa la misma llave.
- La variable `db_password` de Terraform tiene un valor por defecto publicado en el repositorio.
- CORS responde a cualquier origen con credenciales.
- `/docs`, `/redoc` y `/openapi.json` se sirven siempre, y el asesor de prueba se siembra en todos los ambientes.
- El canal de socios `/api/v1/quote-edge` cotiza sin autenticación con cualquier `X-Partner-Id`.

Decisiones del equipo (Juan Camilo Peña, 2026-10-22):

- `ENVIRONMENT` sigue sin definirse en AWS: mientras no haya proveedor de SMS, el ambiente entrega el código de prueba, siembra las cuentas de prueba y sirve la documentación.
- Llaves separadas para tokens y códigos, como variables de entorno alimentadas por los secretos de CI; sin gestor de secretos.
- Contraseña de RDS como variable de Terraform alimentada por los secretos de CI.
- No se rotan las credenciales publicadas de las cuentas de prueba ni la contraseña de RDS.
- CORS por lista de orígenes; el canal de socios se apaga.

### Problem and outcome

Cualquiera con acceso al repositorio público puede fabricar tokens de asesor o asegurado para el backend desplegado, y la configuración depende de valores por defecto publicados. Resultado: el backend no arranca sin llaves propias; en AWS las llaves y la contraseña de RDS llegan desde los secretos de CI; CORS solo autoriza orígenes declarados; el canal de socios no se sirve; la depuración (código en la respuesta, cuentas sembradas, documentación) depende solo de `ENVIRONMENT`.

### Goals and non-goals

Objetivos: quitar los valores por defecto de las llaves y de la contraseña, separar la llave del código de un solo uso, cerrar CORS y el canal de socios, y que `ENVIRONMENT` gobierne toda la depuración.

Fuera de alcance: el proveedor de SMS; un gestor de secretos; rotar las credenciales publicadas de las cuentas de prueba y de RDS; HTTPS entre CloudFront y el balanceador (hotfix 2); la autorización por recurso (HU-WEB-05 y HU-WEB-06).

### Affected paths

| Path | Change |
|---|---|
| backend/app/core/config.py | Llaves obligatorias, validación, CORS_ORIGINS, carga sin valores en el error |
| backend/app/core/security.py | Firma con la llave como SecretStr |
| backend/app/modules/identity/service.py | MAC del código con OTP_SECRET_KEY; siembra según ENVIRONMENT |
| backend/app/bff/auth/router.py | Código de prueba según ENVIRONMENT |
| backend/app/main.py | CORS por lista, documentación y siembra del asesor según ENVIRONMENT, canal de socios desmontado |
| backend/tests/** | Pruebas de configuración, CORS, canal de socios y siembra |
| backend/.env.example | Llaves y CORS_ORIGINS |
| terraform/variables.tf | db_password sin valor por defecto; jwt_secret_key y otp_secret_key |
| terraform/main.tf | Pasa las llaves al módulo ECS |
| terraform/modules/ecs/** | Variables y entorno de la tarea |
| terraform/environments/local.tfvars.example | Valores para el emulador local |
| .github/workflows/deploy.yml | TF_VAR_* desde los secretos de CI |
| .github/workflows/destroy.yml | TF_VAR_* desde los secretos de CI |
| docker-compose.yml | El backend lee backend/.env |
| README.md | Secretos de CI y backend/.env |
| docs/adr/0018-terraform-root-and-modules.md | Regla 5: secretos como variables sin valor por defecto |
| sdd/security/critical-paths.md | Rutas críticas propias del proyecto: configuración, seguridad, semillas, sesión móvil, interceptores y scripts |

### Use cases

| ID | Actor | Use case | Main flow | Alternate flows |
|---|---|---|---|---|
| UC-01 | Pipeline de despliegue | Desplegar el backend con sus secretos | 1. Push a main. 2. Terraform recibe TF_VAR_* desde los secretos de CI. 3. ECS arranca la tarea con las llaves y la contraseña | Falta un secreto o es inválido: Terraform falla antes de cambiar nada |
| UC-02 | Desarrollador | Levantar el backend en local | 1. Copia backend/.env.example. 2. Genera las dos llaves. 3. Arranca uvicorn o docker compose | Sin llaves válidas: el backend no arranca y nombra las variables que faltan |
| UC-03 | Asesor o asegurado | Iniciar sesión y usar la API | 1. Inicia sesión. 2. Recibe tokens firmados con la llave del ambiente. 3. Llama la API | Token firmado con otra llave: 401 y nuevo inicio de sesión |

### Abuse cases

| ID | Abuse case | Actor | Threat | Expected response | Test case |
|---|---|---|---|---|---|
| AB-01 | Fabricar un token de asesor con la llave publicada en el repositorio | Atacante externo | THR-01 | 401: el ambiente usa una llave propia | TC-09 |
| AB-02 | Leer la API desde un sitio ajeno usando el navegador de un asesor | Sitio web ajeno | THR-04 | Sin cabeceras CORS: el navegador bloquea la lectura | TC-07 |
| AB-03 | Cotizar por el canal de socios sin credenciales | Atacante externo | THR-05 | 404 | TC-06 |

### Acceptance criteria

| ID | Criterion | Source |
|---|---|---|
| AC-01 | THE backend SHALL leer la llave de los tokens (JWT_SECRET_KEY) y la del código de un solo uso (OTP_SECRET_KEY) de dos variables de entorno distintas, sin valores por defecto en el código | STATED |
| AC-02 | WHEN falta una llave, tiene menos de 32 caracteres o las dos son iguales, THE backend SHALL negarse a arrancar nombrando los campos inválidos sin mostrar ningún valor | DERIVED: la decisión no dice qué pasa si falta una llave; un valor por defecto o el error estándar de Pydantic las expondrían |
| AC-03 | WHEN se despliega en AWS, THE tarea de ECS SHALL recibir JWT_SECRET_KEY, OTP_SECRET_KEY y la contraseña de RDS desde variables de Terraform sin valor por defecto, alimentadas por los secretos de CI | STATED |
| AC-04 | IF falta un secreto de CI o es inválido, THE despliegue y el apagado SHALL fallar antes de cambiar la infraestructura | DERIVED: la decisión no dice cómo se comporta el pipeline sin secretos |
| AC-05 | THE API SHALL autorizar CORS solo para los orígenes de CORS_ORIGINS, ninguno por defecto, y sin credenciales | STATED |
| AC-06 | WHILE ENVIRONMENT no sea production, THE API SHALL servir la documentación interactiva, sembrar el asesor y los asegurados de prueba y devolver el código de prueba; WHEN sea production, no SHALL hacer ninguna de las tres | STATED |
| AC-07 | THE API SHALL dejar de servir el canal de socios /api/v1/quote-edge, que responde 404 | STATED |
| AC-08 | WHEN el ambiente cambia de llave, THE API SHALL rechazar con 401 los tokens firmados con cualquier otra llave | DERIVED: la decisión no dice qué pasa con las sesiones abiertas al cambiar la llave |

### Quality requirements

N/A: cambio de configuración; no altera latencia, disponibilidad ni pantallas.

### Security triggers

| Trigger | Applies | Rationale |
|---|---|---|
| Personal data (identifies or can identify a person) | NO | El cambio maneja llaves y configuración; las cuentas sembradas son ficticias |
| Sensitive data (special categories, biometrics, health, financial, minors) | NO | No hay datos de categorías especiales |
| Authentication, sessions, credentials or one-time codes | YES | Llave de firma de los tokens y llave del MAC del código de un solo uso |
| Authorization or access to other users' resources | NO | Roles y permisos sin cambios; la propiedad por recurso va en HU-WEB-05 y HU-WEB-06 |
| Payments or money movement | NO | No toca pagos |
| Third-party services or integrations | NO | El SMS sigue en console; no se agregan llamadas externas |
| Infrastructure, network, IAM, CI/CD or secrets | YES | Variables de Terraform, entorno de la tarea de ECS y workflows de despliegue y apagado |
| Multiple tenants, partners or organizations | NO | No hay inquilinos; el canal de socios queda apagado |
| Storage or processing on a mobile device | NO | La app no cambia |
| Web UI or data exposed in the browser | YES | Política CORS que aplica el navegador |
| New or updated dependencies | NO | Sin dependencias nuevas ni actualizadas |
| Critical paths (sdd/security/critical-paths.md) | YES | terraform, workflows, identity, auth, docker-compose y .env.example |

### Security requirements

| ID | Requirement | Source | Controls | Priority |
|---|---|---|---|---|
| SR-01 | Las llaves de tokens y de códigos son propias de cada ambiente, de 32 caracteres o más, distintas y sin valor por defecto en el código | DATA-01, DATA-02, DATA-04, DATA-05, THR-01, THR-02 | CTL-01, CTL-02 | HIGH |
| SR-02 | Un error de configuración no muestra valores en la salida ni en los logs | THR-03 | CTL-03 | HIGH |
| SR-03 | La contraseña de RDS y las llaves no tienen valor por defecto en Terraform y llegan desde los secretos cifrados de CI | DATA-03, THR-06 | CTL-04, CTL-05 | HIGH |
| SR-04 | Ningún sitio ajeno puede leer la API desde el navegador | THR-04 | CTL-06 | MEDIUM |
| SR-05 | El canal de socios sin autenticación no se sirve | THR-05 | CTL-07 | MEDIUM |
| SR-06 | La depuración (código en la respuesta, cuentas sembradas, documentación) depende solo de ENVIRONMENT y se apaga con production | DATA-06, THR-07 | CTL-08 | MEDIUM |

## 2. Design

### Components

- `backend/app/core/config.py`: `JWT_SECRET_KEY` y `OTP_SECRET_KEY` como `SecretStr` obligatorias con validación de largo y de diferencia; `CORS_ORIGINS`; la propiedad `debug_enabled`; `load_settings()` que traduce el error a nombres de campo.
- `backend/app/core/security.py` y `backend/app/modules/identity/service.py`: firma con la llave de tokens; MAC del código con la llave propia.
- `backend/app/main.py`: CORS por lista, `docs_urls()`, siembra del asesor con `debug_enabled`, canal de socios desmontado.
- Terraform: `db_password`, `jwt_secret_key` y `otp_secret_key` sensibles, sin valor por defecto y validadas; el módulo ECS las pasa al entorno de la tarea.
- Workflows `deploy.yml` y `destroy.yml`: `TF_VAR_*` desde los secretos de CI.

### Data flows

Secretos cifrados de GitHub → variables `TF_VAR_*` del job de Terraform → estado de Terraform en S3 y definición de tarea de ECS → entorno del contenedor → `Settings` (`SecretStr`) → firma HS256 de tokens y HMAC-SHA256 de códigos. En local: `backend/.env` → `Settings`. El límite de confianza es el paso de GitHub a AWS y la lectura de la configuración al arrancar.

### Data contract

Sin cambios en las respuestas de la API, salvo:

- `/api/v1/quote-edge/*` responde 404.
- Con `ENVIRONMENT=production`, `/docs`, `/redoc` y `/openapi.json` responden 404 y la raíz devuelve `"docs": null`.
- Los orígenes que no estén en `CORS_ORIGINS` no reciben `Access-Control-Allow-Origin`; nunca se envía `Access-Control-Allow-Credentials`.

Variables nuevas: `JWT_SECRET_KEY` y `OTP_SECRET_KEY` (obligatorias, 32 caracteres o más, distintas) y `CORS_ORIGINS` (JSON, opcional).

### Security design decisions

| Decision | Implements | Rejected alternative and why |
|---|---|---|
| Llaves como SecretStr obligatorias y validadas al arrancar | CTL-01, CRY-02 | Un valor por defecto para desarrollo: es justo lo que se filtró |
| Llave propia para el MAC del código | CTL-02, CRY-03 | Reusar la de tokens: una filtración comprometería ambos |
| Error de configuración con nombres de campo, sin valores ni excepción encadenada | CTL-03 | El error estándar de Pydantic: incluye los valores recibidos, que irían a CloudWatch |
| Secretos como variables de entorno desde los secretos de CI | CTL-04, CTL-05, CRY-01 | Gestor de secretos: decisión del equipo por costo y recursos nuevos; queda como objetivo en ADR 0018 |
| CORS por lista y sin credenciales | CTL-06 | El comodín con credenciales: cualquier sitio podía leer respuestas |
| Canal de socios desmontado | CTL-07 | Exigir X-Partner-Id: una cabecera no prueba identidad |
| ENVIRONMENT gobierna toda la depuración | CTL-08 | Banderas separadas: el equipo prefirió una sola variable |

### Architecture decisions

Regla 5 de docs/adr/0018-terraform-root-and-modules.md: los secretos son variables sensibles sin valor por defecto que CI llena desde sus secretos cifrados.

### Configuration and deployment

- Los secretos `DB_PASSWORD`, `JWT_SECRET_KEY` y `OTP_SECRET_KEY` ya existen en GitHub (2026-10-23 UTC; README, sección 8.5). Sin ellos el despliegue falla en la validación de Terraform sin cambiar nada.
- Las llaves de AWS se generan nuevas: reutilizar la llave publicada dejaría abierta la falsificación de tokens (DEC-01).
- Al desplegar, los tokens emitidos con la llave anterior dejan de valer y los usuarios inician sesión de nuevo.
- En local, `backend/.env` debe tener las dos llaves; `docker compose` lo lee con `env_file`.

## 3. Tasks

| ID | Task | Traces to | Controls | Status | Evidence |
|---|---|---|---|---|---|
| T-01 | Llaves obligatorias, validación y carga de configuración sin valores en el error | AC-01, AC-02, SR-01, SR-02 | CTL-01, CTL-03 | DONE | backend/tests/unit/test_config.py::test_tc_01_sin_llaves_no_arranca_y_no_muestra_valores |
| T-02 | Firmar tokens con JWT_SECRET_KEY y el código con OTP_SECRET_KEY | AC-01, AC-08, SR-01 | CTL-02 | DONE | backend/tests/unit/test_config.py::test_tc_04_el_codigo_se_firma_con_la_llave_otp |
| T-03 | CORS por lista; documentación, siembra y código de prueba según ENVIRONMENT; canal de socios desmontado | AC-05, AC-06, AC-07, SR-04, SR-05, SR-06 | CTL-06, CTL-07, CTL-08 | DONE | backend/tests/integration/test_health_and_api.py::test_tc_06_canal_de_socios_desactivado |
| T-04 | Variables de Terraform sin valor por defecto, validadas, y entorno de la tarea de ECS | AC-03, AC-04, SR-03 | CTL-04 | DONE | terraform/variables.tf |
| T-05 | TF_VAR_* desde los secretos de CI en deploy y destroy | AC-03, AC-04, SR-03 | CTL-05 | DONE | .github/workflows/deploy.yml |
| T-06 | Configuración local: backend/.env.example, docker-compose y README | AC-02 | — | DONE | backend/.env.example |
| T-08 | Registrar las rutas críticas propias del proyecto para que un cambio en ellas exija un spec | SR-01, SR-03 | CTL-01, CTL-05 | DONE | sdd/security/critical-paths.md |
| T-07 | Crear en GitHub DB_PASSWORD, JWT_SECRET_KEY y OTP_SECRET_KEY con llaves nuevas antes de fusionar a main | SR-01, SR-03 | CTL-05 | DONE | gh secret list: los tres secretos creados el 2026-10-23 UTC; las llaves se generaron nuevas sin mostrarse y DB_PASSWORD conserva el valor actual |
