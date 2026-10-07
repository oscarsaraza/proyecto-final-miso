# Solventa · Seguros Digitales

Solventa es una aseguradora nativa digital diseñada para operar en la nube de AWS bajo los estándares colombianos de Finanzas y Datos Abiertos (Decreto 1297 de 2022 y Circular Externa 004 de 2024 de la Superfinanciera).

Su arquitectura implementa un **Monolito Modular API-First con Arquitectura Hexagonal (Puertos y Adaptadores)**, patrón **BFF (Backend for Frontend)** y persistencia transaccional sobre PostgreSQL 16 con CQRS ligero.

---

## 1. Estructura del Repositorio

| Directorio | Componente | Stack Tecnológico |
| :--- | :--- | :--- |
| [`/backend`](backend/) | Monolito Modular Backend (Core, Rating, Policy, Payments, Claims) | Python 3.12, FastAPI, SQLAlchemy, asyncpg |
| [`/web`](web/) | Portal Web para Asesores Comerciales | Angular 18, TypeScript, Jasmine/Karma, Playwright |
| [`/movil`](movil/) | Aplicación Móvil para Asegurados | Android, Kotlin, Jetpack Compose, Room (SQLCipher) |
| [`/terraform`](terraform/) | Infraestructura como Código (AWS Multi-AZ) | Terraform >= 1.5, AWS Provider (ALB, ECS, RDS, S3, SQS) |
| [`.github/workflows`](.github/workflows/) | Pipelines de CI/CD | GitHub Actions (CI en cada commit, CD a AWS en `main`) |
| [`experiments/`](experiments/) | Experimentos de arquitectura y validaciones de carga E1 y E3 | Python, k6, AWS Cloud |
| [`docs/`](docs/) | Prototipos de navegación interactivos | HTML5, CSS3, JavaScript |

---

## 2. Entorno de Desarrollo Local

El proyecto cuenta con un archivo [`docker-compose.yml`](docker-compose.yml) para ejecutar el backend y sus dependencias en local sin incurrir en costos de AWS:

* **PostgreSQL 16:** Base de datos relacional en `localhost:5432`.
* **LocalStack:** Emulación local de AWS S3 (almacenamiento de carátulas) y AWS SQS (cola de eventos) en `localhost:4566`.
* **Backend FastAPI:** Ingress y API en `localhost:8000`.

### Iniciar servicios locales:
```bash
docker compose up -d postgres localstack
```

---

## 3. Ejecución de Pruebas Automatizadas

### Backend (Python/FastAPI)
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/unit tests/integration -v --cov=app --cov-report=term-missing
```

### Frontend Web (Angular)
```bash
cd web
npm install
npm test -- --watch=false --browsers=ChromeHeadless
npm run build
```

### Proyecto Móvil (Android)
```bash
cd movil
./gradlew testDebugUnitTest
```

### Infraestructura (Terraform)
```bash
cd terraform
terraform init -backend=false
terraform fmt -check
terraform validate
```

---

## 4. Configuración de Secretos en GitHub Actions para Despliegue en AWS

Para que el pipeline de despliegue continuo (`.github/workflows/deploy.yml`) aprovisione y actualice los servicios en AWS al integrar un Pull Request en la rama `main`, deben configurarse los siguientes secretos en el repositorio (**Settings > Secrets and variables > Actions**):

| Secreto | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `AWS_ACCESS_KEY_ID` | Identificador de clave de acceso del usuario IAM de despliegue | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Clave de acceso secreta del usuario IAM | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | Región primaria de AWS para el despliegue | `us-east-1` |

El usuario o rol de IAM debe poseer permisos para gestionar recursos de VPC, ECS Fargate, ALB, RDS, ECR, S3 y SQS.
