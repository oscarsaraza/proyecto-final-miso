# Solventa Backend

Monolito Modular API-First con Arquitectura Hexagonal y FastAPI.

## 1. Ejecución Local

### Prerrequisitos:
Iniciar los servicios de infraestructura base desde la raíz del proyecto:
```bash
docker compose up -d postgres floci
```

### Ejecución con Poetry:
```bash
# 1. Instalar dependencias
poetry install

# 2. Iniciar servidor FastAPI con recarga en caliente
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Ejecución sin Poetry (entorno virtual):
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows (en Linux/macOS: .venv/bin/python)
.venv/Scripts/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Documentación y Endpoints:
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **Documentación Swagger / OpenAPI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentación ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Autenticación del asegurado (`app/bff/auth`, `app/modules/identity`):
- `POST /api/v1/auth/otp`: código de un solo uso de 6 dígitos, vigente 5 minutos.
- `POST /api/v1/auth/login`: correo, contraseña y código; bloqueo de 15 minutos al tercer intento fallido (`423`).
- `POST /api/v1/auth/refresh`: renueva y rota el refresh token.
- `POST /api/v1/auth/logout`: revoca el refresh token (`204`).

En desarrollo, `/auth/otp` devuelve el código en `debug_code` y existe el asegurado de prueba `maria.ruiz@correo.co` / `Solventa2026!`. Los códigos, intentos y tokens revocados viven en memoria, así que se limpian al reiniciar el servidor.

### Consentimiento Open Finance, Asegurabilidad y Catálogos (`app/bff/experience`, `app/modules/profile`):
- `POST /api/v1/experience/clients/validate`: valida la asegurabilidad sociodemográfica del tomador (rango 18 a 75 años, TC-S1-03). Exige rol `advisor`.
- `POST /api/v1/experience/consent`: registra consentimiento auditable con hash SHA-256 inalterable (RC-01 / RC-04), vigencia configurable y validación OTP. Exige rol `advisor`.
- `GET /api/v1/experience/consent/{document_number}`: consulta el consentimiento activo registrado para el tomador. Exige rol `advisor`.
- `GET /api/v1/experience/catalogs/financial-entities`: consulta el catálogo de entidades financieras bancarias vigiladas por la SFC activas en base de datos.
- `GET /api/v1/experience/catalogs/cities`: consulta el catálogo de las principales ciudades de Colombia activas en base de datos.

## 2. Pruebas Automatizadas

Las pruebas que guardan cotizaciones usan PostgreSQL (`docker compose up -d postgres`) y crean su propia base, `solventa_test`.

```bash
poetry run pytest
# o, sin Poetry:
.venv/Scripts/python -m pytest
```

