# Solventa · Seguros Digitales

Solventa es una aseguradora nativa digital diseñada para operar en la nube de AWS bajo los estándares colombianos de Finanzas y Datos Abiertos (Decreto 1297 de 2022 y Circular Externa 004 de 2024 de la Superfinanciera).

Su arquitectura implementa un **Monolito Modular API-First con Arquitectura Hexagonal (Puertos y Adaptadores)**, patrón **BFF (Backend for Frontend)** y persistencia transaccional sobre PostgreSQL 16 con CQRS ligero.

---

## 1. Estructura del Repositorio

| Directorio                                | Componente                                                        | Stack Tecnológico                                             |
| :---------------------------------------- | :---------------------------------------------------------------- | :------------------------------------------------------------ |
| [`/backend`](backend/)                    | Monolito Modular Backend (Core, Rating, Policy, Payments, Claims) | Python 3.12, FastAPI, Poetry, SQLAlchemy, asyncpg             |
| [`/web`](web/)                            | Portal Web para Asesores Comerciales                              | Angular 22, TypeScript, Standalone Components, Vitest         |
| [`/movil`](movil/)                        | Aplicación Móvil para Asegurados                                  | Android, Kotlin 2.0, Jetpack Compose, Room (SQLCipher), JUnit |
| [`/terraform`](terraform/)                | Infraestructura como Código (AWS Multi-AZ)                        | Terraform >= 1.5, AWS Provider (ALB, ECS, RDS, S3, SQS)       |
| [`.github/workflows`](.github/workflows/) | Pipelines de CI/CD                                                | GitHub Actions (CI en cada commit, CD a AWS en `main`)        |
| [`experiments/`](experiments/)            | Experimentos de arquitectura y validaciones de carga E1 y E3      | Python, k6, AWS Cloud                                         |
| [`docs/`](docs/)                          | Prototipos de navegación interactivos                             | HTML5, CSS3, JavaScript                                       |

---

## 2. Entorno de Desarrollo Local

El proyecto cuenta con un archivo [`docker-compose.yml`](docker-compose.yml) para ejecutar el backend y sus dependencias en local sin incurrir en costos de AWS:

- **PostgreSQL 16:** Base de datos relacional en `localhost:5432`.
- **LocalStack:** Emulación local de AWS S3 (almacenamiento de carátulas) y AWS SQS (cola de eventos) en `localhost:4566`.
- **Backend FastAPI:** Ingress y API en `localhost:8000`.

### Iniciar servicios locales:

```bash
docker compose up -d postgres localstack
```

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

- **Ejecutar únicamente pruebas unitarias:**

  ```bash
  poetry run pytest tests/unit -v
  ```

- **Ejecutar únicamente pruebas de integración:**

  ```bash
  poetry run pytest tests/integration -v
  ```

- **Inspeccionar detalle de pruebas TDD pendientes de Historias de Usuario:**
  Las pruebas de aceptación técnica de cada historia de usuario (`TC-S1-*`) están estructuradas pero marcadas como `skipped` hasta que la funcionalidad sea codificada en su respectivo sprint. Para visualizar los motivos de omisión:
  ```bash
  poetry run pytest -rs
  ```

---

## 4. Ejecución de Pruebas del Portal Web (Angular 22)

El frontend web utiliza Angular 22 con **Vitest** como runner de pruebas unitarias ultrarrápido y esbuild para empaquetado de producción.

```bash
cd web

# 1. Instalar dependencias
npm install

# 2. Ejecutar pruebas unitarias (modo CI sin watch)
npm test -- --watch=false

# 3. Compilación de producción
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

### 5.2 Ejecutar Pruebas Unitarias

```bash
cd movil

# Ejecutar pruebas unitarias de depuración
./gradlew testDebugUnitTest
```

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

---
