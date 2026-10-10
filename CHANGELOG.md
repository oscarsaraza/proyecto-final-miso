# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- `get_password_hash` y `verify_password` usan `bcrypt` directamente: `passlib` 1.7.4 fallaba con `bcrypt` 5.0.0 (versión del lock).
- Corrección en `backend/Dockerfile` aislando las dependencias en un entorno virtual (`/opt/venv`), configurando el directorio de inicio del usuario `appuser` y adaptando el sondeo de salud (`healthcheck`) para resolver el error `ModuleNotFoundError: No module named 'uvicorn'` al iniciar el backend mediante Docker Compose.

### Changed
- Actualización de la documentación en `README.md` y `backend/README.md`, sustituyendo la referencia residual de LocalStack por Floci e incorporando instrucciones explícitas para la ejecución del servidor backend mediante Poetry (`uvicorn`) y Docker Compose.

### Added
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
