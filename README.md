# Solventa · Proyecto Final MISW4501 · Equipo 7

Repositorio de trabajo del proyecto **Solventa**, aseguradora digital nativa en la nube sobre el ecosistema de Finanzas Abiertas y Datos Abiertos.

## Contenido

| Carpeta | Qué contiene |
| --- | --- |
| `experiments/` | Código, configuración, scripts de carga y resultados de los experimentos de arquitectura E1 y E3 |
| `docs/` | Prototipo de navegación web y móvil (publicado con GitHub Pages) |

## Experimentos

Los criterios de interpretación están en [`experiments/CRITERIOS.md`](experiments/CRITERIOS.md).

| Experimento | Qué valida | Cómo se ejecuta |
| --- | --- | --- |
| **E1** · Latencia con proveedor degradado | ASR-01 y ASR-02 (HA-01, HA-05) | `experiments/e1-latencia/run.sh` |
| **E3** · Continuidad ante caída de réplica | ASR-04 (HA-09) | `experiments/e3-continuidad/run.sh <corrida>` |

Requiere Docker y Docker Compose. El generador de carga (k6) se ejecuta como contenedor, no requiere instalación local.

## Prototipo

`docs/index.html` es un prototipo **sin funcionalidad**, con navegación real y datos de ejemplo. Admite parámetros de consulta para enlazar una pantalla concreta, por ejemplo `?canal=movil&pantalla=4&idioma=en&region=MX`.
