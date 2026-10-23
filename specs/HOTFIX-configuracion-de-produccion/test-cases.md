# Test cases · HOTFIX

## Scenarios

| ID | From | Scenario | Disposition |
|---|---|---|---|
| SC-01 | UC-01 | Dado que existen DB_PASSWORD, JWT_SECRET_KEY y OTP_SECRET_KEY en GitHub, cuando se hace push a main, entonces la tarea arranca con esas llaves y esa contraseña | TC-12 |
| SC-02 | UC-01 | Dado que falta un secreto o una llave es corta, cuando corre el despliegue o el apagado, entonces Terraform falla en la validación sin cambiar nada | TC-10 |
| SC-03 | UC-02 | Dado un backend/.env sin llaves, cuando el desarrollador arranca el backend, entonces no arranca y el error nombra JWT_SECRET_KEY y OTP_SECRET_KEY sin mostrar valores | TC-01 |
| SC-04 | AC-02 | Dada una llave de 31 caracteres, cuando arranca el backend, entonces se rechaza; con 32 arranca | TC-02 |
| SC-05 | AC-02 | Dadas dos llaves iguales, cuando arranca el backend, entonces se rechaza sin mostrarlas | TC-03 |
| SC-06 | UC-03 | Dado un token de asesor firmado con la llave publicada, cuando llama una ruta de asesor, entonces recibe 401 | TC-09 |
| SC-07 | UC-03 | Dadas sesiones abiertas antes del despliegue, cuando el ambiente cambia de llave, entonces los tokens anteriores reciben 401 y el usuario inicia sesión de nuevo | TC-09 |
| SC-08 | UC-03 | Dado un código pedido antes del despliegue, cuando se valida después, entonces no coincide y el usuario pide otro | OUT OF SCOPE: equivale a un código vencido (duran 5 minutos), ya cubierto por las pruebas de HU-MOV-02 |
| SC-09 | UC-03 | Dados un asesor y un asegurado con sesión, cuando cambia la llave, entonces los dos roles deben iniciar sesión de nuevo | TC-09 |
| SC-10 | UC-01 | Dadas dos tareas de ECS, cuando una emite un token, entonces la otra lo acepta | OUT OF SCOPE: ambas tareas usan la misma definición y el mismo entorno; no hay valores por tarea |
| SC-11 | AC-05 | Dado un sitio ajeno, cuando el navegador consulta la API, entonces no recibe permiso CORS | TC-07 |
| SC-12 | AC-07 | Dado un cliente con o sin X-Partner-Id, cuando llama al canal de socios, entonces recibe 404 | TC-06 |
| SC-13 | AC-06 | Dado ENVIRONMENT=production, cuando arranca el backend, entonces no siembra cuentas ni sirve la documentación | TC-05, TC-08 |
| SC-14 | UC-02 | Dado docker compose sin backend/.env, cuando se levanta el backend, entonces compose falla indicando el archivo que falta | OUT OF SCOPE: es el comportamiento estándar de env_file en Docker Compose; el README indica crear el archivo |

## Scenario coverage

| Kind | Applies | Scenarios | Rationale |
|---|---|---|---|
| Main flow | YES | SC-01, SC-03 | — |
| Alternate flows | YES | SC-10, SC-14 | — |
| Invalid input and errors | YES | SC-02, SC-03, SC-05 | — |
| Limits and boundaries | YES | SC-04 | — |
| Related flows before and after | YES | SC-02, SC-07, SC-08 | — |
| Several users, sessions, devices or roles | YES | SC-09, SC-10 | — |
| State and time (expiry, retries, interruptions, going back, offline) | YES | SC-07, SC-08, SC-13 | — |

## Test cases

### TC-01 · Sin llaves no arranca y no muestra valores

| Field | Value |
|---|---|
| Covers | AC-02, SR-01, SR-02 |
| Kind | SECURITY |
| Risk covered | THR-03 |
| Level | UNIT |
| Preconditions | Entorno sin JWT_SECRET_KEY ni OTP_SECRET_KEY y con un valor canario en DB_PASSWORD |
| Procedure | 1. Cargar la configuración. 2. Revisar el mensaje y la cadena de la excepción |
| Expected result | RuntimeError que nombra las dos llaves, sin el canario y sin excepción encadenada |
| Tool or method | pytest backend/tests/unit/test_config.py::test_tc_01_sin_llaves_no_arranca_y_no_muestra_valores |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_config.py::test_tc_01_sin_llaves_no_arranca_y_no_muestra_valores; suite del backend 2026-10-22 en local, 189 pruebas OK |
| Status | PASS |

### TC-02 · Llave corta rechazada y mínima aceptada

| Field | Value |
|---|---|
| Covers | AC-02, SR-01 |
| Kind | SECURITY |
| Risk covered | THR-01 |
| Level | UNIT |
| Preconditions | Llaves aleatorias generadas en la prueba |
| Procedure | 1. Cargar con una llave de 31 caracteres. 2. Cargar con una de 32 |
| Expected result | La de 31 se rechaza sin mostrarla; la de 32 se acepta |
| Tool or method | pytest backend/tests/unit/test_config.py::test_tc_02_llave_corta_se_rechaza_y_la_minima_se_acepta |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_config.py::test_tc_02_llave_corta_se_rechaza_y_la_minima_se_acepta en la corrida local |
| Status | PASS |

### TC-03 · Llaves iguales rechazadas

| Field | Value |
|---|---|
| Covers | AC-02, SR-01 |
| Kind | SECURITY |
| Risk covered | THR-02 |
| Level | UNIT |
| Preconditions | Una sola llave aleatoria usada para las dos variables |
| Procedure | 1. Cargar la configuración. 2. Revisar el mensaje |
| Expected result | Error que pide llaves distintas, sin mostrar la llave |
| Tool or method | pytest backend/tests/unit/test_config.py::test_tc_03_llaves_iguales_se_rechazan |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_config.py::test_tc_03_llaves_iguales_se_rechazan en la corrida local |
| Status | PASS |

### TC-04 · El código se firma con la llave del código

| Field | Value |
|---|---|
| Covers | AC-01, SR-01 |
| Kind | SECURITY |
| Risk covered | THR-02 |
| Level | UNIT |
| Preconditions | Llaves de prueba generadas en tiempo de ejecución |
| Procedure | 1. Calcular el MAC del código. 2. Compararlo con HMAC-SHA256 con cada llave |
| Expected result | Coincide con la llave del código y no con la de tokens |
| Tool or method | pytest backend/tests/unit/test_config.py::test_tc_04_el_codigo_se_firma_con_la_llave_otp |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_config.py::test_tc_04_el_codigo_se_firma_con_la_llave_otp en la corrida local |
| Status | PASS |

### TC-05 · CORS y documentación según la configuración

| Field | Value |
|---|---|
| Covers | AC-05, AC-06, SR-06 |
| Kind | SECURITY |
| Risk covered | THR-07 |
| Level | UNIT |
| Preconditions | Configuración cargada con y sin CORS_ORIGINS y ENVIRONMENT |
| Procedure | 1. Cargar sin CORS_ORIGINS y con una lista. 2. Cargar con ENVIRONMENT=production y sin definir. 3. Pedir las rutas de documentación |
| Expected result | Lista vacía por defecto; depuración apagada solo con production; documentación sin rutas cuando está apagada |
| Tool or method | pytest backend/tests/unit/test_config.py::test_tc_05_cors_y_documentacion_segun_configuracion |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_config.py::test_tc_05_cors_y_documentacion_segun_configuracion en la corrida local |
| Status | PASS |

### TC-06 · Canal de socios desactivado

| Field | Value |
|---|---|
| Covers | AC-07, SR-05 |
| Kind | SECURITY |
| Risk covered | THR-05 |
| Level | INTEGRATION |
| Preconditions | API en proceso con la sesión de prueba |
| Procedure | 1. Llamar quote-edge sin cabecera. 2. Llamarlo con X-Partner-Id |
| Expected result | 404 en los dos casos |
| Tool or method | pytest backend/tests/integration/test_health_and_api.py::test_tc_06_canal_de_socios_desactivado |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_health_and_api.py::test_tc_06_canal_de_socios_desactivado en la corrida local |
| Status | PASS |

### TC-07 · CORS no autoriza orígenes ajenos

| Field | Value |
|---|---|
| Covers | AC-05, SR-04 |
| Kind | SECURITY |
| Risk covered | THR-04 |
| Level | INTEGRATION |
| Preconditions | API en proceso sin CORS_ORIGINS |
| Procedure | 1. Enviar un preflight desde un origen ajeno. 2. Enviar una solicitud simple desde ese origen |
| Expected result | Ninguna respuesta trae Access-Control-Allow-Origin ni Access-Control-Allow-Credentials |
| Tool or method | pytest backend/tests/integration/test_health_and_api.py::test_tc_07_cors_no_autoriza_origenes_ajenos |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_health_and_api.py::test_tc_07_cors_no_autoriza_origenes_ajenos en la corrida local |
| Status | PASS |

### TC-08 · Con production no se siembran cuentas

| Field | Value |
|---|---|
| Covers | AC-06, SR-06 |
| Kind | SECURITY |
| Risk covered | THR-07 |
| Level | INTEGRATION |
| Preconditions | PostgreSQL de pruebas vacío y ENVIRONMENT=production |
| Procedure | 1. Ejecutar el arranque del backend. 2. Consultar asesores y asegurados |
| Expected result | Ninguna cuenta sembrada |
| Tool or method | pytest backend/tests/integration/test_lifespan.py::test_tc_08_con_environment_production_no_siembra_cuentas |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_lifespan.py::test_tc_08_con_environment_production_no_siembra_cuentas en la corrida local con PostgreSQL |
| Status | PASS |

### TC-09 · Token firmado con otra llave rechazado

| Field | Value |
|---|---|
| Covers | AC-08, SR-01 |
| Kind | SECURITY |
| Risk covered | THR-01 |
| Level | INTEGRATION |
| Preconditions | API en proceso; un token de asesor firmado con una llave aleatoria y otro con la del ambiente |
| Procedure | 1. Llamar una ruta de asesor con el token ajeno. 2. Llamarla con el token válido |
| Expected result | 401 con el token ajeno; el válido no recibe 401 |
| Tool or method | pytest backend/tests/integration/test_health_and_api.py::test_tc_09_token_firmado_con_otra_llave_es_rechazado |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/integration/test_health_and_api.py::test_tc_09_token_firmado_con_otra_llave_es_rechazado en la corrida local |
| Status | PASS |

### TC-10 · Terraform rechaza secretos faltantes o inválidos

| Field | Value |
|---|---|
| Covers | AC-03, AC-04, SR-03 |
| Kind | SECURITY |
| Risk covered | THR-06 |
| Level | STATIC |
| Preconditions | Copia temporal de terraform/ con backend local y credenciales de AWS falsas |
| Procedure | 1. terraform validate. 2. terraform plan con una contraseña corta y llaves de un carácter. 3. terraform plan con valores válidos |
| Expected result | La configuración es válida; el plan con valores inválidos falla en la validación de variables; con valores válidos no hay error de validación |
| Tool or method | Terraform 1.14.9 en local (validate y plan) |
| Automation | MANUAL |
| Environment | LOCAL |
| Evidence | Corrida local del 2026-10-22: validate OK; el plan inválido falla con Invalid value for variable en db_password y jwt_secret_key; el válido solo falla al consultar STS con credenciales falsas |
| Status | PASS |

### TC-11 · Contraseñas sembradas con hash

| Field | Value |
|---|---|
| Covers | SR-06 |
| Kind | SECURITY |
| Risk covered | THR-07 |
| Level | UNIT |
| Preconditions | Servicio de autenticación de asesores |
| Procedure | 1. Generar el hash de una contraseña. 2. Verificarla con la correcta y con otra |
| Expected result | El hash no es la contraseña y solo verifica la correcta |
| Tool or method | pytest backend/tests/unit/test_auth_service.py::test_bcrypt_hashing_and_verification |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | backend/tests/unit/test_auth_service.py::test_bcrypt_hashing_and_verification en la corrida local |
| Status | PASS |

### TC-12 · Despliegue con los secretos de CI

| Field | Value |
|---|---|
| Covers | AC-03, SR-03 |
| Kind | SECURITY |
| Risk covered | THR-06 |
| Level | E2E |
| Preconditions | Secretos DB_PASSWORD, JWT_SECRET_KEY y OTP_SECRET_KEY creados en GitHub con llaves nuevas (T-07); cambio fusionado a main |
| Procedure | 1. Esperar el workflow de despliegue. 2. Consultar /health. 3. Iniciar sesión como asesor de prueba. 4. Repetir una llamada con un token emitido antes del despliegue |
| Expected result | El despliegue termina, /health responde 200, el inicio de sesión funciona y el token anterior recibe 401 |
| Tool or method | Workflow de despliegue y llamadas con un cliente HTTP |
| Automation | MANUAL |
| Environment | DEV |
| Evidence | PENDING |
| Status | PENDING |

### TC-13 · Sin secretos en el cambio

| Field | Value |
|---|---|
| Covers | SR-01, SR-03 |
| Kind | SECURITY |
| Risk covered | THR-01 |
| Level | STATIC |
| Preconditions | Rama del hotfix |
| Procedure | 1. python sdd/tools/sdd.py scan secrets --diff origin/dev |
| Expected result | 0 posibles secretos en las líneas nuevas |
| Tool or method | python sdd/tools/sdd.py scan secrets --diff origin/dev |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | Corrida local del 2026-10-22: 0 posibles secretos |
| Status | PASS |

## Security test coverage

| Category | Applies | Test cases | Rationale |
|---|---|---|---|
| Unauthenticated user | YES | TC-06 | — |
| User without permissions | NO | — | Los permisos no cambian |
| Access to another user's resources | NO | — | Sin cambios; la propiedad por recurso va en HU-WEB-05 y HU-WEB-06 |
| Cross-tenant access | NO | — | No hay inquilinos |
| Malicious input | YES | TC-07 | — |
| Expired tokens | NO | — | Los vencimientos no cambian |
| Revoked sessions | YES | TC-09 | — |
| Tampered data | YES | TC-09 | — |
| Wrong keys | YES | TC-02, TC-03, TC-04 | — |
| External service failures | NO | — | No se agregan servicios externos |
| Race conditions | NO | — | No se agrega estado compartido |
| Information exposure | YES | TC-01, TC-05 | — |
| Secrets in code | YES | TC-13 | — |
| Insecure configuration | YES | TC-05, TC-07, TC-10 | — |
| Vulnerable dependencies | NO | — | Sin dependencias nuevas; las críticas se evaluaron en OSV.dev (DEP-01 a DEP-03) |
