"""Agrega los resultados en bruto de k6 y nginx."""
import collections
import json
import re
from datetime import datetime
from pathlib import Path
from statistics import median

RAIZ = Path(__file__).parent
CAIDA_S, REGRESO_S = 45, 165


def percentiles(ruta: Path) -> dict:
    metricas = json.loads(ruta.read_text())["metrics"]
    duracion = metricas["http_req_duration"]["values"]
    return {
        "p95": duracion["p(95)"],
        "p99": duracion["p(99)"],
        "exito": (1 - metricas["http_req_failed"]["values"]["rate"]) * 100,
        "degradadas": metricas.get("respuestas_degradadas", {}).get("values", {}).get("rate"),
    }


def dispersion(valores: list[float]) -> dict:
    centro = median(valores)
    return {"mediana": centro, "rango_sobre_mediana": (max(valores) - min(valores)) / centro * 100}


def trafico_a_la_caida(ruta: Path) -> int:
    """Peticiones que nginx envió a la réplica detenida durante la ventana de caída."""
    filas = []
    for linea in ruta.read_text().splitlines():
        campos = re.match(r"(\S+) upstream=(\S+?)(?:, \S+)? status=", linea)
        if campos:
            filas.append((datetime.fromisoformat(campos.group(1)), campos.group(2)))
    inicio = filas[0][0]
    detenida = min(collections.Counter(u for _, u in filas).items(), key=lambda x: x[1])[0]
    ventana = [u for t, u in filas if CAIDA_S <= (t - inicio).total_seconds() < REGRESO_S]
    return ventana.count(detenida)


def resumir_e1() -> dict:
    base = RAIZ / "e1-latencia/resultados"
    salida = {}
    for fase in ("base", "degradada"):
        corridas = [percentiles(base / f"{fase}-{i}.json") for i in (1, 2, 3)]
        salida[fase] = {
            "p95": [c["p95"] for c in corridas],
            "p99": [c["p99"] for c in corridas],
            "dispersion_p95": dispersion([c["p95"] for c in corridas]),
            "degradadas": [c["degradadas"] for c in corridas],
        }
    return salida


def resumir_e3() -> dict:
    base = RAIZ / "e3-continuidad/resultados"
    salida = {}
    for version in ("v1", "v2"):
        exitos = [percentiles(base / f"{version}-corrida-{i}.json")["exito"] for i in (1, 2, 3)]
        salida[version] = {
            "exito": exitos,
            "mediana_exito": median(exitos),
            "trafico_a_la_replica_caida": [
                trafico_a_la_caida(base / f"{version}-nginx-{i}.log") for i in (1, 2, 3)
            ],
        }
    return salida


if __name__ == "__main__":
    for ruta, datos in (
        (RAIZ / "e1-latencia/resultados/resumen-e1.json", resumir_e1()),
        (RAIZ / "e3-continuidad/resultados/resumen-e3.json", resumir_e3()),
    ):
        ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n")
        print(f"escrito {ruta.relative_to(RAIZ)}")
