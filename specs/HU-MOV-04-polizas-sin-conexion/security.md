# Security and privacy assessment · HU-MOV-04

## 1. Data inventory and classification

| ID | Data | Classification | Personal | Sensitive | Purpose |
|---|---|---|---|---|---|
| DATA-01 | Pólizas vigentes del asegurado: número, plan, nombre del titular, coberturas con su límite y vigencia | CONFIDENTIAL | YES | NO | Demostrar la cobertura con y sin conexión |
| DATA-02 | Frase de la base local y llave de envoltura de cada cuenta | RESTRICTED | NO | NO | Cifrar la copia local |

## 2. Data lifecycle

### DATA-01 · Pólizas de la billetera

| Question | Answer |
|---|---|
| What it contains | Número, plan, nombre del titular, coberturas con su límite y fechas de vigencia; sin documento, beneficiarios ni prima |
| Why it is needed | El asegurado debe demostrar su cobertura donde no hay señal |
| Who can access it | El asegurado titular y el backend; en el teléfono, solo tras su huella cuando no hay red |
| Where it is captured | Al emitir la póliza (HU-WEB-05); esta historia solo la consulta |
| How it is transmitted | HTTPS hasta CloudFront y red privada de AWS hasta el backend |
| Where it is stored | PostgreSQL en el servidor y una base SQLCipher por cuenta en el teléfono |
| Copies, caches and backups | Respaldos de RDS; la base del teléfono se excluye de respaldos (allowBackup en false) |
| How long it is kept | En el teléfono, hasta el cierre de sesión, un 401 o el cambio de cuenta |
| How access is audited | Sin registro nuevo; el acceso al endpoint queda en los registros de la API |
| How it is deleted or anonymized | Se borra el archivo de la base y la frase envuelta de la cuenta |
| What happens if it leaks | Se exponen coberturas y vigencias de una persona; la copia mínima y cifrada reduce el daño |
| Transfers to third parties | Ninguna |

### DATA-02 · Frase y llave de la copia local

| Question | Answer |
|---|---|
| What it contains | Una frase aleatoria de 32 bytes por cuenta y una llave AES-256 del Keystore que la envuelve |
| Why it is needed | Abrir la base cifrada de la cuenta |
| Who can access it | La llave no sale del Keystore; la frase envuelta solo se descifra en la app con el teléfono desbloqueado |
| Where it is captured | Se generan al guardar la primera copia de la cuenta |
| How it is transmitted | No se transmite |
| Where it is stored | Llave en el Android Keystore; frase envuelta en las preferencias privadas de la app |
| Copies, caches and backups | Ninguna; las preferencias se excluyen de respaldos |
| How long it is kept | Hasta que se borra la copia de la cuenta |
| How access is audited | No aplica: no sale del teléfono |
| How it is deleted or anonymized | Se elimina la entrada del Keystore y la frase envuelta |
| What happens if it leaks | Sin la llave del Keystore la frase envuelta no sirve; la frase en claro solo existe en memoria al abrir la base |
| Transfers to third parties | Ninguna |

## 3. Actors and roles

| Actor | Role | Trust level | What they can do |
|---|---|---|---|
| Asegurado | insured | Autenticado | Ver sus pólizas vigentes con y sin conexión |
| Asesor | advisor | Autenticado | Nada en este endpoint (403) |
| Quien tenga el teléfono | Ninguno | No confiable | Abrir la app sin la huella del titular |
| Atacante externo | Ninguno | No confiable | Llamar al endpoint sin token o con uno ajeno |

## 4. Trust boundaries

| Boundary | Between | What is validated when crossing it |
|---|---|---|
| API | App y backend | Firma, vencimiento y rol del token (HU-MOV-01); el titular sale del token |
| Keystore | App y almacenamiento del teléfono | Teléfono desbloqueado para usar la llave; huella para abrir la billetera sin red |

## 5. Data flows

| Source | Destination | Data | Channel | Protection |
|---|---|---|---|---|
| Backend | App | DATA-01 | HTTPS por CloudFront | CTL-01, CTL-02 |
| App | Base local | DATA-01 | Archivo en el teléfono | CRY-01, CRY-02 |

## 6. Third-party services

N/A: la historia no usa servicios externos.

## 7. Attack surface

| Surface | Exposure | Inputs the attacker controls |
|---|---|---|
| GET /api/v1/insured/policies | Autenticada | El token |
| Base local de la billetera | Almacenamiento del teléfono | El archivo, si tiene acceso al almacenamiento |
| Entrada sin red | Quien tenga el teléfono | Intentos de desbloqueo biométrico |

## 8. Threat model

| ID | STRIDE | Asset | Threat | Actor | Likelihood | Impact | Risk | Controls |
|---|---|---|---|---|---|---|---|---|
| THR-01 | I, E | DATA-01 | Pedir las pólizas de otro asegurado | Asegurado malicioso | MEDIUM | HIGH | HIGH | CTL-01 |
| THR-02 | I | DATA-01 | Leer la copia desde el almacenamiento del teléfono | Quien tenga el teléfono | MEDIUM | HIGH | HIGH | CTL-03 |
| THR-03 | I | DATA-01 | Otra persona o cuenta ve la copia tras cerrar sesión o en un teléfono compartido | Otro usuario del teléfono | MEDIUM | MEDIUM | MEDIUM | CTL-04 |
| THR-04 | I | DATA-01 | La respuesta expone documento o beneficiarios | Atacante con un token | LOW | MEDIUM | LOW | CTL-02 |
| THR-05 | S | DATA-01 | Abrir la billetera sin red sin ser el titular | Quien tenga el teléfono | MEDIUM | HIGH | HIGH | CTL-05 |
| THR-06 | I | DATA-01 | La copia se sigue viendo sin red después de revocar el dispositivo en el servidor | Quien tenga el teléfono y la huella del titular | LOW | MEDIUM | LOW | CTL-04 |

## 9. Controls

| ID | Control | Domain | Status | Mitigates | Tests | Tasks | References | Rationale |
|---|---|---|---|---|---|---|---|---|
| CTL-01 | El titular sale del token; la consulta filtra por su documento y solo pólizas vigentes; rol insured | API, BACKEND | EXISTING | THR-01 | TC-01, TC-02 | T-01 | API1:2023, CWE-639 | — |
| CTL-02 | Respuesta y copia solo con los campos de la tarjeta | API, DATA | EXISTING | THR-04 | TC-03 | T-01, T-02 | API3:2023, CWE-213 | — |
| CTL-03 | Base SQLCipher por cuenta con frase envuelta por una llave AES-GCM del Keystore | MOBILE, CRYPTO | EXISTING | THR-02 | TC-06 | T-02 | MASVS-STORAGE-1, MASVS-CRYPTO-2 | — |
| CTL-04 | Borrado de la copia al cerrar sesión, con 401 y por cuenta | MOBILE | EXISTING | THR-03, THR-06 | TC-07 | T-04 | MASVS-STORAGE-2 | — |
| CTL-05 | Sin red, la billetera se abre solo tras el desbloqueo biométrico fuerte de la cuenta | MOBILE | EXISTING | THR-05 | TC-08 | T-03 | MASVS-AUTH-2 | — |
| CTL-06 | Aislamiento entre inquilinos | DATA | NOT APPLICABLE | — | — | — | — | Canal del asegurado sin socios ni inquilinos |

## 10. Cryptography

### CRY-01 · Base local cifrada

| Field | Value |
|---|---|
| Protects | DATA-01 |
| Type | AT_REST |
| Algorithm or service | SQLCipher 4: AES-256-CBC por página con HMAC-SHA512 |
| Rationale | Cifra la copia de pólizas en el teléfono y detecta alteraciones de cada página |
| Key management | Frase aleatoria de 32 bytes por cuenta, envuelta por CRY-02; en claro solo en memoria al abrir la base |
| Permissions | Solo la app |
| Rotation | Se genera una nueva cada vez que se crea la copia de una cuenta |
| Recovery | Si la base no abre, se borra y se descarga de nuevo con red |
| Failure behavior | La billetera muestra que necesita conexión |
| Tests | TC-06 |

### CRY-02 · Envoltura de la frase

| Field | Value |
|---|---|
| Protects | DATA-02 |
| Type | APP_LEVEL |
| Algorithm or service | AES-256-GCM con una llave del Android Keystore por cuenta, no exportable y usable solo con el teléfono desbloqueado |
| Rationale | La frase de la base nunca queda en claro en el almacenamiento |
| Key management | Llave por cuenta en el Keystore; IV aleatorio por envoltura guardado junto a la frase envuelta |
| Permissions | Solo la app |
| Rotation | Se crea con la copia y se elimina al borrarla |
| Recovery | Si la llave se invalida, se borra la copia y se descarga de nuevo con red (HU-MOV-05) |
| Failure behavior | La billetera muestra que necesita conexión |
| Tests | TC-06 |

## 11. Secrets and keys

| Secret | Location | Access | Environments | Rotation | Revocation | Leak detection |
|---|---|---|---|---|---|---|
| Llave de envoltura de la billetera por cuenta | Android Keystore | La app, con el teléfono desbloqueado | Cada teléfono | Se crea con la copia y se elimina al borrarla | Borrar la copia de la cuenta | No exportable del Keystore |
| Frase de la base por cuenta | Preferencias privadas, envuelta | La app | Cada teléfono | Nueva con cada copia | Borrar la copia de la cuenta | No se registra ni se muestra |

## 12. Authentication, authorization and sessions

| Check | Applies | Controls | Rationale |
|---|---|---|---|
| User identification | YES | CTL-01 | — |
| Secure authentication | YES | CTL-05 | — |
| Session management | YES | CTL-04 | — |
| Token expiration | YES | CTL-04 | — |
| Revocation | YES | CTL-04 | — |
| Server-side permission checks | YES | CTL-01 | — |
| Per-resource access (ownership) | YES | CTL-01 | — |
| Roles | YES | CTL-01 | — |
| Privilege separation | NO | — | Un solo rol consulta y solo lee |
| Brute-force protection | NO | — | Sin credenciales nuevas; BiometricPrompt bloquea tras varios intentos |
| Rate limiting | NO | — | Consulta de solo lectura del propio titular |
| One-time code (OTP) handling | NO | — | Sin códigos |
| User enumeration prevention | NO | — | El endpoint no recibe identificadores |
| CSRF protection | NO | — | Token en cabecera, sin cookies |

## 13. Data isolation and multi-tenancy

N/A: canal del asegurado, sin socios ni inquilinos.

## 14. Dependencies

| ID | Dependency | Version | Component | Use | Criticality | Evaluation | Result | Status |
|---|---|---|---|---|---|---|---|---|
| DEP-01 | net.zetetic:sqlcipher-android | 4.9.0 | movil | Cifrado de la base local | CRITICAL | OSV.dev 2026-10-22 | No known vulnerabilities | EVALUATED |
| DEP-02 | androidx.room:room-runtime | 2.6.1 | movil | Base local | HIGH | OSV.dev 2026-10-22 | No known vulnerabilities | EVALUATED |
| DEP-03 | androidx.room:room-compiler | 2.6.1 | movil (compilación) | Generación del DAO | MEDIUM | OSV.dev 2026-10-22 | No known vulnerabilities | EVALUATED |
| DEP-04 | com.google.devtools.ksp | 2.1.0-1.0.29 | movil (compilación) | Procesador de anotaciones | MEDIUM | OSV.dev 2026-10-22 | No known vulnerabilities | EVALUATED |

## 15. Risk register and residual risk

| ID | Risk | Threats | Likelihood | Impact | Level | Treatment | Residual risk | Status |
|---|---|---|---|---|---|---|---|---|
| RISK-01 | Sin red, la app no puede saber si el dispositivo se revocó en el servidor; la copia se sigue viendo con la huella del titular hasta la siguiente conexión | THR-06 | LOW | MEDIUM | LOW | ACCEPT | Bajo: se requiere la huella del titular y la copia se borra al primer 401 | ACCEPTED |
| RISK-02 | Con el teléfono desbloqueado y la app abierta, la frase en memoria o la pantalla pueden capturarse en un teléfono comprometido | THR-02 | LOW | HIGH | MEDIUM | ACCEPT | Medio: requiere un teléfono comprometido; FLAG_SECURE va en el endurecimiento del móvil | ACCEPTED |
| RISK-03 | Las pólizas se buscan solo por número de documento, sin el tipo; dos personas con el mismo número y distinto tipo verían las pólizas de la otra | THR-01 | LOW | HIGH | MEDIUM | ACCEPT | Bajo: colisión rara entre tipos de documento; se corrige cuando la póliza guarde el tipo | ACCEPTED |

## 16. Pending decisions

N/A: las decisiones de esta historia se tomaron el 2026-10-22 y están en spec.md.
