# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Corrección en `.github/workflows/destroy.yml` asignando `working-directory: terraform` exclusivamente a los pasos que invocan Terraform, evitando errores de inicialización de shell previos al paso de `checkout` del repositorio.
- `get_password_hash` y `verify_password` usan `bcrypt` directamente: `passlib` 1.7.4 fallaba con `bcrypt` 5.0.0 (versión del lock).
- Corrección en `backend/Dockerfile` aislando las dependencias en un entorno virtual (`/opt/venv`), configurando el directorio de inicio del usuario `appuser` y adaptando el sondeo de salud (`healthcheck`) para resolver el error `ModuleNotFoundError: No module named 'uvicorn'` al iniciar el backend mediante Docker Compose.

### Changed
- Habilitación del disparador manual `workflow_dispatch` en el workflow de despliegue continuo (`.github/workflows/deploy.yml`) permitiendo aprovisionar y desplegar la plataforma bajo demanda sin requerir commits vacíos en `main`.
- Adición de `force_destroy = true` a los buckets S3 (`aws_s3_bucket.documents` y `aws_s3_bucket.web`) y `force_delete = true` al repositorio ECR (`aws_ecr_repository.backend`) en Terraform para garantizar un desaprovisionamiento limpio y sin bloqueos ante objetos o imágenes existentes.
- Actualización de la documentación en `README.md` incorporando la guía de uso del workflow de apagado/destrucción y reestructurando la sección de CI/CD.
- `README.md` y `backend/README.md`: ejecución del backend sin Poetry, endpoints de autenticación del asegurado, conexión de la app con el backend local, emulador con huella y nueva guía de pruebas manuales en `docs/GUIA-PRUEBAS-SPRINT1.md`.
- Actualización de apariencia del Portal Web (`web`) con el sistema de diseño del prototipo (`prototipos/web`).
- Configuración de persistencia de estado para Terraform mediante Remote Backend en Amazon S3 en el workflow de despliegue (`.github/workflows/deploy.yml`) y `terraform/versions.tf`, garantizando que `terraform.tfstate` persista entre runners efímeros de GitHub Actions.
- Actualización de archivo `README.md` con permisos adicionales requeridos para el despliegue con el workflow de CD desde Github (`application-autoscaling`, `cloudwatch`, `kms`).
- Actualización de la documentación en `README.md` y `backend/README.md`, sustituyendo la referencia residual de LocalStack por Floci e incorporando instrucciones explícitas para la ejecución del servidor backend mediante Poetry (`uvicorn`) y Docker Compose.

### Added
- **HU-WEB-02 · Capturar los datos del cliente y solicitar la cotización:**
  - Backend: `POST /api/v1/experience/clients/validate` para validación de asegurabilidad por edad (`TC-S1-03`) en el rango de 18 a 75 años con `ProfileService.validate_insurable_age()`, cálculo determinístico y excepción `IneligibleAgeError` (HTTP 400 Bad Request).
  - Web: componente `ClientDataStepComponent` (Paso 1) en el cotizador con captura de datos personales del titular y condiciones del crédito hipotecario, cálculo dinámico y validación interactiva de edad en el formulario, formateo en pesos colombianos COP y validación con el BFF.
  - Servicio `ClientService` para validación sociodemográfica de asegurabilidad.
  - Integración comercial guiada en `CotizadorComponent`: transferencia fluida hacia consentimiento (`ConsentStepComponent`), resumen visible del titular y monto asegurado, solicitud automática de cotización con `QuoteService.createQuote()` tras autorizar consentimiento, despliegue del desglose explicativo de la prima (`app-premium-breakdown`) y soporte de recotización sin recargar la página.
  - Pruebas: suite `TC-S1-03` en backend con pruebas parametrizadas de límites de edad (17, 18, 40, 75 y 76 años), pruebas de integración de endpoint protegido con rol `advisor` y validación de esquemas (116 pruebas aprobadas con 97 % de cobertura), y 73 pruebas unitarias en frontend con Angular y Vitest.
- **HU-WEB-01 · Registrar el consentimiento de tratamiento de datos:**
  - Backend: `POST /api/v1/experience/consent` y `GET /api/v1/experience/consent/{document_number}` con generación de hash SHA-256 canónico inalterable para auditoría (RC-01 / RC-04), validación estricta de OTP numérico (`^\d{6}$`), vigencia configurable con reloj inyectable para expiración determinística y aislamiento de estado en `ProfileService`.
  - Web: componente `ConsentStepComponent` en el cotizador con indicación de finalidad, alcance y vigencia por el asesor, sincronización reactiva de documento con `linkedSignal`, validación numérica y atributos modernos de formulario (`sms-otp-form`), detalle de fuentes consultadas (Open Finance, Burós, KYC), verificación OTP simulada y visualización del hash SHA-256 de auditoría.
  - Servicio `ConsentService` para comunicación con el BFF de experiencia.
  - Pruebas: suite `TC-S1-04` en backend con pruebas unitarias de expiración determinística y rechazo de campos inválidos, prueba de integración dedicada en `test_health_and_api.py`, y pruebas unitarias con Vitest (62 pruebas pasando).
- **HU-WEB-06 · Cobrar la prima sin duplicar el cobro:**
  - Backend: `POST /payments/charge` exige `Idempotency-Key` y cobra la primera prima mensual con una pasarela simulada, con la póliza bloqueada y en una sola transacción: si se aprueba, la póliza pasa a `ACTIVE` con recibo `REC-YYYY-XXXXX` y evento `PaymentApproved` en el outbox; la misma clave repite la respuesta sin otro cargo, un rechazo responde 402 con el motivo y una póliza ya pagada, 409.
  - Web: paso de pago debajo de la póliza emitida, con PSE o tarjeta y una clave por intento que se conserva en los reintentos; muestra el recibo o el motivo del rechazo.
  - Pruebas TC-S1-08 contra PostgreSQL (reintento, corte después de cobrar, rechazo, 10 cobros simultáneos y atomicidad) y Vitest del paso de pago.
- Workflow de Destrucción y Apagado de Infraestructura AWS (`.github/workflows/destroy.yml`) ejecutable bajo demanda con `workflow_dispatch` y confirmación de seguridad para desaprovisionar todos los recursos gestionados por Terraform y reducir a \$0 los costos fijos por hora (NAT Gateway, ALB, RDS Multi-AZ y ECS Fargate).
- **HU-WEB-05 · Aceptar la cotización y emitir la póliza:**
  - Backend: guarda cada cotización y emite la póliza `POL-YYYY-XXXXX` con un año de vigencia y su evento `PolicyIssued` en el outbox, en una sola transacción; repetir la emisión devuelve la misma póliza y una cotización vencida responde 409.
  - Web: botón «Emitir póliza» con la confirmación, y aviso de cotización vencida con «Recotizar con datos actuales».
  - Pruebas TC-S1-07 contra PostgreSQL, ahora también en el CI, y Vitest de la emisión.
- **HU-WEB-04 · Cotización con perfil parcial:**
  - Backend: si el buró supera 400 ms, cotiza con puntaje neutro y recargo del 4 %, y responde `status="degraded"` con `degradation_reason="TIMEOUT_EXCEEDED"`.
  - Web: banner ámbar con `role="alert"` para cotizaciones degradadas.
  - Pruebas TC-S1-06 y Vitest del banner.
- **HU-MOV-12 · Cierre de sesión seguro y revocación móvil:**
  - Backend: `POST /api/v1/auth/logout` revoca el refresh token (lista negra por `jti`) y `POST /api/v1/auth/refresh` rechaza los revocados y rota el token en cada uso.
  - App: confirmación modal, purga de tokens y llave del Keystore, regreso a la bienvenida y revocación en el servidor (de mejor esfuerzo sin red).
  - Pruebas TC-S1-12 en backend y en `AuthViewModel`.
- **HU-MOV-02 · Acceso alternativo con contraseña y segundo factor:**
  - Backend: `POST /api/v1/auth/otp` y `POST /api/v1/auth/login` para el asegurado, con código de 6 dígitos de un solo uso (5 min), bloqueo de 15 minutos al tercer intento fallido (HTTP 423) y emisión de access y refresh token. En desarrollo el código se devuelve como `debug_code` para simular el SMS.
  - App: pantalla de acceso alternativo, cliente HTTP del BFF y oferta de activar la biometría tras ingresar, que guarda la sesión cifrada (HU-MOV-03).
  - Pruebas TC-S1-10 en backend (unitarias e integración) y en `AuthViewModel`.
- **HU-MOV-03 · Credenciales en el almacén protegido del dispositivo:**
  - Llave AES-256-GCM en Android Keystore que exige biometría fuerte en cada uso y se invalida al registrar nuevas huellas o rostros.
  - `SecureSessionRepository`: guarda los tokens cifrados, los desbloquea con el `CryptoObject` de `BiometricPrompt` y sobrescribe en memoria el texto plano.
  - Si la llave se invalida o la sesión guardada se altera, la sesión se descarta y se pide ingresar con contraseña y código.
  - Pruebas unitarias TC-S1-11 sobre el repositorio y el flujo de desbloqueo en `AuthViewModel`.
- **HU-MOV-01 · Acceso biométrico en la app móvil:**
  - Pantalla M1 en Jetpack Compose con tema de marca e íconos del prototipo; el diálogo biométrico se lanza al abrir la app.
  - Puerto `BiometricAuthenticator` e implementación con `BiometricPrompt` restringida a biometría fuerte (`BIOMETRIC_STRONG`).
  - Manejo de sensor ausente, sin huella o rostro registrados, cancelación y bloqueo por intentos, orientando al acceso alternativo (HU-MOV-02).
  - Pruebas unitarias TC-S1-09 sobre `AuthViewModel` y el mapeo de códigos de `BiometricPrompt`.
- **HU-WEB-03 · Desglose explicativo de la prima:**
  - Backend: `calculate_quote` calcula en memoria los planes básico, estándar y premium con el aporte en pesos de la tarifa base y de los ajustes por edad, ocupación, historial de pago y plan; la suma del desglose es exactamente la prima mensual. El buró usa un puntaje neutro hasta HU-WEB-04.
  - Web: `QuoteService` contra `POST /api/v1/experience/quotes`, componente `app-premium-breakdown` con recargos, descuentos y multiplicadores, y selector de plan en el cotizador.
  - Pruebas TC-S1-05 en el motor de tarifa y pruebas Vitest del desglose, el servicio y el cotizador.
- Implementación integral de la historia de usuario **HU-WEB-13: Login y Sesión del Asesor Comercial en el Portal Web**:
  - Modelo relacional `UserDB` en SQLAlchemy con hash seguro bcrypt (`HA-06`) y esquemas Pydantic para endpoints de autenticación y renovación de sesión.
  - Implementación de segundo factor TOTP conforme a RFC 6238 en Python nativo con tolerancia temporal de $\pm 30$ segundos (`HA-06`).
  - Mitigación de fuerza bruta y enumeración de cuentas mediante bloqueo temporal de 15 minutos (HTTP 423 Locked) tras 5 intentos fallidos consecutivos, y mensaje de error genérico.
  - Endpoints BFF `/api/v1/experience/auth/login` y `/api/v1/experience/auth/refresh` con generación de tokens JWT (`access_token` con expiración de 15 min y `refresh_token` de 7 días).
  - Control de acceso por roles RBAC (`HA-13`) mediante la dependencia `require_roles(["advisor"])` asegurando los endpoints comerciales del portal.
  - Inicialización de tablas y siembra del usuario asesor comercial semilla (`asesor@solventa.com` / `SuperSecreta2026*`) mediante gestor de ciclo de vida `lifespan` en FastAPI.
  - Servicio Angular `AuthService` con señales reactivas (`signal`), almacenamiento seguro en `sessionStorage` y métodos `login`, `refreshToken` e `isAuthenticated`.
  - Interceptor HTTP `jwtInterceptor` con inyección de cabecera Bearer y renovación silenciosa transparente ante errores 401.
  - Guard de rutas `authGuard` protegiendo `/cotizador` con redirección a `/login` preservando `returnUrl`.
  - Formulario reactivo `LoginComponent` con manejo visual de estados de carga, error 401 y bloqueo 423.
  - Barra de navegación en `AppComponent` con visualización del nombre del asesor autenticado y acción de cierre de sesión (`logout`).
  - Configuración de proxy inverso de desarrollo (`web/proxy.conf.json`) para reenvío automático de `/api` hacia `localhost:8000`.
- Script de automatización [`scripts/setup-aws-secrets.sh`](scripts/setup-aws-secrets.sh) para ingreso interactivo o lectura de perfil de AWS CLI, verificación de identidad con AWS STS y sincronización desatendida de credenciales IAM de AWS hacia GitHub Actions usando GitHub CLI (`gh`).
- Workflow de Integración Continua en GitHub Actions (`.github/workflows/ci.yml`) ejecutando pruebas automatizadas en cada commit y branch:
  - `backend-ci`: Python 3.12, Poetry y Pytest con validación de cobertura mínima.
  - `web-ci`: Node.js 22, npm test con Vitest y build de producción de Angular 22.
  - `mobile-ci`: Java 17 LTS y Gradle ejecutando `testDebugUnitTest` para Android nativo.
  - `terraform-ci`: `terraform fmt -check` y `terraform validate`.
- Workflow de Despliegue Continuo a AWS en GitHub Actions (`.github/workflows/deploy.yml`) ejecutado exclusivamente ante cambios en la rama `main`:
  - `deploy-infra`: Sincronización de infraestructura Multi-AZ con Terraform.
  - `deploy-backend`: Compilación y subida de imagen Docker a ECR con despliegue progresivo en ECS Fargate.
  - `deploy-web`: Despliegue de estáticos de Angular en S3 con invalidación de caché en CloudFront.
- Workflow de Despliegue Local Simulado (`.github/workflows/deploy-local.yml`) y script de automatización (`scripts/deploy-local.sh`) para ejecutar pruebas de despliegue integrales contra Floci emulando el entorno de producción de AWS sin costos de nube.
- Infraestructura como Código (IaC) modular en `/terraform` para AWS Multi-AZ (`us-east-1`):
  - Módulo VPC (`10.0.0.0/16`) con subredes públicas y privadas en `us-east-1a` y `us-east-1b`, Internet Gateway y NAT Gateway.
  - Módulo ALB con sondeo activo en `/health` cada 5s y tolerancia a fallos (`HA-09`).
  - Módulo ECS Fargate para `solventa-backend` con auto-escalado horizontal de 2 a 6 instancias según carga de CPU (`HA-06`).
  - Módulo RDS PostgreSQL 16 Multi-AZ (`multi_az = true`) con almacenamiento cifrado con KMS (`HA-15`).
  - Módulo de almacenamiento y eventos con bucket S3 versionado y cifrado SSE-KMS (`HA-08`), y cola SQS con Dead Letter Queue (DLQ).
  - Módulo ECR para registro de imágenes Docker del backend con escaneo de seguridad.
  - Módulo de hosting web con S3 y CloudFront con Origin Access Control (OAC) para el frontend Angular SPA.
  - Soporte para emulación local de servicios AWS con **Floci** (`floci.io/aws`), integrando `environments/local.tfvars` para planificar infraestructura sin costos de nube.
- Migración del emulador local en `docker-compose.yml` de LocalStack a **Floci** (`floci/floci:latest`), con montaje de socket Docker para emulación ligera con Quarkus Native.
- Configuración de `.mise.toml` para gestión automatizada de Java 17 LTS, Gradle 8.10.2 y Android SDK con `mise`.
- Estructura base de la aplicación móvil para asegurados en `/movil` con Android nativo (Android 13+ / minSdk 33), Kotlin 2.1.0 y Jetpack Compose.
- Arquitectura limpia y MVVM con `AuthViewModel`, modelos de dominio (`Policy`, `UserSession`) y gestor de persistencia segura `EncryptedStorageManager` (SQLCipher).
- Métodos placeholder estructurados que lanzan `NotImplementedError` para biometría (`HU-MOV-01`), PIN (`HU-MOV-02`), almacén cifrado (`HU-MOV-03`) y logout (`HU-MOV-12`).
- Suite de pruebas unitarias con JUnit 4/5 y MockK en `movil/app/src/test/` con validación de estado inicial y excepciones de placeholder.
- Estructura base del Portal Web para Asesores Comerciales en `/web` con Angular 22 (Standalone Components, Vitest, esbuild).
- Configuración de rutas (`/login`, `/cotizador`) y componentes con placeholders de interfaz de usuario (`LoginComponent` para `HU-WEB-13` y `CotizadorComponent` para flujo comercial `HU-WEB-01..06`).
- Servicio de autenticación `AuthService` con métodos placeholder que lanzan excepciones explicativas previas a la implementación funcional.
- Interceptor HTTP funcional para inyección de token JWT (`jwtInterceptor`).
- Suite de pruebas unitarias en TypeScript (12 pruebas pasando con Vitest) validando instanciación, componentes y contratos del arnés base.
- Estructura base del Monolito Modular en Python 3.12 con FastAPI bajo Arquitectura Hexagonal y patrón BFF (`experience-edge` y `quote-edge`).
- Configuración y gestión de dependencias del backend centralizada con **Poetry** (`pyproject.toml` y `poetry.lock`).
- Endpoint de infraestructura `/health` para sondeo activo por parte del AWS Application Load Balancer (`HA-09`).
- Modelos de dominio y contratos DTO (Pydantic) para los módulos `rating`, `profile`, `policy`, `payments` y `claims`.
- Métodos de servicio y endpoints BFF estructurados como placeholders (`NotImplementedError` y HTTP 501) listos para la codificación progresiva de historias de usuario.
- Arnés técnico de pruebas con `pytest` ejecutado vía `poetry run pytest` (93% de cobertura), con casos de prueba de HU (`TC-S1-*`) preparados para TDD.
- Configuración inicial de entorno local base con `docker-compose.yml` (PostgreSQL 16 y LocalStack para emulación de S3/SQS).
- Archivo `.gitignore` con exclusiones para Python, Poetry, Node, Android, Terraform y secretos.
- Documentación inicial del proyecto en `README.md` con guías de arquitectura, ejecución local y configuración de secretos AWS.
