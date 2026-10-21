# Solventa · Seguros Digitales

Solventa es una aseguradora nativa digital diseñada para operar en la nube de AWS bajo los estándares colombianos de Finanzas y Datos Abiertos (Decreto 1297 de 2022 y Circular Externa 004 de 2024 de la Superfinanciera).

Su arquitectura implementa un **Monolito Modular API-First con Arquitectura Hexagonal (Puertos y Adaptadores)**, patrón **BFF (Backend for Frontend)** y persistencia transaccional sobre PostgreSQL 16 con CQRS ligero.

---

## 1. Estructura del Repositorio

| Directorio                                | Componente                                                        | Stack Tecnológico                                             |
| :---------------------------------------- | :---------------------------------------------------------------- | :------------------------------------------------------------ |
| [`/backend`](backend/)                    | Monolito Modular Backend (Core, Rating, Policy, Payments, Claims) | Python 3.12, FastAPI, Poetry, SQLAlchemy, asyncpg             |
| [`/web`](web/)                            | Portal Web para Asesores Comerciales                              | Angular 22, TypeScript, Standalone Components, Vitest         |
| [`/movil`](movil/)                        | Aplicación Móvil para Asegurados                                  | Android, Kotlin 2.1, Jetpack Compose, BiometricPrompt, Android Keystore, JUnit |
| [`/terraform`](terraform/)                | Infraestructura como Código (AWS Multi-AZ)                        | Terraform >= 1.5, AWS Provider (ALB, ECS, RDS, S3, SQS)       |
| [`.github/workflows`](.github/workflows/) | Pipelines de CI/CD                                                | GitHub Actions (CI en cada commit, CD a AWS en `main`)        |
| [`experiments/`](experiments/)            | Experimentos de arquitectura y validaciones de carga E1 y E3      | Python, k6, AWS Cloud                                         |
| [`docs/`](docs/)                          | Prototipos de navegación interactivos y guía de pruebas manuales  | HTML5, CSS3, JavaScript, Markdown                             |

---

## 2. Entorno de Desarrollo Local

El proyecto cuenta con un archivo [`docker-compose.yml`](docker-compose.yml) para ejecutar el backend y sus dependencias en local sin incurrir en costos de AWS:

- **PostgreSQL 16:** Base de datos relacional en `localhost:5432`.
- **Floci:** Emulación local de AWS S3 (almacenamiento de carátulas) y AWS SQS (cola de eventos) en `localhost:4566`.
- **Backend FastAPI:** Ingress y API en `localhost:8000`.

### 2.1 Iniciar infraestructura base (Base de datos y AWS local)

```bash
docker compose up -d postgres floci
```

### 2.2 Ejecución del Backend FastAPI

Existen dos alternativas para levantar el backend en desarrollo local:

#### Opción A: Ejecución nativa con Poetry (Recomendada para desarrollo con recarga activa)

Requiere tener los servicios base (`postgres` y `floci`) iniciados previamente.

```bash
cd backend

# 1. Instalar dependencias del proyecto
poetry install

# 2. Iniciar servidor FastAPI con recarga en caliente (hot reload)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Opción A.1: Sin Poetry (entorno virtual con `requirements.txt`)

Útil cuando Poetry no está disponible (por ejemplo, si Windows bloquea `poetry.exe` con Control de aplicaciones inteligente):

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt        # Windows (en Linux/macOS: .venv/bin/python)
.venv/Scripts/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Opción B: Ejecución en contenedor con Docker Compose

Levanta automáticamente PostgreSQL, Floci y el contenedor del backend (`solventa-backend`):

```bash
docker compose up -d
```

#### Verificación de la API

Una vez iniciado el backend, puede acceder a los siguientes puntos de enlace:
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **Documentación Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentación ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 2.3 Autenticación del Asegurado (canal móvil)

El BFF expone en `/api/v1/auth` el acceso del asegurado (HU-MOV-02 y HU-MOV-12):

| Endpoint | Descripción | Respuestas |
| :------- | :---------- | :--------- |
| `POST /api/v1/auth/otp` | Genera un código de 6 dígitos válido por 5 minutos (simula el SMS). No revela si el correo existe. | `200` |
| `POST /api/v1/auth/login` | Valida correo, contraseña y código de un solo uso. Al tercer intento fallido bloquea la cuenta 15 minutos. | `200` tokens · `401` credenciales inválidas · `423` cuenta bloqueada |
| `POST /api/v1/auth/refresh` | Renueva la sesión y rota el refresh token (cada uno se usa una sola vez). | `200` · `401` revocado o vencido |
| `POST /api/v1/auth/logout` | Revoca el refresh token (lista negra por `jti`). | `204` · `401` token inválido |

En `ENVIRONMENT=development`:
- `POST /auth/otp` devuelve el código en `debug_code` en lugar de enviar un SMS.
- Existe un asegurado de prueba: `maria.ruiz@correo.co` / `Solventa2026!`.

En producción ninguno de los dos está disponible.

### 2.4 Consentimiento de Tratamiento de Datos (HU-WEB-01)

El BFF expone en `/api/v1/experience` el registro y consulta del consentimiento informado para perfilamiento Open Finance (`RC-01` / `RC-04`):

| Endpoint | Descripción | Respuestas |
| :------- | :---------- | :--------- |
| `POST /api/v1/experience/consent` | Registra el consentimiento informado con hash SHA-256 canónico inalterable para auditoría, vigencia y validación OTP. Exige rol `advisor`. | `200` record · `400` sin términos u OTP inválido · `422` formato |
| `GET /api/v1/experience/consent/{document_number}` | Consulta el consentimiento activo registrado para el número de documento del cliente. Exige rol `advisor`. | `200` record · `404` no encontrado |

### 2.5 Validación de Asegurabilidad del Cliente (HU-WEB-02)

El BFF expone la verificación de asegurabilidad sociodemográfica por rango de edad (18 a 75 años) para el seguro de vida hipotecario (`TC-S1-03`):

| Endpoint | Descripción | Respuestas |
| :------- | :---------- | :--------- |
| `POST /api/v1/experience/clients/validate` | Valida que el tomador cumpla con el rango asegurable de 18 a 75 años según su fecha de nacimiento. Exige rol `advisor`. | `200` `{"status": "ELIGIBLE", "age": N}` · `400` fuera de rango · `422` formato |

### 2.6 Canal de Socios B2B — Quote Edge (HU-WEB-10)

El BFF expone en `/api/v1/quote-edge` el canal dedicado para socios de distribución B2B con autenticación OAuth2 *Client Credentials*, confinamiento estricto por `partner_id` y auditoría JSON de rechazos:

| Endpoint | Descripción | Respuestas |
| :------- | :---------- | :--------- |
| `POST /api/v1/quote-edge/auth/token` | Emite un JWT firmado con `role: "partner"` y `partner_id` a partir de `client_id` y `client_secret`. | `200` token · `401` credenciales inválidas o socio revocado |
| `POST /api/v1/quote-edge/quotes` | Calcula y persiste la cotización confinada al `partner_id` del socio autenticado e incrementa atómicamente `quota_used`. | `200` cotización · `401` token ausente, inválido o revocado |
| `GET /api/v1/quote-edge/quotes/{quote_id}` | Consulta una cotización individual verificando pertenencia estricta al socio autenticado. | `200` cotización · `401` no autorizado · `404` no existe o pertenece a otro socio |
| `GET /api/v1/quote-edge/quotes` | Lista el histórico de cotizaciones generadas exclusivamente por el socio autenticado (`created_at DESC`). | `200` listado · `401` no autorizado |

Socios semilla inicializados automáticamente en el arranque (`lifespan`):
- **Socio activo:** `client_id`: `banco_aliado` · `client_secret`: `AliadoSecret2026*` (`partner_id`: `banco-aliado-1`).
- **Socio revocado:** `client_id`: `socio_inactivo` · `client_secret`: `Inactivo2026*` (`partner_id`: `socio-inactivo-1`, estado `REVOKED`).

---

## 3. Ejecución de Pruebas Automatizadas del Backend (con Poetry)

El backend utiliza **Poetry** para la gestión estricta de dependencias y entornos virtuales reproducibles. Toda la configuración de dependencias y pruebas se encuentra centralizada en [`backend/pyproject.toml`](backend/pyproject.toml).

### 3.1 Instalación de Dependencias

```bash
cd backend
poetry install
```

### 3.2 Ejecución de Suites de Pruebas con `poetry run pytest`

- **Ejecutar toda la suite con reporte de cobertura (umbral $\ge 85\%$):**

  ```bash
  poetry run pytest
  ```

  _(La configuración de `pyproject.toml` incluye automáticamente los flags `--verbose --cov=app --cov-report=term-missing`)._

  Las pruebas que guardan cotizaciones usan PostgreSQL (`docker compose up -d postgres`) y crean su propia base, `solventa_test`.

- **Ejecutar únicamente pruebas unitarias:**

  ```bash
  poetry run pytest tests/unit -v
  ```

- **Ejecutar únicamente pruebas de integración:**

  ```bash
  poetry run pytest tests/integration -v
  ```

- **Inspeccionar detalle de pruebas TDD pendientes de Historias de Usuario:**
  Las pruebas de aceptación técnica de cada historia de usuario (`TC-S1-*`) están estructuradas y marcadas según el avance del sprint. Las de HU-WEB-02 (`TC-S1-03`), HU-WEB-01 (`TC-S1-04`), HU-MOV-02 (`TC-S1-10`) y HU-MOV-12 (`TC-S1-12`) ya están implementadas en `tests/unit/test_profile_and_consent.py`, `tests/unit/test_insured_auth.py`, `tests/unit/test_insured_logout.py` y `tests/integration/`. Para visualizar los motivos de omisión:
  ```bash
  poetry run pytest -rs
  ```

---

## 4. Portal Web para Asesores Comerciales (Angular 22)

El portal web para asesores comerciales (`/web`) está desarrollado en Angular 22 con Standalone Components, **Vitest** como runner de pruebas unitarias ultrarrápido y esbuild para empaquetado de producción.

### 4.1 Ejecución en Entorno Local

Para iniciar el servidor de desarrollo con proxy inverso hacia el backend en `localhost:8000`:

```bash
cd web

# 1. Instalar dependencias
npm install

# 2. Iniciar servidor de desarrollo con proxy
npm start
```

La aplicación estará disponible en [http://localhost:4200/](http://localhost:4200/).

### 4.2 Autenticación y Acceso del Asesor Comercial (HU-WEB-13)

El sistema cuenta con un usuario asesor semilla configurado para pruebas de desarrollo:

- **Usuario (Email):** `asesor@solventa.com`
- **Contraseña:** `SuperSecreta2026*`
- **Secreto TOTP (Base32):** `JBSWY3DPEHPK3PXP`

Para obtener el código TOTP dinámico de 6 dígitos válido en cualquier momento (ventana de $\pm 30$ segundos según RFC 6238):

```bash
backend/.venv/bin/python -c "from app.core.security import generate_totp; print('TOTP actual:', generate_totp('JBSWY3DPEHPK3PXP'))"
```

*(Opcionalmente, puede registrar la clave `JBSWY3DPEHPK3PXP` en aplicaciones como Google Authenticator o Authy).*

> [!NOTE]
> **Seguridad y Bloqueo Temporal:** Tras acumular 5 intentos fallidos consecutivos de autenticación, la cuenta se bloquea por 15 minutos (HTTP 423 Locked).

### 4.3 Pruebas Automatizadas y Compilación

```bash
cd web

# 1. Ejecutar pruebas unitarias (modo CI sin watch)
npm test -- --watch=false

# 2. Compilación de producción
npm run build
```

---

## 5. Ejecución de Pruebas de la Aplicación Móvil (Android)

La aplicación móvil utiliza Android Nativo con **Kotlin 2.1.0**, Android Gradle Plugin **8.7.3**, Jetpack Compose, **Java 17 LTS** y versión mínima de sistema operativo **Android 13 (API 33)** (`targetSdk = 35`).

### 5.1 Requisitos Previos de Entorno

Puede configurar el entorno mediante **`mise`** (CLI) o mediante **Android Studio**:

#### Opción A: Mediante `mise` (Recomendado para CLI y Terminal)

1. Instalar herramientas declaradas en `.mise.toml` (Java 17 LTS, Gradle 8.10.2, Android SDK CLI):
   ```bash
   mise install
   ```
2. Instalar la plataforma y herramientas de compilación de Android requeridas (`android-35` y `build-tools;35.0.0`) y aceptar licencias:
   ```bash
   yes | $(mise where android-sdk)/cmdline-tools/latest/bin/sdkmanager "platforms;android-35" "build-tools;35.0.0"
   ```
   _(Nota: Si no se utiliza la activación automática de shell de `mise`, asegúrese de contar con `movil/local.properties` indicando `sdk.dir=<ruta_al_sdk>`)_.

#### Opción B: Mediante Android Studio

- Abra la carpeta `/movil` en Android Studio. El IDE detectará el SDK instalado en el sistema (`$HOME/Library/Android/sdk`) y descargará automáticamente la plataforma Android 35.

#### Opción C: Instalación manual (sin `mise` ni Android Studio)

1. JDK 17 (por ejemplo Temurin 17) con `JAVA_HOME` apuntando a él.
2. Android SDK command-line tools en `<sdk>/cmdline-tools/latest`, más los paquetes `"platforms;android-35" "build-tools;35.0.0" "platform-tools"` instalados con `sdkmanager`.
3. `movil/local.properties` con `sdk.dir=<ruta_al_sdk>` (archivo ignorado por git).

### 5.2 Ejecutar Pruebas Unitarias

```bash
cd movil

# Ejecutar pruebas unitarias de depuración (en PowerShell: .\gradlew testDebugUnitTest)
./gradlew testDebugUnitTest
```

Las pruebas cubren `TC-S1-09` (biometría), `TC-S1-10` (acceso alternativo), `TC-S1-11` (sesión cifrada con Keystore) y `TC-S1-12` (cierre de sesión). En la JVM, el Keystore se sustituye por una llave AES-GCM por software (`FakeSessionCrypto`).

### 5.3 Compilación y Ejecución en Dispositivo o Emulador

```bash
cd movil

# 1. Compilar y empaquetar el APK de depuración (genera app/build/outputs/apk/debug/app-debug.apk)
./gradlew assembleDebug

# 2. Instalar en un emulador o dispositivo físico conectado con depuración USB
./gradlew installDebug

# 3. Iniciar la Activity principal mediante adb (o mise exec -- adb)
mise exec -- adb shell am start -n com.solventa.app/.MainActivity
```

Antes de instalar, espere a que el emulador termine de arrancar: `adb shell getprop sys.boot_completed` debe devolver `1`. Si se instala antes, falla con `NullPointerException ... freeStorage`.

### 5.4 Conexión con el Backend Local

La app consume el BFF en `BuildConfig.API_BASE_URL`, definido en `movil/app/build.gradle.kts`:

- **Emulador:** `http://10.0.2.2:8000/api/v1/` (valor por defecto; `10.0.2.2` es el `localhost` del equipo visto desde el emulador).
- **Dispositivo físico:** ejecute `adb reverse tcp:8000 tcp:8000` y cambie la URL a `http://localhost:8000/api/v1/`.

El tráfico HTTP sin TLS solo está permitido hacia `10.0.2.2` y `localhost` (`res/xml/network_security_config.xml`); cualquier otro destino exige HTTPS.

### 5.5 Emulador con Huella para Pruebas Biométricas

```bash
SDK=<ruta_al_sdk>
$SDK/cmdline-tools/latest/bin/sdkmanager "emulator" "system-images;android-35;google_apis;x86_64"
$SDK/cmdline-tools/latest/bin/avdmanager create avd -n solventa -k "system-images;android-35;google_apis;x86_64"
$SDK/emulator/emulator -avd solventa

# Registrar huella: abre el asistente del sistema (PIN 1234 y luego la huella)
adb shell am start -a android.settings.BIOMETRIC_ENROLL
adb -e emu finger touch 1     # repetir hasta "Fingerprint added"; también sirve para entrar a la app
```

Si después de la huella queda una pantalla en blanco (registro de rostro, que el emulador no soporta), ciérrela con `adb shell am force-stop com.android.settings`.

---

## 6. Guía de Pruebas Manuales

El recorrido paso a paso para probar a mano las historias del Sprint 1 está en [`docs/GUIA-PRUEBAS-SPRINT1.md`](docs/GUIA-PRUEBAS-SPRINT1.md). Indica qué hacer, qué debe pasar y qué tarea y caso cubre cada paso.

---

## 7. Infraestructura como Código (Terraform)

La topología en AWS está estructurada de forma modular en [`/terraform`](terraform/) implementando alta disponibilidad Multi-AZ (`us-east-1a`, `us-east-1b`):

- **`modules/vpc`**: VPC (`10.0.0.0/16`) con 2 subredes públicas, 2 subredes privadas, Internet Gateway y NAT Gateway.
- **`modules/alb`**: Application Load Balancer con sondeo activo en `/health` cada 5s y reintentos automáticos (`HA-09`).
- **`modules/ecs`**: Cluster ECS Fargate con autoscaling dinámico de 2 a 6 instancias según consumo de CPU (`HA-06`).
- **`modules/rds`**: Base de datos PostgreSQL 16 Multi-AZ con conmutación por error automática y cifrado KMS (`HA-15`).
- **`modules/storage_events`**: Bucket S3 con versionado y SSE-KMS (`HA-08`) y cola SQS con Dead Letter Queue (DLQ).
- **`modules/ecr`**: Repositorio de imágenes Docker del backend con escaneo de vulnerabilidades.
- **`modules/web_hosting`**: Bucket S3 y CDN CloudFront con Origin Access Control (OAC) para el portal web Angular y enrutamiento dinámico sin caché de `/api/*` y `/health` hacia el Application Load Balancer.

### 7.1 Comprobación y Validación Local

```bash
cd terraform
terraform init -backend=false
terraform fmt -check
terraform validate
```

### 7.2 Planificación y Ejecución Local contra Floci (Emulador AWS)

Para simular la creación de la infraestructura sin costos de nube utilizando el emulador local [Floci](https://floci.io/aws/) (`http://localhost:4566`):

```bash
# 1. Levantar el emulador local Floci
docker compose up -d floci

# 2. Planificar la infraestructura contra el emulador local
cd terraform
terraform plan -var-file=environments/local.tfvars

# 3. Desplegar infraestructura localmente (opcional)
terraform apply -var-file=environments/local.tfvars -auto-approve
```

---

## 8. Integración y Despliegue Continuo (CI/CD con GitHub Actions)

El repositorio cuenta con workflows automatizados en [`.github/workflows`](.github/workflows/):

### 8.1 Integración Continua (`.github/workflows/ci.yml`)

Se dispara en **cada commit y pull request sin importar la rama** (`push` y `pull_request` en `**`):

1. **`backend-ci`**: Instala Python 3.12 y Poetry, ejecuta la suite de pruebas unitarias y valida cobertura mínima ($\ge 85\%$).
2. **`web-ci`**: Instala Node.js 22, ejecuta las pruebas unitarias del portal comercial con Vitest y genera el bundle de producción.
3. **`mobile-ci`**: Configura Java 17 LTS y Gradle, ejecutando `./gradlew testDebugUnitTest` para la aplicación móvil.
4. **`terraform-ci`**: Inicializa los módulos de Terraform y valida el formato y sintaxis (`fmt -check`, `validate`).

### 8.2 Despliegue Continuo a AWS (`.github/workflows/deploy.yml`)

Se dispara automáticamente ante **push / merges a la rama `main`** o **manualmente vía `workflow_dispatch`** desde la pestaña *Actions* de GitHub:

1. **`deploy-infra`**: Ejecuta `terraform apply -auto-approve` para sincronizar o recrear desde cero la topología AWS Multi-AZ (VPC, ALB, ECS, RDS, S3/SQS, ECR y CloudFront).
2. **`deploy-backend`**: Construye la imagen Docker del backend, la publica en Amazon ECR y actualiza el servicio ECS Fargate con despliegue progresivo.
3. **`deploy-web`**: Compila los estáticos de Angular 22, los sincroniza con el bucket S3 del portal comercial e invalida la caché de CloudFront.

### 8.3 Apagado y Destrucción de Infraestructura AWS (`.github/workflows/destroy.yml`)

Diseñado especialmente para el contexto académico para evitar incurrir en costos continuos innecesarios (~\$90–\$110 USD/mes por recursos facturados por hora como NAT Gateway, ALB, RDS Multi-AZ y ECS Fargate):

* **Disparo manual protegido:** Se ejecuta exclusivamente bajo demanda mediante `workflow_dispatch` en GitHub Actions, exigiendo ingresar la palabra `DESTRUIR` como confirmación de seguridad.
* **Vaciado y desaprovisionamiento total:** Realiza la limpieza preventiva de buckets S3 (`force_destroy`) y ejecuta `terraform destroy -auto-approve`, reduciendo el costo horario a **\$0.00 USD**.
* **Recreación en cualquier momento:** Para volver a levantar la plataforma completa, basta con ejecutar el workflow `CD - Despliegue a AWS` o mezclar nuevos cambios a la rama `main`. El backend inicializará automáticamente el esquema de base de datos y el usuario asesor semilla en su arranque.

### 8.4 Despliegue Local Simulado con Floci (`.github/workflows/deploy-local.yml` y `scripts/deploy-local.sh`)

Permite validar de forma integral el flujo de despliegue simulando la arquitectura completa de AWS de producción localmente:
* **Vía Workflow de GitHub Actions (`act` o manual):** Archivo [`.github/workflows/deploy-local.yml`](.github/workflows/deploy-local.yml) ejecutable mediante `act` o evento `workflow_dispatch`.
* **Vía Script Local Directo:** Ejecutable en un solo paso desde la terminal:
  ```bash
  ./scripts/deploy-local.sh
  ```
  El script orquesta de forma automatizada:
  1. Inicio del emulador Floci (`docker compose up -d floci`).
  2. Aprovisionamiento de los 46 recursos Multi-AZ con Terraform en Floci (`environments/local.tfvars`).
  3. Construcción de la imagen Docker de producción del backend (`solventa-backend:local`).
  4. Compilación del bundle de producción del portal web Angular 22 y sincronización al bucket S3 en Floci (`s3://solventa-web-portal-local`).
  5. Verificación de salud e integridad de los recursos creados.

### 8.5 Configuración de Secretos en GitHub Actions

Para el funcionamiento del pipeline de despliegue a AWS en la nube (`deploy.yml`), deben configurarse los siguientes secretos en el repositorio (**Settings > Secrets and variables > Actions**):

| Secreto                 | Requerido | Descripción                                                        | Ejemplo                                    |
| :---------------------- | :-------: | :----------------------------------------------------------------- | :----------------------------------------- |
| `AWS_ACCESS_KEY_ID`     | **Sí**    | Identificador de clave de acceso del usuario IAM de despliegue     | `AKIAIOSFODNN7EXAMPLE`                     |
| `AWS_SECRET_ACCESS_KEY` | **Sí**    | Clave de acceso secreta del usuario IAM                            | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION`            | Opcional  | Región primaria de AWS para el despliegue (por defecto `us-east-1`)| `us-east-1`                                |

> [!NOTE]
> Para que Terraform y los workflows de GitHub Actions puedan aprovisionar y actualizar la infraestructura sin errores de autorización, debes asociar al usuario de IAM las siguientes **Políticas administradas por AWS (AWS Managed Policies)**:
> 
> 1. `AmazonEC2FullAccess` (o `AmazonVPCFullAccess`): Gestión de VPC, subredes, tablas de ruteo, Internet Gateways, NAT Gateways y Security Groups.
> 2. `ElasticLoadBalancingFullAccess`: Creación y configuración del ALB, Target Groups y Listeners.
> 3. `AmazonECS_FullAccess`: Gestión del clúster ECS Fargate, tareas, servicios y autoescalado.
> 4. `AmazonEC2ContainerRegistryFullAccess`: Repositorio ECR, políticas de ciclo de vida e inicio de sesión para push/pull de imágenes Docker.
> 5. `AmazonRDSFullAccess`: Instancia PostgreSQL 16 Multi-AZ y grupos de subredes de base de datos.
> 6. `AmazonS3FullAccess`: Buckets de almacenamiento de documentos y portal web, versionado, cifrado y sincronización de estáticos.
> 7. `AmazonSQSFullAccess`: Colas SQS de eventos y Dead Letter Queues (DLQ).
> 8. `CloudFrontFullAccess`: Distribución CDN de CloudFront, Origin Access Control (OAC) e invalidación de caché.
> 9. `CloudWatchLogsFullAccess`: Grupos de logs para los contenedores del backend en Fargate.
> 10. `IAMFullAccess`: Creación de roles de ejecución y de tarea requeridos por ECS (`execution_role` y `task_role`).
> 11. **Política en Línea de Soporte para Servicios Específicos (`SolventaKMSFullPolicy`)**: AWS no provee políticas administradas de acceso total para KMS ni para Application Auto Scaling. El usuario debe poseer una política en línea con permisos:
>     - `kms:*` (permite a RDS crear "grants" de cifrado con `kms:CreateGrant` y habilitar rotación de llaves).
>     - `application-autoscaling:*` y `autoscaling:*` (registro de target de autoescalado y etiquetado de recursos con `application-autoscaling:TagResource`).
>     - `cloudwatch:*` (creación de alarmas métricas vinculadas a las políticas de autoescalado del backend).

#### Automatización con el Script `setup-aws-secrets.sh`

El repositorio incluye un script interactivo en [`scripts/setup-aws-secrets.sh`](scripts/setup-aws-secrets.sh) que valida las credenciales de IAM contra AWS STS y las sincroniza en GitHub vía GitHub CLI (`gh`):

```bash
# Ejecución interactiva (solicita Access Key y Secret Key o lee ~/.aws/credentials):
./scripts/setup-aws-secrets.sh

# O cargando directamente un perfil configurado en AWS CLI:
./scripts/setup-aws-secrets.sh --profile default
```
