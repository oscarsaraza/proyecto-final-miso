# Test cases · HU-MOV-04

## Scenarios

| ID | From | Scenario | Disposition |
|---|---|---|---|
| SC-01 | UC-01 | Dado un asegurado con red y pólizas vigentes, cuando abre la billetera, entonces ve una tarjeta por póliza y queda la copia de su cuenta | TC-04 |
| SC-02 | AC-10 | Dado un titular con pólizas ACTIVE, ISSUED, vencidas y canceladas, cuando consulta, entonces solo recibe las ACTIVE con vigencia futura | TC-01 |
| SC-03 | AC-10 | Dada una póliza cuya vigencia termina justo en el instante de la consulta, cuando consulta, entonces no se devuelve | TC-01 |
| SC-04 | AC-13 | Dado un asegurado sin pólizas vigentes, cuando abre la billetera, entonces ve que no tiene pólizas vigentes y no se guarda copia con datos | TC-04 |
| SC-05 | UC-02 | Dado un asegurado sin red y con copia, cuando entra con su huella, entonces ve la copia con el aviso "Sin conexión" | TC-05 |
| SC-06 | AC-03 | Dado un asegurado sin red y sin copia, cuando entra con su huella, entonces ve que necesita conexión para la primera descarga | TC-05 |
| SC-07 | AC-07 | Dado un servidor caído o lento y una copia, cuando abre la billetera, entonces ve la copia con el aviso de sin conexión | TC-05 |
| SC-08 | AC-14 | Dada una copia con una póliza que vence mientras no hay red, cuando abre la billetera, entonces esa tarjeta aparece como vencida | TC-05 |
| SC-09 | AC-12 | Dado un asegurado sin huella vinculada y sin red, cuando intenta entrar, entonces se le indica activar la huella para ver sus pólizas sin conexión | TC-08 |
| SC-10 | AC-12 | Dado un intento de entrada sin red, cuando la huella falla o se cancela, entonces no se abre la copia | TC-08 |
| SC-11 | UC-02 | Dada la app cerrada por el sistema sin red, cuando se vuelve a abrir, entonces pide de nuevo la huella antes de mostrar la copia | TC-08 |
| SC-12 | AC-05 | Dado un asegurado que añade un documento u otro identificador a la solicitud, cuando consulta, entonces solo recibe sus propias pólizas | TC-02 |
| SC-13 | AC-05 | Dada una solicitud sin token, con token vencido o con token de asesor, cuando consulta, entonces recibe 401 o 403 y ninguna póliza | TC-02 |
| SC-14 | AC-08 | Dada una póliza con beneficiarios y prima, cuando se consulta y se guarda, entonces ni la respuesta ni la copia los incluyen | TC-03 |
| SC-15 | AC-06 | Dada una sesión revocada en el servidor, cuando la billetera consulta y recibe 401, entonces se borra la copia y se pide iniciar sesión | TC-07 |
| SC-16 | UC-03 | Dado el cierre de sesión confirmado, cuando el servidor no responde, entonces la copia se borra igual | TC-07 |
| SC-17 | AC-09 | Dado un teléfono con dos cuentas, cuando entra la segunda, entonces no ve las pólizas de la primera | TC-07 |
| SC-18 | AC-11 | Dado el archivo de la base copiado fuera de la app, cuando se intenta abrir sin la llave, entonces no se lee ninguna póliza | TC-06 |
| SC-19 | AC-11 | Dado un teléfono bloqueado, cuando un proceso intenta usar la llave de envoltura, entonces el Keystore la rechaza | TC-06 |
| SC-20 | AC-11 | Dada una llave del Keystore invalidada (cambio de huellas o de bloqueo de pantalla), cuando se abre la billetera, entonces se regenera la base | OUT OF SCOPE: HU-MOV-05 maneja la llave inválida y la regeneración |
| SC-21 | UC-01 | Dada la conexión recuperada tras usar la copia, cuando vuelve la red, entonces se sincroniza sola | OUT OF SCOPE: la sincronización al volver la red es de HU-MOV-07 |
| SC-22 | UC-02 | Dada la copia en uso, cuando la billetera la muestra, entonces indica la fecha de la última sincronización | OUT OF SCOPE: la fecha de la última sincronización es de HU-MOV-06 |
| SC-23 | AC-05 | Dados dos titulares con el mismo número y distinto tipo de documento, cuando uno consulta, entonces podría ver pólizas del otro | OUT OF SCOPE: RISK-03, la póliza no guarda el tipo de documento |
| SC-24 | UC-02 | Dada la fuente al 200 % y TalkBack activo, cuando recorre la billetera, entonces lee cada tarjeta completa sin textos cortados | TC-09 |

## Scenario coverage

| Kind | Applies | Scenarios | Rationale |
|---|---|---|---|
| Main flow | YES | SC-01, SC-05 | — |
| Alternate flows | YES | SC-04, SC-06, SC-07, SC-09 | — |
| Invalid input and errors | YES | SC-10, SC-12, SC-13 | — |
| Limits and boundaries | YES | SC-03, SC-14, SC-24 | — |
| Related flows before and after | YES | SC-15, SC-16, SC-20, SC-21, SC-22 | — |
| Several users, sessions, devices or roles | YES | SC-13, SC-17, SC-23 | — |
| State and time (expiry, retries, interruptions, going back, offline) | YES | SC-08, SC-11, SC-15, SC-19 | — |

## Test cases

### TC-01 · Solo pólizas vigentes del titular

| Field | Value |
|---|---|
| Covers | AC-10, SR-01 |
| Kind | FUNCTIONAL |
| Risk covered | — |
| Level | INTEGRATION |
| Preconditions | Base de pruebas con un asegurado y pólizas ACTIVE, ISSUED, vencidas, canceladas y una que vence en el instante de la consulta |
| Procedure | 1. Iniciar sesión como el asegurado. 2. Llamar GET /api/v1/insured/policies |
| Expected result | 200 solo con las pólizas ACTIVE de vigencia futura, con número, plan, titular, coberturas y vigencia |
| Tool or method | pytest backend/tests/integration/test_insured_policies_api.py |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | backend/tests/integration/test_insured_policies_api.py::test_tc_01_devuelve_solo_las_polizas_activas_y_vigentes_del_titular; backend/tests/integration/test_insured_policies_api.py::test_tc_01_sin_polizas_vigentes_devuelve_una_lista_vacia |
| Status | PASS |

### TC-02 · Sin acceso a pólizas ajenas

| Field | Value |
|---|---|
| Covers | AC-05, SR-01 |
| Kind | SECURITY |
| Risk covered | THR-01 |
| Level | INTEGRATION |
| Preconditions | Dos asegurados con pólizas vigentes y un asesor |
| Procedure | 1. Consultar como el primero con el documento del segundo en la consulta. 2. Consultar sin token, con token vencido, con token alterado y con token de asesor |
| Expected result | El primero solo recibe sus pólizas; sin token, vencido o alterado responde 401; asesor responde 403 |
| Tool or method | pytest backend/tests/integration/test_insured_policies_api.py |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | backend/tests/integration/test_insured_policies_api.py::test_tc_02_ignora_identificadores_del_cliente_y_no_devuelve_polizas_ajenas; backend/tests/integration/test_insured_policies_api.py::test_tc_02_sin_sesion_valida_responde_401; backend/tests/integration/test_insured_policies_api.py::test_tc_02_token_de_asesor_responde_403 |
| Status | PASS |

### TC-03 · Solo los campos de la tarjeta

| Field | Value |
|---|---|
| Covers | AC-08, SR-02 |
| Kind | SECURITY |
| Risk covered | THR-04 |
| Level | INTEGRATION |
| Preconditions | Póliza con beneficiarios, prima y documento del titular |
| Procedure | 1. Consultar el endpoint. 2. Guardar la respuesta en el almacén de pólizas y leerla |
| Expected result | La respuesta y la copia tienen exactamente los campos del contrato, sin documento, beneficiarios, cotización ni prima |
| Tool or method | pytest backend/tests/integration/test_insured_policies_api.py; ./gradlew testDebugUnitTest (HttpPoliciesApiTest) |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | backend/tests/integration/test_insured_policies_api.py::test_tc_03_la_tarjeta_no_incluye_documento_beneficiarios_ni_prima; movil/app/src/test/java/com/solventa/app/data/policies/HttpPoliciesApiTest.kt::"TC-03 pide las polizas con el token y guarda solo los campos de la tarjeta" |
| Status | PASS |

### TC-04 · Billetera con conexión

| Field | Value |
|---|---|
| Covers | AC-01, AC-10, AC-13 |
| Kind | FUNCTIONAL |
| Risk covered | — |
| Level | UNIT |
| Preconditions | WalletViewModel con dobles de PoliciesApi y PolicyStore |
| Procedure | 1. Cargar con la API respondiendo dos pólizas. 2. Cargar con la API respondiendo una lista vacía |
| Expected result | Muestra dos tarjetas y las guarda en la copia de la cuenta; con la lista vacía indica que no hay pólizas vigentes |
| Tool or method | ./gradlew testDebugUnitTest (WalletViewModelTest) |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | movil/app/src/test/java/com/solventa/app/ui/wallet/WalletViewModelTest.kt::"TC-04 con red muestra las polizas del servidor y guarda la copia de la cuenta"; movil/app/src/test/java/com/solventa/app/ui/wallet/WalletViewModelTest.kt::"TC-04 sin polizas vigentes lo indica y la copia queda vacia"; movil/app/src/test/java/com/solventa/app/ui/wallet/WalletScreenTest.kt |
| Status | PASS |

### TC-05 · Billetera sin conexión

| Field | Value |
|---|---|
| Covers | AC-02, AC-03, AC-07, AC-14 |
| Kind | FUNCTIONAL |
| Risk covered | — |
| Level | UNIT |
| Preconditions | WalletViewModel con dobles y un reloj fijo |
| Procedure | 1. Cargar sin red con copia. 2. Cargar sin red sin copia. 3. Cargar con la API caída o lenta y copia. 4. Cargar sin red con una póliza de la copia ya vencida según el reloj |
| Expected result | 1 y 3 muestran la copia con el aviso "Sin conexión"; 2 indica que necesita conexión para la primera descarga; 4 marca la tarjeta como vencida |
| Tool or method | ./gradlew testDebugUnitTest (WalletViewModelTest) |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | movil/app/src/test/java/com/solventa/app/ui/wallet/WalletViewModelTest.kt::"TC-05 sin red y con copia muestra la copia con el aviso de sin conexion"; movil/app/src/test/java/com/solventa/app/ui/wallet/WalletViewModelTest.kt::"TC-05 una poliza de la copia que vencio sin red aparece como vencida"; movil/app/src/test/java/com/solventa/app/ui/wallet/WalletScreenTest.kt |
| Status | PASS |

### TC-06 · Copia cifrada en el teléfono

| Field | Value |
|---|---|
| Covers | AC-11, SR-03 |
| Kind | SECURITY |
| Risk covered | THR-02 |
| Level | INTEGRATION |
| Preconditions | Emulador o dispositivo con bloqueo de pantalla y una copia guardada |
| Procedure | 1. Guardar una copia. 2. Leer los bytes del archivo de la base y buscar la cabecera SQLite y el número de póliza. 3. Borrar la llave de la cuenta e intentar leer la copia. 4. Revisar que la frase guardada esté envuelta (PassphraseVaultTest) |
| Expected result | El archivo no es SQLite legible ni contiene el número; sin la llave la copia no abre y se borra; la frase guardada no es la de la base |
| Tool or method | ./gradlew connectedDebugAndroidTest (EncryptedPolicyStoreTest) en emulador con Keystore real |
| Automation | AUTOMATED |
| Environment | LOCAL |
| Evidence | movil/app/src/androidTest/java/com/solventa/app/data/policies/EncryptedPolicyStoreTest.kt::el_archivo_no_es_sqlite_legible_ni_contiene_el_numero_de_poliza; movil/app/src/androidTest/java/com/solventa/app/data/policies/EncryptedPolicyStoreTest.kt::sin_la_llave_de_la_cuenta_la_copia_no_abre_y_se_borra; movil/app/src/test/java/com/solventa/app/data/policies/PassphraseVaultTest.kt. Emulador con Android 15, 2026-10-23: 4 de 4 |
| Status | PASS |

### TC-07 · Borrado de la copia y aislamiento por cuenta

| Field | Value |
|---|---|
| Covers | AC-04, AC-06, AC-09, SR-04 |
| Kind | SECURITY |
| Risk covered | THR-03 |
| Level | UNIT |
| Preconditions | AuthViewModel y WalletViewModel con dobles; dos cuentas en el teléfono |
| Procedure | 1. Cerrar sesión con el servidor caído. 2. Recibir 401 en la consulta. 3. Guardar la copia de la cuenta A y entrar con la cuenta B |
| Expected result | 1 y 2 borran la copia y la llave de la cuenta; 2 lleva a iniciar sesión; 3 no muestra pólizas de A |
| Tool or method | ./gradlew testDebugUnitTest (WalletViewModelTest, AuthViewModelTest) |
| Automation | AUTOMATED |
| Environment | CI |
| Evidence | movil/app/src/test/java/com/solventa/app/ui/wallet/WalletViewModelTest.kt::"TC-07 un 401 borra la copia de la cuenta y marca la sesion vencida"; movil/app/src/test/java/com/solventa/app/ui/auth/AuthViewModelTest.kt::"TC-07 cerrar sesion borra la copia de la cuenta aunque el servidor no responda"; movil/app/src/test/java/com/solventa/app/ui/auth/AuthViewModelTest.kt::"TC-07 sesion vencida borra la copia, cierra la sesion y pide ingresar" |
| Status | PASS |

### TC-08 · Entrada sin red solo con huella

| Field | Value |
|---|---|
| Covers | AC-12, SR-05 |
| Kind | SECURITY |
| Risk covered | THR-05 |
| Level | E2E |
| Preconditions | Emulador con huella registrada, una cuenta con huella vinculada y copia; otra cuenta sin huella vinculada |
| Procedure | 1. Modo avión. 2. Entrar con la huella correcta. 3. Repetir con una huella no registrada y cancelando. 4. Cerrar la app desde el sistema y abrirla. 5. Intentar entrar con la cuenta sin huella |
| Expected result | 2 muestra la copia en solo lectura; 3 no la abre; 4 pide la huella otra vez; 5 indica activar la huella |
| Tool or method | Prueba manual en emulador (README, sección 5.5); la lógica se prueba en AuthViewModelTest con los casos TC-08 |
| Automation | MANUAL |
| Environment | LOCAL |
| Evidence | PENDING |
| Status | PENDING |

### TC-09 · Accesibilidad de la billetera

| Field | Value |
|---|---|
| Covers | QR-01 |
| Kind | QUALITY |
| Risk covered | — |
| Level | ACCESSIBILITY |
| Preconditions | Emulador con TalkBack y fuente al 200 %, copia con tres pólizas |
| Procedure | 1. Recorrer la billetera con TalkBack. 2. Revisar textos y áreas táctiles con la fuente al 200 %. 3. Pasar Accessibility Scanner |
| Expected result | Cada tarjeta se lee completa, el aviso de sin conexión se anuncia, nada se corta y las áreas táctiles miden al menos 48 dp |
| Tool or method | TalkBack y Accessibility Scanner |
| Automation | MANUAL |
| Environment | LOCAL |
| Evidence | PENDING |
| Status | PENDING |

### TC-10 · Dependencias de la copia cifrada

| Field | Value |
|---|---|
| Covers | SR-03 |
| Kind | SECURITY |
| Risk covered | THR-02 |
| Level | STATIC |
| Preconditions | Versiones fijas en movil/gradle/libs.versions.toml |
| Procedure | 1. Consultar en OSV.dev cada dependencia nueva con su versión. 2. Revisar que el artefacto obsoleto android-database-sqlcipher no quede |
| Expected result | Sin vulnerabilidades conocidas; solo net.zetetic:sqlcipher-android en el catálogo |
| Tool or method | OSV.dev y revisión del catálogo de versiones |
| Automation | MANUAL |
| Environment | LOCAL |
| Evidence | movil/gradle/libs.versions.toml solo declara net.zetetic:sqlcipher-android 4.9.0; consulta de OSV.dev del 2026-10-22 en security.md, sección 14 |
| Status | PASS |

## Security test coverage

| Category | Applies | Test cases | Rationale |
|---|---|---|---|
| Unauthenticated user | YES | TC-02 | — |
| User without permissions | YES | TC-02 | — |
| Access to another user's resources | YES | TC-02, TC-07 | — |
| Cross-tenant access | NO | — | Canal del asegurado sin inquilinos |
| Malicious input | YES | TC-02 | — |
| Expired tokens | YES | TC-02, TC-07 | — |
| Revoked sessions | YES | TC-07 | — |
| Tampered data | YES | TC-02, TC-06 | — |
| Wrong keys | YES | TC-06 | — |
| External service failures | YES | TC-05 | — |
| Race conditions | NO | — | Consulta de solo lectura; la copia de cada cuenta tiene un solo escritor |
| Information exposure | YES | TC-03 | — |
| Secrets in code | NO | — | Sin secretos nuevos; la frase se genera en el teléfono y el gate revisa secretos en cada commit |
| Insecure configuration | YES | TC-06 | — |
| Vulnerable dependencies | YES | TC-10 | — |
