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

## 2. Pruebas Automatizadas

```bash
poetry run pytest
# o, sin Poetry:
.venv/Scripts/python -m pytest
```

