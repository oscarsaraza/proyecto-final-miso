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

### Documentación y Endpoints:
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **Documentación Swagger / OpenAPI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentación ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 2. Pruebas Automatizadas

```bash
poetry run pytest
```

