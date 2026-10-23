# HU-MOV-04 · Polizas sin conexion

| Field | Value |
|---|---|
| ID | HU-MOV-04 |
| Title | Polizas sin conexion |
| User story | https://github.com/proyectos-miso/proyecto-final-miso/issues/70 |
| Owner | Juan Camilo Peña |
| Status | IN_PROGRESS |
| Created | 2026-10-22 |
| Security profile | HIGH |

<!-- A spec is a contract: what, why, how, and how we will know it is done. Fill the sections in
     order and stop for agreement between them: Requirements → Design → Tasks.
     Status: DRAFT → READY (after spec-review) → IN_PROGRESS → IN_REVIEW → DONE | BLOCKED. -->

## 1. Requirements

### User story

**HU-MOV-04 · Consultar mis pólizas sin conexión a internet** (Sprint 2, Must have, 3 puntos, FE-MOV-03, ESC-LAT-04; depende de HU-MOV-01).

**Como** cliente asegurado **quiero** consultar mis coberturas y credenciales aunque no tenga señal **para** demostrar que estoy asegurado en el lugar y el momento en que me lo exigen.

Criterios de aceptación de la historia:

1. **Pólizas con conexión.** *Dado* el asegurado autenticado y con red, *cuando* abre la billetera, *entonces* ve sus pólizas obtenidas del servidor y se guarda una copia local.
2. **Pólizas sin conexión.** *Dado* el asegurado sin red y con una copia local, *cuando* abre la billetera, *entonces* ve sus pólizas desde el teléfono y un aviso de "Sin conexión".
3. **Primera vez sin conexión.** *Dado* un asegurado sin copia local y sin red, *cuando* abre la billetera, *entonces* se le informa que necesita conexión para la primera descarga.
4. **Copia ligada a la sesión.** *Dado* el cierre de sesión (HU-MOV-12), *cuando* se confirma, *entonces* la copia local de pólizas se borra.

Requisitos no funcionales: HA-06 (autenticación robusta y biometría fuerte), HA-08 (absorber picos con contrapresión), HA-16 (proteger los datos personales almacenados). Mockup: https://solventa-movil.vercel.app/?vista=billetera. Tareas: #188 endpoint del asegurado, #189 base local con Room (la cifra HU-MOV-05), #190 billetera con aviso de sin conexión, #191 pruebas.

### Problem and outcome

El asegurado necesita demostrar su cobertura donde no hay señal, y hoy la app no muestra pólizas. Resultado: una billetera que muestra las pólizas del asegurado autenticado desde el servidor, guarda una copia local mínima para verla sin conexión y la borra al cerrar la sesión.

### Goals and non-goals

Objetivos: endpoint con las pólizas vigentes del asegurado autenticado; copia local cifrada en el teléfono; billetera con los estados con conexión, sin conexión y primera vez sin conexión; borrado de la copia al cerrar sesión.

Aclaraciones de Juan Camilo Peña (2026-10-22): la billetera muestra solo pólizas vigentes; la "credencial" es la tarjeta de cada póliza con su número y vigencia, sin código QR; la copia local se cifra en esta historia, y HU-MOV-05 (David) queda para el manejo de una llave inválida y la regeneración de la base.

Fuera de alcance: llave inválida y regeneración de la base (HU-MOV-05); sincronizar al recuperar la conexión (HU-MOV-07); fecha de la última sincronización (HU-MOV-06); carátula en PDF (HU-WEB-16); carné con código QR.

### Affected paths

| Path | Change |
|---|---|
| backend/app/bff/insured/** | Router nuevo del canal del asegurado con GET /api/v1/insured/policies |
| backend/app/main.py | Monta el router del asegurado |
| backend/app/modules/policy/** | Pólizas vigentes del titular como tarjetas de la billetera |
| backend/app/modules/identity/service.py | Cuenta del token de acceso, rechazada si la sesión fue revocada |
| backend/tests/** | Pruebas del endpoint |
| movil/app/src/main/java/com/solventa/app/domain/** | Modelo y puertos de pólizas; se retira el modelo Policy sin uso |
| movil/app/src/main/java/com/solventa/app/data/** | Cliente HTTP de pólizas, base Room cifrada por cuenta y llave en el Keystore; se retira EncryptedStorageManager |
| movil/app/src/main/java/com/solventa/app/ui/** | Billetera, su ViewModel, entrada sin red y borrado de la copia en AuthViewModel |
| movil/app/src/main/java/com/solventa/app/MainActivity.kt | La billetera reemplaza el inicio provisional |
| movil/app/src/main/java/com/solventa/app/SolventaApplication.kt | Composición de las dependencias nuevas |
| movil/build.gradle.kts | Plugin KSP |
| movil/app/build.gradle.kts | KSP, compilador de Room y SQLCipher |
| movil/gradle/libs.versions.toml | Versiones de las dependencias nuevas |
| movil/app/src/main/res/values/strings.xml | Textos de la billetera |
| movil/app/src/test/** | Pruebas del cliente, de la frase, del ViewModel y de la pantalla |
| movil/app/src/androidTest/** | Prueba instrumentada del cifrado |
| docs/adr/** | ADR 0021 y ajuste de la ADR 0015 |
| AGENTS.md | Rango de las ADR del móvil |

### Use cases

| ID | Actor | Use case | Main flow | Alternate flows |
|---|---|---|---|---|
| UC-01 | Asegurado | Ver mis pólizas con conexión | 1. Abre la billetera. 2. La app pide sus pólizas al backend con su token. 3. Las muestra y guarda la copia local | Error del servidor o tiempo de espera: muestra la copia local, si existe, con el aviso de sin conexión |
| UC-02 | Asegurado | Ver mis pólizas sin conexión | 1. Abre la app sin red. 2. Entra con su huella, que se verifica en el teléfono. 3. La app abre la copia local y muestra las pólizas con el aviso "Sin conexión" | Sin copia local: aviso de que necesita conexión para la primera descarga. Sin huella vinculada: aviso de activar la huella para ver las pólizas sin conexión |
| UC-03 | Asegurado | Cerrar sesión | 1. Confirma el cierre (HU-MOV-12). 2. La app borra la copia local de pólizas | Falla la llamada de cierre en el servidor: la copia se borra igual |

### Abuse cases

| ID | Abuse case | Actor | Threat | Expected response | Test case |
|---|---|---|---|---|---|
| AB-01 | Pedir las pólizas de otro asegurado cambiando un parámetro de la solicitud | Asegurado malicioso | THR-01 | El endpoint no recibe identificadores: usa el del token y nunca devuelve pólizas ajenas | TC-02 |
| AB-02 | Leer la copia local de un teléfono perdido o con acceso de depuración | Quien tenga el teléfono | THR-02 | Copia mínima, cifrada con una llave del Keystore y borrada al cerrar sesión | TC-06 |
| AB-03 | Ver las pólizas de la cuenta anterior en un teléfono compartido | Otro usuario del teléfono | THR-03 | La copia es de una cuenta y se borra al cerrar sesión o al cambiar de cuenta | TC-07 |

### Acceptance criteria

| ID | Criterion | Source |
|---|---|---|
| AC-01 | WHEN el asegurado autenticado y con red abre la billetera, THE app SHALL mostrar sus pólizas del servidor y guardar una copia local | STATED |
| AC-02 | WHEN el asegurado sin red y con copia local abre la billetera, THE app SHALL mostrar las pólizas de la copia y el aviso "Sin conexión" | STATED |
| AC-03 | WHEN el asegurado sin copia local y sin red abre la billetera, THE app SHALL informar que necesita conexión para la primera descarga | STATED |
| AC-04 | WHEN se confirma el cierre de sesión, THE app SHALL borrar la copia local de pólizas | STATED |
| AC-05 | THE endpoint SHALL devolver solo las pólizas del asegurado del token, sin aceptar identificadores del cliente | DERIVED: la historia no dice cómo se identifica al titular; tomarlo del cliente permitiría ver pólizas ajenas |
| AC-06 | WHEN el servidor responde 401 a la consulta, THE app SHALL borrar la copia local y pedir un nuevo inicio de sesión | DERIVED: la historia liga la copia a la sesión solo en el cierre explícito; una sesión revocada debe tener el mismo efecto |
| AC-07 | WHEN el servidor falla o no responde a tiempo y hay copia local, THE app SHALL mostrar la copia con el aviso de sin conexión | DERIVED: la historia solo cubre la falta de red; un servidor caído deja al usuario en la misma situación |
| AC-08 | THE copia local SHALL guardar solo los campos que muestra la billetera, sin el documento completo ni los beneficiarios | DERIVED: minimización de datos personales en el teléfono (HA-16) |
| AC-09 | WHEN cambia la cuenta activa en el teléfono, THE billetera SHALL mostrar solo las pólizas de esa cuenta | DERIVED: el teléfono admite varias cuentas desde HU-MOV-01 |
| AC-10 | THE endpoint SHALL devolver solo las pólizas vigentes, y la billetera SHALL mostrar cada una como una tarjeta con número, plan, titular, suma asegurada y vigencia | DERIVED: aclaración del 2026-10-22 sobre qué pólizas y qué "credenciales" se muestran |
| AC-11 | THE copia local SHALL guardarse cifrada con una llave que solo existe en el Android Keystore del teléfono | DERIVED: aclaración del 2026-10-22; HA-16 pide proteger los datos personales almacenados |
| AC-12 | WHEN no hay red, THE asegurado con huella vinculada SHALL entrar a la billetera con un desbloqueo local de su huella y ver solo la copia; sin huella vinculada, THE app SHALL indicar que active la huella para usar la billetera sin conexión | DERIVED: el ingreso actual siempre pasa por el servidor; sin esto el criterio 2 no se puede cumplir (decisión del 2026-10-22) |
| AC-13 | WHEN el asegurado no tiene pólizas vigentes, THE billetera SHALL indicarlo en lugar de una lista vacía | DERIVED: la historia no dice qué ve quien aún no tiene pólizas pagadas |
| AC-14 | WHEN una póliza de la copia vence mientras no hay red, THE billetera SHALL mostrarla como vencida | DERIVED: sin red la copia no se actualiza y no debe presentar como vigente una cobertura terminada |

### Quality requirements

| ID | Category | Requirement | Target and conditions |
|---|---|---|---|
| QR-01 | ACCESSIBILITY | La billetera se usa con TalkBack y con la fuente más grande | Guías de accesibilidad de Android: descripciones, encabezados, áreas táctiles de 48 dp y textos que crecen hasta 200 % sin cortarse |

### Security triggers

| Trigger | Applies | Rationale |
|---|---|---|
| Personal data (identifies or can identify a person) | YES | Las pólizas identifican al titular y se guardan en el teléfono |
| Sensitive data (special categories, biometrics, health, financial, minors) | NO | Coberturas y vigencias, sin datos de salud, cuentas ni tarjetas |
| Authentication, sessions, credentials or one-time codes | YES | El endpoint exige el token del asegurado y la copia se liga a la sesión |
| Authorization or access to other users' resources | YES | Cada asegurado ve solo sus pólizas |
| Payments or money movement | NO | Solo consulta |
| Third-party services or integrations | NO | Sin servicios externos |
| Infrastructure, network, IAM, CI/CD or secrets | NO | Sin cambios de infraestructura |
| Multiple tenants, partners or organizations | NO | Canal del asegurado, sin socios |
| Storage or processing on a mobile device | YES | Copia local de pólizas en el teléfono |
| Web UI or data exposed in the browser | NO | Solo app móvil |
| New or updated dependencies | YES | Compilador de Room, SQLCipher y posiblemente Navigation Compose (ADR 0015) |
| Critical paths (sdd/security/critical-paths.md) | YES | **/auth/**, sesión del móvil (data/session) y archivos Gradle |

### Security requirements

| ID | Requirement | Source | Controls | Priority |
|---|---|---|---|---|
| SR-01 | El endpoint toma al titular del token y devuelve solo sus pólizas vigentes | DATA-01, THR-01 | CTL-01 | HIGH |
| SR-02 | La respuesta y la copia local solo llevan los campos de la tarjeta | DATA-01, THR-04 | CTL-02 | MEDIUM |
| SR-03 | La copia local está cifrada con una llave por cuenta que no sale del Keystore | DATA-01, DATA-02, THR-02 | CTL-03 | HIGH |
| SR-04 | La copia se borra al cerrar sesión y al recibir 401, y no se muestra a otra cuenta | DATA-01, THR-03 | CTL-04 | HIGH |
| SR-05 | Sin red, la billetera solo se abre tras un desbloqueo biométrico fuerte en el teléfono | DATA-01, THR-05 | CTL-05 | HIGH |

## 2. Design

### Components

Backend, canal móvil (ADR 0005):

- `backend/app/bff/insured/router.py`: router nuevo del canal del asegurado, con `GET /api/v1/insured/policies` y el rol `insured`.
- `backend/app/modules/policy/service.py`: `active_for_holder(session, document_number)`, que trae las pólizas `ACTIVE` con `valid_until` futuro.
- `backend/app/modules/policy/models.py`: `InsuredPolicyCard` como modelo de respuesta.
- La cuenta se lee con el `sub` del token (`user_id`); de ella salen el documento y el nombre.

App (ADR 0013):

- `domain/policies/`: modelo `PolicyCard`, puerto `PoliciesApi` con resultado sellado (`Loaded`, `Unauthorized`, `Unavailable`) y puerto `PolicyStore` (guardar, leer y borrar por cuenta).
- `data/policies/`:
  - `HttpPoliciesApi`, con el mismo patrón que `HttpAuthApi`;
  - `WalletDatabase` (Room), con la entidad y el DAO de tarjetas;
  - `EncryptedPolicyStore`, que abre una base por cuenta con SQLCipher.
- `ui/wallet/`:
  - `WalletViewModel`, con un `WalletUiState` para cargando, con datos, sin conexión, primera vez sin red y sesión vencida;
  - `WalletScreen`, con las tarjetas, el aviso de sin conexión y el botón de cerrar sesión.
- `AuthViewModel`:
  - si el servidor no responde tras un desbloqueo biométrico exitoso, entra en modo sin conexión con esa cuenta;
  - el cierre de sesión y la sesión vencida borran la copia.
- `MainActivity`: la billetera reemplaza la pantalla que hoy aparece tras entrar.
- `SolventaApplication`: compone `HttpPoliciesApi` y `EncryptedPolicyStore`.
- Se reemplaza el marcador `data/local/EncryptedStorageManager`, porque el cifrado nace en esta historia.

### Data flows

- **Con red:** app → CloudFront → `GET /api/v1/insured/policies` con el token → backend → PostgreSQL. La respuesta llega a la billetera y se guarda en la copia cifrada de la cuenta.
- **Sin red:** huella → desbloqueo local de la credencial del dispositivo de la cuenta → apertura de la copia cifrada → billetera en solo lectura.
- **Límites de confianza:** el token en el backend y el Keystore en el teléfono.

### Data contract

`GET /api/v1/insured/policies`, sin parámetros: el titular sale del token. Rol `insured`.

| Campo | Tipo | Notas |
|---|---|---|
| policy_number | string (16) | Número de la póliza |
| plan | basic, standard o premium | Plan contratado |
| holder_name | string (150) | Nombre de la cuenta del asegurado |
| coverages | lista de {name: string, limit: number} | Solo coberturas incluidas |
| valid_from | fecha y hora ISO 8601 | Inicio de vigencia |
| valid_until | fecha y hora ISO 8601 | Fin de vigencia |

- `200`: `{"policies": [...]}`, que puede venir vacía.
- `401`: sin token, o con un token inválido o vencido.
- `403`: token de otro rol.

La respuesta no incluye el documento, los beneficiarios, la cotización ni la prima. Las pólizas en `ISSUED` (sin pagar) o vencidas no se devuelven. Clasificación: CONFIDENTIAL (DATA-01).

### Security design decisions

| Decision | Implements | Rejected alternative and why |
|---|---|---|
| El titular sale del `sub` del token; el endpoint no recibe identificadores | CTL-01 | Recibir el documento: permitiría pedir pólizas ajenas |
| Respuesta y copia solo con los campos de la tarjeta | CTL-02 | Devolver PolicyRecord: incluye documento y beneficiarios |
| Una base SQLCipher por cuenta, con frase aleatoria de 32 bytes envuelta por una llave AES-GCM del Keystore por cuenta, usable solo con el teléfono desbloqueado | CTL-03, CRY-01, CRY-02 | Archivo plano o preferencias: datos personales en claro |
| La copia se borra al cerrar sesión, con 401 y al cambiar de cuenta | CTL-04 | Conservarla: quedaría disponible para otra persona |
| Sin red, la billetera se abre solo tras el desbloqueo biométrico de la credencial de la cuenta | CTL-05 | Abrirla sin verificar: cualquiera con el teléfono la vería |

### Architecture decisions

- docs/adr/0021-mobile-encrypted-local-database.md: base local cifrada con Room y SQLCipher, con llaves por cuenta en el Keystore.
- docs/adr/0015-mobile-navigation.md: Navigation Compose se adopta cuando una funcionalidad tenga varias pantallas con historial; la billetera es una sola pantalla.

### Configuration and deployment

- **Dependencias nuevas:** plugin KSP 2.1.0-1.0.29, `room-compiler` 2.6.1 y `net.zetetic:sqlcipher-android` 4.9.0. La última reemplaza el artefacto obsoleto `android-database-sqlcipher`.
- **Variables:** ninguna nueva.
- **Pruebas en dispositivo:** el cifrado real, el Keystore y la huella se prueban en un dispositivo o emulador con huella (README, sección 5.5).

## 3. Tasks

| ID | Task | Traces to | Controls | Status | Evidence |
|---|---|---|---|---|---|
| T-01 | Backend: GET /api/v1/insured/policies con las pólizas vigentes del titular del token (#188) | AC-01, AC-05, AC-10, SR-01, SR-02 | CTL-01, CTL-02 | DONE | backend/tests/integration/test_insured_policies_api.py |
| T-02 | App: dominio, cliente HTTP y base Room con SQLCipher por cuenta (#189) | AC-01, AC-08, AC-11, SR-02, SR-03 | CTL-02, CTL-03 | DONE | movil/app/src/main/java/com/solventa/app/data/policies/EncryptedPolicyStore.kt |
| T-03 | App: billetera con estados con conexión, sin conexión y primera vez, y entrada sin red con huella (#190) | AC-02, AC-03, AC-07, AC-10, AC-12, AC-13, AC-14, SR-05 | CTL-05 | DONE | movil/app/src/main/java/com/solventa/app/ui/wallet/WalletScreen.kt |
| T-04 | App: borrado de la copia al cerrar sesión, con 401 y por cuenta | AC-04, AC-06, AC-09, SR-04 | CTL-04 | DONE | movil/app/src/test/java/com/solventa/app/ui/auth/AuthViewModelTest.kt |
| T-05 | Pruebas del endpoint, del repositorio y del ViewModel (#191) | AC-01, AC-05, SR-01 | CTL-01 | DONE | movil/app/src/test/java/com/solventa/app/ui/wallet/WalletViewModelTest.kt |
| T-06 | Pruebas en dispositivo del cifrado, del Keystore y de la entrada sin red | AC-11, AC-12, SR-03, SR-05 | CTL-03, CTL-05 | IN_PROGRESS | movil/app/src/androidTest/java/com/solventa/app/data/policies/EncryptedPolicyStoreTest.kt; falta la prueba manual de la huella (TC-08) |
| T-07 | ADR 0021 y ajuste de la ADR 0015 | AC-11 | — | DONE | docs/adr/0021-mobile-encrypted-local-database.md |
