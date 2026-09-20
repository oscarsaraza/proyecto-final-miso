"""Agrega y compara los resultados en bruto de k6 y nginx para E1 y E3."""
from __future__ import annotations

import collections

import json
import re
import sys
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
        "degradadas": metricas.get("respuestas_degradadas", {}).get("values", {}).get("rate", 0.0),
    }


def dispersion(valores: list[float]) -> dict:
    centro = median(valores)
    rango = (max(valores) - min(valores)) / centro * 100 if centro > 0 else 0.0
    return {"mediana": centro, "rango_sobre_mediana": rango}


def trafico_a_la_caida(ruta: Path) -> int:
    """Peticiones que nginx envió a la réplica detenida durante la ventana de caída."""
    filas = []
    for linea in ruta.read_text().splitlines():
        campos = re.match(r"(\S+) upstream=(\S+?)(?:, \S+)? status=", linea)
        if campos:
            filas.append((datetime.fromisoformat(campos.group(1)), campos.group(2)))
    if not filas:
        return 0
    inicio = filas[0][0]
    detenida = min(collections.Counter(u for _, u in filas).items(), key=lambda x: x[1])[0]
    ventana = [u for t, u in filas if CAIDA_S <= (t - inicio).total_seconds() < REGRESO_S]
    return ventana.count(detenida)


def resumir_e1(subcarpeta: str = "resultados") -> dict | None:
    base = RAIZ / "e1-latencia" / subcarpeta
    for fase in ("base", "degradada"):
        for i in (1, 2, 3):
            if not (base / f"{fase}-{i}.json").exists():
                return None

    salida = {}
    for fase in ("base", "degradada"):
        corridas = [percentiles(base / f"{fase}-{i}.json") for i in (1, 2, 3)]
        salida[fase] = {
            "p95": [round(c["p95"], 2) for c in corridas],
            "p99": [round(c["p99"], 2) for c in corridas],
            "dispersion_p95": dispersion([c["p95"] for c in corridas]),
            "degradadas": [c["degradadas"] for c in corridas],
        }

    # Evaluación según CRITERIOS.md
    deg = salida["degradada"]
    p95_vals = deg["p95"]
    disp = deg["dispersion_p95"]["rango_sobre_mediana"]
    degradadas = deg["degradadas"]

    if disp > 20.0:
        dictamen = "No concluyente (dispersión > 20%)"
    elif sum(1 for v in p95_vals if v >= 250.0) >= 2:
        dictamen = "Hipótesis refutada (p95 >= 250 ms en 2 de 3 ejecuciones)"
    elif median(p95_vals) < 250.0 and all(d == 1.0 for d in degradadas):
        dictamen = "Hipótesis respaldada (p95 < 250 ms y 100% degradadas marcadas)"
    else:
        dictamen = "No concluyente"

    salida["evaluacion"] = {
        "dictamen": dictamen,
        "mediana_p95_degradada_ms": round(median(p95_vals), 2),
        "dispersion_pct": round(disp, 2),
        "respuestas_degradadas_pct": round(median(degradadas) * 100, 1) if degradadas else 0.0,
    }
    return salida


def resumir_e3(subcarpeta: str = "resultados") -> dict | None:
    base = RAIZ / "e3-continuidad" / subcarpeta
    for version in ("v1", "v2"):
        for i in (1, 2, 3):
            if not (base / f"{version}-corrida-{i}.json").exists() or not (base / f"{version}-nginx-{i}.log").exists():
                return None

    salida = {}
    for version in ("v1", "v2"):
        exitos = [percentiles(base / f"{version}-corrida-{i}.json")["exito"] for i in (1, 2, 3)]
        trafico = [trafico_a_la_caida(base / f"{version}-nginx-{i}.log") for i in (1, 2, 3)]
        salida[version] = {
            "exito": [round(e, 2) for e in exitos],
            "mediana_exito": round(median(exitos), 2),
            "trafico_a_la_replica_caida": trafico,
        }

    # Evaluación según CRITERIOS.md para v2 (solución propuesta)
    v2_exitos = salida["v2"]["exito"]
    v2_trafico = salida["v2"]["trafico_a_la_replica_caida"]
    med_exito = salida["v2"]["mediana_exito"]

    if sum(1 for e in v2_exitos if e < 99.0) >= 2:
        dictamen = "Hipótesis refutada (éxito < 99% en 2 de 3 ejecuciones)"
    elif med_exito >= 99.0 and all(t == 0 for t in v2_trafico):
        dictamen = "Hipótesis respaldada (éxito >= 99% y 0 tráfico a réplica caída)"
    else:
        dictamen = "No concluyente"

    salida["evaluacion"] = {
        "dictamen_v2": dictamen,
        "mediana_exito_v2_pct": med_exito,
        "trafico_a_caida_v2": v2_trafico,
        "mediana_exito_v1_pct": salida["v1"]["mediana_exito"],
        "trafico_a_caida_v1": salida["v1"]["trafico_a_la_replica_caida"],
    }
    return salida


def procesar_carpeta(subcarpeta: str) -> tuple[dict | None, dict | None]:
    e1 = resumir_e1(subcarpeta)
    e3 = resumir_e3(subcarpeta)

    if e1:
        ruta_e1 = RAIZ / "e1-latencia" / subcarpeta / "resumen-e1.json"
        ruta_e1.parent.mkdir(parents=True, exist_ok=True)
        ruta_e1.write_text(json.dumps(e1, indent=2, ensure_ascii=False) + "\n")
        print(f"✓ Escrito {ruta_e1.relative_to(RAIZ)}")

    if e3:
        ruta_e3 = RAIZ / "e3-continuidad" / subcarpeta / "resumen-e3.json"
        ruta_e3.parent.mkdir(parents=True, exist_ok=True)
        ruta_e3.write_text(json.dumps(e3, indent=2, ensure_ascii=False) + "\n")
        print(f"✓ Escrito {ruta_e3.relative_to(RAIZ)}")

    return e1, e3


def imprimir_tabla_comparativa(local_e1: dict | None, nube_e1: dict | None, local_e3: dict | None, nube_e3: dict | None):
    print("\n" + "=" * 80)
    print("RESUMEN COMPARATIVO DE EXPERIMENTOS DE ARQUITECTURA: LOCAL vs NUBE (AWS)")
    print("=" * 80)

    print("\n--- E1. LATENCIA DE COTIZACIÓN CON PROVEEDOR DEGRADADO (ASR-01, ASR-02) ---")
    print(f"{'Métrica':<35} | {'Local':<18} | {'Nube (AWS)':<18} | {'Criterio Aceptación'}")
    print("-" * 80)
    if local_e1:
        p95_base_loc = f"{median(local_e1['base']['p95']):.2f} ms"
        p95_deg_loc = f"{local_e1['evaluacion']['mediana_p95_degradada_ms']:.2f} ms"
        disp_loc = f"{local_e1['evaluacion']['dispersion_pct']:.1f} %"
        deg_pct_loc = f"{local_e1['evaluacion']['respuestas_degradadas_pct']:.0f} %"
        dict_loc = local_e1['evaluacion']['dictamen']
    else:
        p95_base_loc = p95_deg_loc = disp_loc = deg_pct_loc = dict_loc = "N/A"

    if nube_e1:
        p95_base_nub = f"{median(nube_e1['base']['p95']):.2f} ms"
        p95_deg_nub = f"{nube_e1['evaluacion']['mediana_p95_degradada_ms']:.2f} ms"
        disp_nub = f"{nube_e1['evaluacion']['dispersion_pct']:.1f} %"
        deg_pct_nub = f"{nube_e1['evaluacion']['respuestas_degradadas_pct']:.0f} %"
        dict_nub = nube_e1['evaluacion']['dictamen']
    else:
        p95_base_nub = p95_deg_nub = disp_nub = deg_pct_nub = dict_nub = "Pendiente"

    print(f"{'Mediana p95 Fase Base':<35} | {p95_base_loc:<18} | {p95_base_nub:<18} | Informativo")
    print(f"{'Mediana p95 Fase Degradada':<35} | {p95_deg_loc:<18} | {p95_deg_nub:<18} | < 250 ms")
    print(f"{'Dispersión p95':<35} | {disp_loc:<18} | {disp_nub:<18} | <= 20 %")
    print(f"{'Marcación respuestas degradadas':<35} | {deg_pct_loc:<18} | {deg_pct_nub:<18} | 100 %")
    print(f"{'Dictamen Hipótesis E1':<35} | {dict_loc:<18} | {dict_nub:<18} | Hipótesis respaldada")

    print("\n--- E3. CONTINUIDAD ANTE CAÍDA SÚBITA DE RÉPLICA (ASR-04) ---")
    print(f"{'Métrica':<35} | {'Local':<18} | {'Nube (AWS)':<18} | {'Criterio Aceptación'}")
    print("-" * 80)
    if local_e3:
        exito_v1_loc = f"{local_e3['evaluacion']['mediana_exito_v1_pct']:.2f} %"
        exito_v2_loc = f"{local_e3['evaluacion']['mediana_exito_v2_pct']:.2f} %"
        caida_v2_loc = f"{sum(local_e3['evaluacion']['trafico_a_caida_v2'])} req"
        dict_e3_loc = local_e3['evaluacion']['dictamen_v2']
    else:
        exito_v1_loc = exito_v2_loc = caida_v2_loc = dict_e3_loc = "N/A"

    if nube_e3:
        exito_v1_nub = f"{nube_e3['evaluacion']['mediana_exito_v1_pct']:.2f} %"
        exito_v2_nub = f"{nube_e3['evaluacion']['mediana_exito_v2_pct']:.2f} %"
        caida_v2_nub = f"{sum(nube_e3['evaluacion']['trafico_a_caida_v2'])} req"
        dict_e3_nub = nube_e3['evaluacion']['dictamen_v2']
    else:
        exito_v1_nub = exito_v2_nub = caida_v2_nub = dict_e3_nub = "Pendiente"

    print(f"{'Éxito v1 (Nginx pasivo sin retry)':<35} | {exito_v1_loc:<18} | {exito_v1_nub:<18} | Línea base")
    print(f"{'Éxito v2 (Nginx proxy_next_upstream)':<35} | {exito_v2_loc:<18} | {exito_v2_nub:<18} | >= 99.00 %")
    print(f"{'Tráfico a réplica caída (v2)':<35} | {caida_v2_loc:<18} | {caida_v2_nub:<18} | 0 req")
    print(f"{'Dictamen Hipótesis E3':<35} | {dict_e3_loc:<18} | {dict_e3_nub:<18} | Hipótesis respaldada")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    sub = sys.argv[1] if len(sys.argv) > 1 else None
    if sub:
        procesar_carpeta(sub)
    else:
        local_e1, local_e3 = procesar_carpeta("resultados")
        nube_e1, nube_e3 = procesar_carpeta("resultados/nube")
        imprimir_tabla_comparativa(local_e1, nube_e1, local_e3, nube_e3)
