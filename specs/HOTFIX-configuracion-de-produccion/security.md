# Security and privacy assessment · HOTFIX

## 1. Data inventory and classification

| ID | Data | Classification | Personal | Sensitive | Purpose |
|---|---|---|---|---|---|
| DATA-01 | Llave de firma de tokens (JWT_SECRET_KEY) | RESTRICTED | NO | NO | Firmar y verificar los tokens de asesores y asegurados |
| DATA-02 | Llave del MAC del código de un solo uso (OTP_SECRET_KEY) | RESTRICTED | NO | NO | Guardar los códigos como MAC y verificarlos |
| DATA-03 | Contraseña maestra de RDS (DB_PASSWORD) | RESTRICTED | NO | NO | Conectar el backend con PostgreSQL |
| DATA-04 | Tokens de acceso y de refresco | RESTRICTED | NO | NO | Autenticar cada solicitud |
| DATA-05 | Códigos de un solo uso | RESTRICTED | NO | NO | Segundo factor y recuperación de contraseña |
| DATA-06 | Credenciales de las cuentas sembradas, ficticias y publicadas en el repositorio | RESTRICTED | NO | NO | Probar el portal y la app fuera de production |

## 2. Data lifecycle

### DATA-01, DATA-02, DATA-03 · Llaves y contraseña de RDS

| Question | Answer |
|---|---|
| What it contains | Dos llaves aleatorias de 32 caracteres o más y la contraseña maestra de RDS |
| Why it is needed | Firmar tokens, proteger los códigos y conectar el backend con la base |
| Who can access it | Administradores del repositorio (secretos de GitHub), el job de despliegue, quien pueda leer la definición de tarea de ECS o el estado de Terraform en la cuenta de AWS, y el proceso del backend |
| Where it is captured | Las genera una persona y las guarda con `gh secret set` sin mostrarlas; en local, en backend/.env |
| How it is transmitted | De GitHub al runner como variables de entorno enmascaradas; del runner a AWS por las API de AWS sobre TLS |
| Where it is stored | Secretos cifrados de GitHub, estado de Terraform en S3, definición de tarea de ECS y backend/.env local (ignorado por git) |
| Copies, caches and backups | Versiones anteriores del estado en el bucket versionado y revisiones anteriores de la definición de tarea |
| How long it is kept | Hasta que se cambien; las revisiones y versiones anteriores conservan los valores viejos |
| How access is audited | Historial de ejecuciones de GitHub Actions e historial de eventos de CloudTrail de la cuenta |
| How it is deleted or anonymized | Se reemplaza el secreto en GitHub y se despliega; las revisiones viejas de la tarea se desregistran a mano |
| What happens if it leaks | Con una llave se fabrican tokens o se verifican códigos: se generan llaves nuevas y se despliega, lo que cierra todas las sesiones. Con la contraseña se entra a la base solo desde la red del backend: se cambia el secreto y se despliega |
| Transfers to third parties | GitHub guarda los secretos y AWS el estado y la tarea, como proveedores del pipeline y de la nube |

### DATA-04, DATA-05 · Tokens y códigos de un solo uso

| Question | Answer |
|---|---|
| What it contains | Tokens HS256 con sujeto, rol, tipo y vencimiento; códigos de 6 dígitos guardados como HMAC-SHA256 |
| Why it is needed | Autenticar solicitudes y verificar el segundo factor o la recuperación |
| Who can access it | El cliente que los recibe y el backend |
| Where it is captured | Al iniciar sesión y al pedir un código |
| How it is transmitted | Cabecera Authorization y cuerpo JSON a través de CloudFront y el balanceador; entre ambos va por HTTP hasta el hotfix 2 |
| Where it is stored | Tokens en el cliente; los códigos solo como MAC en PostgreSQL |
| Copies, caches and backups | Respaldos de RDS para los MAC de los códigos; los tokens no se guardan en el servidor |
| How long it is kept | Acceso 15 minutos, refresco 7 días, códigos 5 minutos |
| How access is audited | Intentos de inicio de sesión registrados sin el código ni el token |
| How it is deleted or anonymized | Vencen; los códigos se marcan como usados |
| What happens if it leaks | Un token permite actuar como su dueño hasta que vence; un código, iniciar sesión o cambiar la contraseña dentro de su vigencia |
| Transfers to third parties | Ninguna mientras el SMS esté en console |

### DATA-06 · Cuentas sembradas

| Question | Answer |
|---|---|
| What it contains | Usuario, contraseña y secreto TOTP del asesor de prueba, y correo, teléfono, documento y contraseña de los asegurados de prueba, todos ficticios |
| Why it is needed | Probar el portal y la app sin crear usuarios a mano |
| Who can access it | Cualquiera: están en el repositorio público |
| Where it is captured | En el código del backend y en backend/seeds |
| How it is transmitted | En la imagen del contenedor; se insertan al arrancar |
| Where it is stored | Código, imagen y PostgreSQL, con la contraseña en bcrypt |
| Copies, caches and backups | Respaldos de RDS e historial de git |
| How long it is kept | Mientras el ambiente no sea production |
| How access is audited | Intentos de inicio de sesión registrados |
| How it is deleted or anonymized | Se borran de la base; con ENVIRONMENT=production no se vuelven a crear |
| What happens if it leaks | Ya son públicas: cualquiera inicia sesión como una cuenta de prueba (RISK-01) |
| Transfers to third parties | Ninguna |

## 3. Actors and roles

| Actor | Role | Trust level | What they can do |
|---|---|---|---|
| Pipeline de despliegue | GitHub Actions | Confiable con los secretos de CI | Aplicar Terraform y desplegar la tarea |
| Desarrollador | Equipo | Confiable en su ambiente local | Definir sus llaves en backend/.env |
| Asesor | advisor | Autenticado | Usar el portal con tokens firmados |
| Asegurado | insured | Autenticado | Usar la app con tokens firmados |
| Persona con acceso a la cuenta de AWS | Operación | Confiable | Leer la definición de tarea y el estado de Terraform |
| Atacante externo | Ninguno | No confiable | Llamar la API pública y leer el repositorio |
| Sitio web ajeno | Ninguno | No confiable | Hacer que el navegador de un asesor llame la API |

## 4. Trust boundaries

| Boundary | Between | What is validated when crossing it |
|---|---|---|
| CI hacia la nube | GitHub Actions y AWS | Credenciales del pipeline; los secretos llegan como variables sensibles validadas por Terraform |
| Arranque del backend | Entorno del contenedor y la aplicación | Llaves presentes, de 32 caracteres o más y distintas; si no, no arranca |
| API pública | Internet y el backend | Firma y vencimiento del token con la llave del ambiente |
| Navegador | Sitios ajenos y la API | Origen contra CORS_ORIGINS, sin credenciales |

## 5. Data flows

| Source | Destination | Data | Channel | Protection |
|---|---|---|---|---|
| Secretos de GitHub | Job de Terraform | DATA-01, DATA-02, DATA-03 | Variables de entorno enmascaradas | CRY-01, CTL-05 |
| Job de Terraform | Estado en S3 y tarea de ECS | DATA-01, DATA-02, DATA-03 | API de AWS sobre TLS | CRY-01, CTL-04 |
| Entorno del contenedor | Backend | DATA-01, DATA-02 | Variables de entorno | CTL-01, CTL-03 |
| Backend | Cliente | DATA-04 | HTTP a través de CloudFront | CRY-02 |
| Backend | PostgreSQL | DATA-05 | Conexión de la VPC | CRY-03 |

## 6. Third-party services

N/A: el cambio no agrega servicios externos; GitHub y AWS ya alojan el pipeline y el sistema.

## 7. Attack surface

| Surface | Exposure | Inputs the attacker controls |
|---|---|---|
| /api/v1/* | Pública | Tokens, cuerpos y cabeceras, incluida Origin |
| /api/v1/quote-edge/* | Pública | Cuerpo y X-Partner-Id; ahora responde 404 |
| /docs, /redoc, /openapi.json | Pública fuera de production | Ninguna; exponen el contrato |
| Repositorio público | Pública | Lectura del código y de su historial |
| Configuración al arrancar | Interna | Variables de entorno del contenedor |

## 8. Threat model

| ID | STRIDE | Asset | Threat | Actor | Likelihood | Impact | Risk | Controls |
|---|---|---|---|---|---|---|---|---|
| THR-01 | S, E | DATA-01 | Fabricar tokens de asesor o asegurado con la llave publicada en el repositorio | Atacante externo | HIGH | CRITICAL | CRITICAL | CTL-01 |
| THR-02 | S | DATA-02 | Calcular o verificar códigos con la llave de los tokens | Atacante externo | LOW | HIGH | MEDIUM | CTL-02 |
| THR-03 | I | DATA-01, DATA-02, DATA-03 | Valores de los secretos en el error de arranque y en CloudWatch | Persona con acceso a los logs | MEDIUM | HIGH | HIGH | CTL-03 |
| THR-04 | I | DATA-04 | Un sitio ajeno lee respuestas de la API desde el navegador de un asesor | Sitio web ajeno | LOW | MEDIUM | LOW | CTL-06 |
| THR-05 | E | Motor de tarifas | Cotizar sin autenticación por el canal de socios | Atacante externo | HIGH | MEDIUM | HIGH | CTL-07 |
| THR-06 | I | DATA-03 | Usar la contraseña de RDS publicada como valor por defecto | Atacante con acceso a la red de la VPC | LOW | HIGH | MEDIUM | CTL-04, CTL-05 |
| THR-07 | S, I | DATA-05, DATA-06 | Entrar como una cuenta de prueba o cambiar su contraseña con el código devuelto en la respuesta | Atacante externo | HIGH | MEDIUM | HIGH | CTL-08 |
| THR-08 | I | DATA-01, DATA-02, DATA-03 | Leer los secretos desde la definición de tarea de ECS o el estado de Terraform | Persona con acceso a la cuenta de AWS | LOW | HIGH | MEDIUM | CTL-05 |

## 9. Controls

| ID | Control | Domain | Status | Mitigates | Tests | Tasks | References | Rationale |
|---|---|---|---|---|---|---|---|---|
| CTL-01 | Llaves obligatorias sin valor por defecto, de 32 caracteres o más y distintas, validadas al arrancar | BACKEND, SECRETS | EXISTING | THR-01 | TC-01, TC-02, TC-03, TC-09 | T-01 | ASVS 5.0 V13, CWE-798, CWE-1188 | — |
| CTL-02 | Llave propia para el MAC del código de un solo uso | CRYPTO | EXISTING | THR-02 | TC-04 | T-02 | CWE-320 | — |
| CTL-03 | Error de configuración que nombra campos sin valores ni excepción encadenada | BACKEND | EXISTING | THR-03 | TC-01, TC-02, TC-03 | T-01 | CWE-209, CWE-532 | — |
| CTL-04 | Variables sensibles de Terraform sin valor por defecto y validadas | INFRA, SECRETS | EXISTING | THR-06 | TC-10 | T-04 | CWE-798 | — |
| CTL-05 | Secretos inyectados desde los secretos cifrados de CI en deploy y destroy | INFRA | EXISTING | THR-06, THR-08 | TC-10 | T-05 | CWE-522 | — |
| CTL-06 | CORS por lista de orígenes y sin credenciales | WEB, API | EXISTING | THR-04 | TC-07 | T-03 | CWE-942 | — |
| CTL-07 | Canal de socios sin autenticación desmontado | API | EXISTING | THR-05 | TC-06 | T-03 | API2:2023, CWE-306 | — |
| CTL-08 | Código en la respuesta, cuentas sembradas y documentación solo fuera de production | BACKEND | EXISTING | THR-07 | TC-05, TC-08 | T-03 | CWE-489 | — |
| CTL-09 | Aislamiento entre inquilinos | DATA | NOT APPLICABLE | — | — | — | — | No hay inquilinos y el canal de socios queda apagado |

## 10. Cryptography

### CRY-01 · Secretos en CI y en la nube

| Field | Value |
|---|---|
| Protects | DATA-01, DATA-02, DATA-03 |
| Type | AT_REST |
| Algorithm or service | Secretos cifrados de GitHub Actions; estado de Terraform en S3 con cifrado del lado del servidor administrado por AWS (AES-256) |
| Rationale | Mantener los valores fuera del código y de los artefactos |
| Key management | GitHub y AWS administran las llaves de cifrado de cada servicio |
| Permissions | Administradores del repositorio; usuario de despliegue y administradores de la cuenta de AWS |
| Rotation | Manual: valor nuevo en GitHub y despliegue |
| Recovery | Generar valores nuevos y desplegar; las sesiones inician de nuevo |
| Failure behavior | Si falta un valor, Terraform falla la validación sin cambiar nada y el backend no arranca |
| Tests | TC-10 |

### CRY-02 · Firma de tokens

| Field | Value |
|---|---|
| Protects | DATA-04 |
| Type | MAC |
| Algorithm or service | HMAC-SHA256 (HS256) con JWT_SECRET_KEY |
| Rationale | Integridad y autenticidad de tokens que emite y verifica el mismo backend |
| Key management | Variable de entorno por ambiente desde los secretos de CI; 32 caracteres o más |
| Permissions | Proceso del backend; lectores de la tarea de ECS y del estado (RISK-02) |
| Rotation | Al sospechar una filtración; cambiarla invalida todas las sesiones |
| Recovery | Llave nueva y nuevo inicio de sesión |
| Failure behavior | Token firmado con otra llave o alterado: 401 |
| Tests | TC-09 |

### CRY-03 · MAC de los códigos de un solo uso

| Field | Value |
|---|---|
| Protects | DATA-05 |
| Type | MAC |
| Algorithm or service | HMAC-SHA256 con OTP_SECRET_KEY |
| Rationale | Guardar el código sin poder leerlo y separado de la llave de tokens |
| Key management | Variable de entorno por ambiente desde los secretos de CI, distinta de JWT_SECRET_KEY |
| Permissions | Proceso del backend; lectores de la tarea de ECS y del estado (RISK-02) |
| Rotation | Al sospechar una filtración; cambiarla invalida los códigos pendientes |
| Recovery | Llave nueva; el usuario pide otro código |
| Failure behavior | Código calculado con otra llave: no coincide y se rechaza |
| Tests | TC-04 |

### CRY-04 · Contraseñas de las cuentas sembradas

| Field | Value |
|---|---|
| Protects | DATA-06 |
| Type | PASSWORD_HASH |
| Algorithm or service | bcrypt (sin cambios en este hotfix) |
| Rationale | La base no guarda contraseñas en claro |
| Key management | No usa llave; sal por contraseña |
| Permissions | Proceso del backend |
| Rotation | No aplica; la migración a Argon2id va en HU-WEB-13 |
| Recovery | Restablecer la contraseña |
| Failure behavior | Contraseña incorrecta: 401 genérico |
| Tests | TC-11 |

## 11. Secrets and keys

| Secret | Location | Access | Environments | Rotation | Revocation | Leak detection |
|---|---|---|---|---|---|---|
| JWT_SECRET_KEY | Secreto de GitHub, variable de Terraform, entorno de ECS; backend/.env en local | Administradores del repositorio, job de despliegue, lectores de ECS y del estado | AWS y cada ambiente local, con valores distintos | Manual: secreto nuevo y despliegue | Cambiarla invalida todos los tokens | sdd scan secrets en cada pull request |
| OTP_SECRET_KEY | Igual que JWT_SECRET_KEY | Igual que JWT_SECRET_KEY | AWS y cada ambiente local, con valores distintos | Manual: secreto nuevo y despliegue | Cambiarla invalida los códigos pendientes | sdd scan secrets en cada pull request |
| DB_PASSWORD | Secreto de GitHub, variable de Terraform, RDS y entorno de ECS | Administradores del repositorio, job de despliegue, lectores de ECS y del estado | AWS; en local se usa la de docker-compose | Manual: valor nuevo y despliegue, que actualiza RDS | Cambiarla corta las conexiones hasta que arranca la tarea nueva | sdd scan secrets en cada pull request |

## 12. Authentication, authorization and sessions

| Check | Applies | Controls | Rationale |
|---|---|---|---|
| User identification | YES | CTL-01 | — |
| Secure authentication | YES | CTL-02 | — |
| Session management | NO | — | El manejo de sesiones no cambia |
| Token expiration | NO | — | Los vencimientos no cambian |
| Revocation | YES | CTL-01 | — |
| Server-side permission checks | NO | — | Los permisos no cambian |
| Per-resource access (ownership) | NO | — | Sin cambios; la propiedad por recurso va en HU-WEB-05 y HU-WEB-06 |
| Roles | NO | — | Los roles no cambian |
| Privilege separation | NO | — | Sin cambios |
| Brute-force protection | NO | — | Los bloqueos no cambian |
| Rate limiting | NO | — | Los límites no cambian |
| One-time code (OTP) handling | YES | CTL-02, CTL-08 | — |
| User enumeration prevention | NO | — | Sin cambios; los hallazgos de enumeración van en HU-WEB-13 y HU-MOV-02 |
| CSRF protection | NO | — | Tokens en cabecera, sin cookies, y CORS sin credenciales |

## 13. Data isolation and multi-tenancy

N/A: no hay inquilinos; el canal de socios, única entrada con identificador de socio, queda apagado.

## 14. Dependencies

| ID | Dependency | Version | Component | Use | Criticality | Evaluation | Result | Status |
|---|---|---|---|---|---|---|---|---|
| DEP-01 | pydantic | 2.13.5 | backend | SecretStr y validación de configuración | HIGH | OSV.dev 2026-10-22 | No known vulnerabilities | EVALUATED |
| DEP-02 | pydantic-settings | 2.15.0 | backend | Carga de configuración desde el entorno | HIGH | OSV.dev 2026-10-22 | No known vulnerabilities | EVALUATED |
| DEP-03 | pyjwt | 2.15.1 | backend | Firma y verificación HS256 | CRITICAL | OSV.dev 2026-10-22 | No known vulnerabilities | EVALUATED |

## 15. Risk register and residual risk

| ID | Risk | Threats | Likelihood | Impact | Level | Treatment | Residual risk | Status |
|---|---|---|---|---|---|---|---|---|
| RISK-01 | El ambiente de AWS sigue sin ENVIRONMENT: entrega el código en la respuesta, siembra cuentas con credenciales públicas y sirve la documentación; quien conozca un correo de prueba entra o cambia su contraseña | THR-07 | HIGH | MEDIUM | HIGH | ACCEPT | Alto mientras el ambiente tenga solo datos ficticios; desaparece con ENVIRONMENT=production y un proveedor de SMS | ACCEPTED |
| RISK-02 | Llaves y contraseña viajan como variables de entorno: legibles en la definición de tarea de ECS y en el estado de Terraform | THR-08 | LOW | HIGH | MEDIUM | ACCEPT | Medio; desaparece con un gestor de secretos (nueva ADR) | ACCEPTED |
| RISK-03 | La contraseña de RDS no se rota: si se reutiliza, el valor publicado en el historial de git sigue vigente | THR-06 | LOW | HIGH | MEDIUM | ACCEPT | Medio; la base solo acepta conexiones del grupo de seguridad del backend | ACCEPTED |
| RISK-04 | Si JWT_SECRET_KEY reutiliza la llave publicada, cualquiera sigue fabricando tokens | THR-01 | LOW | CRITICAL | HIGH | MITIGATE | Bajo: las llaves se generaron nuevas al crear los secretos (T-07) | MITIGATED |

## 16. Pending decisions

| ID | Decision | Options | Recommendation | Decider | Blocks gate | Status |
|---|---|---|---|---|---|---|
| DEC-01 | Valores de JWT_SECRET_KEY y OTP_SECRET_KEY en AWS | Generar llaves nuevas; reutilizar la publicada | Generar llaves nuevas con los comandos del README (sección 8.5) | Responsable del despliegue | YES | APPROVED |
