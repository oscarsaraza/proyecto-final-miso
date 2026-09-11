# Criterios de interpretación de resultados

## Reglas comunes a todos los experimentos

1. Cada experimento se ejecuta **3 veces** con configuración idéntica.
2. El valor reportado es la **mediana** de las 3 ejecuciones. También se conservan los 3 resultados individuales.
3. Todas las ejecuciones se hacen en la **misma máquina**, con los mismos límites de CPU y memoria declarados en `docker-compose.yml`.
4. Una ejecución solo se descarta si falla el propio script de prueba, nunca por el valor que arroje. Toda exclusión queda registrada.
5. Los umbrales provienen del diseño de la Semana 5 y de los ASR.

## E1. Latencia de cotización con proveedor degradado

Valida **ASR-01** y **ASR-02** (historias HA-01 y HA-05).

| Resultado | Condición |
| --- | --- |
| **Hipótesis respaldada** | `p95 < 250 ms` en la fase degradada **y** 100 % de las respuestas degradadas marcadas explícitamente |
| **Hipótesis refutada** | `p95 >= 250 ms` en 2 de las 3 ejecuciones |
| **No concluyente** | La dispersión del `p95` entre ejecuciones supera el 20 % de su mediana |

La métrica principal es el `p95` de la latencia extremo a extremo de `POST /api/v1/quotes`.

La métrica de control es la proporción de respuestas marcadas con el estado `degraded` durante la fase degradada.

## E3. Continuidad ante la caída súbita de una réplica

Valida **ASR-04** (historia HA-09).

| Resultado | Condición |
| --- | --- |
| **Hipótesis respaldada** | Solicitudes exitosas `>= 99 %` durante la ventana completa **y** cero tráfico enrutado a la réplica caída tras su retiro |
| **Hipótesis refutada** | Solicitudes exitosas `< 99 %` en 2 de las 3 ejecuciones |
| **No concluyente** | El balanceador no alcanza a detectar la caída dentro de la ventana medida |

La métrica principal es el porcentaje de solicitudes HTTP exitosas durante los 3 minutos de carga.

La métrica de control son las peticiones servidas por cada réplica antes, durante y después del fallo.
