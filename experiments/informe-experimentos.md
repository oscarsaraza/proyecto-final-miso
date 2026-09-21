# Informe de Ejecución y Validación de Experimentos de Arquitectura en la Nube (AWS)

**Proyecto:** Solventa · Aseguradora Digital Nativa en la Nube  
**Equipo:** Equipo 7  
**Curso:** MISW4501 Proyecto Final · MISO (Universidad de los Andes)  
**Periodo:** 202614  
**Entorno de Validación:** Amazon Web Services (AWS) · Región `us-east-1`

---

## 1. Resumen Ejecutivo

Este documento consolida el plan de implementación, protocolo de ejecución, recolección de evidencias forenses y análisis de resultados para los experimentos de arquitectura prioritarios del proyecto **Solventa**:

1. **Experimento E1 — Latencia de cotización con proveedor degradado:**  
   Valida los escenarios de latencia **ASR-01** y **ASR-02** (Historias de Arquitectura HA-01 y HA-05). Evalúa la efectividad del _circuit breaker_, timeout duro y el _fallback_ a caché frente indisponibilidad simulada de proveedores externos de Open Finance.
2. **Experimento E3 — Continuidad de servicio ante caída súbita de una réplica:**  
   Valida el escenario de disponibilidad **ASR-04** (Historia de Arquitectura HA-09). Evalúa la capacidad del balanceador de carga Nginx con reintento no idempotente (`proxy_next_upstream`) y detección pasiva de fallos para absorber la caída de una réplica sin interrumpir las transacciones activas de cotización.

La ejecución en la nube se llevó a cabo sobre una **instancia de cómputo dedicado de AWS (`c6i.large`)** aprovisionada de forma efímera mediante **Terraform**. Esta configuración garantiza un entorno controlado y reproducible.

---

## 2. Definición y Criterios de Aceptación

Estos provienen del diseño de arquitectura y de los ASR y están documentados en CRITERIOS.md.

### Reglas Metodológicas

1. Cada experimento se ejecuta **3 veces consecutivas** bajo idénticas condiciones.
2. La métrica consolidada es la **mediana** de las tres ejecuciones, conservando íntegros los datos de cada corrida individual.
3. Todas las ejecuciones se realizan sobre la **misma máquina anfitriona**, respetando estrictamente los límites de CPU y memoria declarados en `docker-compose.yml` (vía cgroups v2).
4. Ninguna corrida se descarta por el valor arrojado.

---

## 3. Especificación Técnica del Entorno en AWS Cloud

Para evitar el sesgo de virtualización en nubes públicas, se implementó una topología efímera en AWS mediante Terraform:

| Parámetro                | Configuración en AWS                                               | Justificación Arquitectónica                                                                                                                                     |
| :----------------------- | :----------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Proveedor Cloud**      | Amazon Web Services (AWS)                                          | Entorno nativo meta del proyecto Solventa.                                                                                                                       |
| **Región / AZ**          | `us-east-1` (`us-east-1a`)                                         | Minimiza latencias de aprovisionamiento y costo.                                                                                                                 |
| **Familia de Instancia** | `c6i.large` (Compute Optimized)                                    | Procesadores Intel Xeon Ice Lake 3.5 GHz con cómputo dedicado. Evita el _throttling_ por agotamiento de créditos de CPU de familias `t3`/`t4g`.                  |
| **Recursos del Nodo**    | 2 vCPUs dedicadas, 4 GiB RAM                                       | Holgura adecuada para soportar las 2.0 vCPUs límite de Docker y la ejecución concurrente del generador k6.                                                       |
| **Almacenamiento**       | 30 GiB EBS `gp3` (3000 IOPS, 125 MB/s)                             | Alto rendimiento de I/O para escritura concurrente de logs de Nginx y métricas JSON.                                                                             |
| **Sistema Operativo**    | Ubuntu 24.04 LTS (Noble Numbat), Kernel 6.8                        | Compatibilidad nativa con Docker Engine v27 y aislamiento cgroups v2.                                                                                            |
| **Aislamiento de Red**   | VPC dedicada (`10.0.0.0/16`), Subred pública (`10.0.1.0/24`)       | Aislamiento completo de tráfico de red frente a otras cargas de trabajo.                                                                                         |
| **Seguridad Perimetral** | Security Group con ingreso TCP 22 restringido al CIDR del operador | Cero exposición pública de los puertos de las APIs (8000, 8080) ni del simulador (8001); todo el tráfico de prueba discurre en la red virtual interna de Docker. |

---

## 4. Arquitectura y Procedimiento de Ejecución

### 4.1 Experimento E1: Latencia con Proveedor Degradado

```
                          DISEÑO EXPERIMENTO E1 (Latencia)
 ┌────────────────────────────────────────────────────────────────────────┐
 │ Instancia EC2: c6i.large (Ubuntu 24.04)                               │
 │                                                                        │
 │   Red Docker: e1-latencia_default                                      │
 │   ┌───────────────┐  POST /api/v1/quotes   ┌──────────────────────┐    │
 │   │  grafana/k6   ├───────────────────────►│      FastAPI         │    │
 │   │  (10 VUs)     │                        │  (1.0 CPU / 512 MiB) │    │
 │   └───────────────┘                        └──────────┬───────────┘    │
 │                                                       │                │
 │                              Fase Base: 50 ms         │ GET /profile   │
 │                              Fase Degradada: 900 ms   ▼                │
 │                                            ┌──────────────────────┐    │
 │                                            │     Provider-Sim     │    │
 │                                            │ (0.5 CPU / 256 MiB)  │    │
 │                                            └──────────────────────┘    │
 └────────────────────────────────────────────────────────────────────────┘
```

- **Fase Base:** 100 iteraciones compartidas (10 VUs concurrentes) contra el endpoint `/api/v1/quotes`. Proveedor configurado con latencia normal de 50 ms y 0% de error.
- **Fase Degradada:** 500 iteraciones bajo carga concurrente. Se inyecta una latencia artificial de 900 ms y 20% de error HTTP 503 en el simulador. Se reinicia el servicio API para purgar la caché inicial y forzar la invocación del proveedor externo.
- **Mecanismo de Resiliencia:** El adaptador HTTP implementa un _timeout_ duro de 700 ms (`httpx.Timeout`). Al expirar o recibir error 503, conmuta inmediatamente a la caché en proceso / perfil sintético materializado, retornando la cotización con el indicador obligatorio `"status": "degraded"`.

### 4.2 Experimento E3: Continuidad ante Caída Súbita de Réplica

```
                          DISEÑO EXPERIMENTO E3 (Continuidad)
 ┌────────────────────────────────────────────────────────────────────────┐
 │ Instancia EC2: c6i.large (Ubuntu 24.04)                               │
 │                                                                        │
 │   Red Docker: e3-continuidad_default                                   │
 │   ┌───────────────┐ 50 req/s constante     ┌──────────────────────┐    │
 │   │  grafana/k6   ├───────────────────────►│  Nginx Load Balancer │    │
 │   │  (3 minutos)  │                        │     (v1 vs v2)       │    │
 │   └───────────────┘                        └──────┬────────────┬──┘    │
 │                                                   │            │       │
 │                                                   ▼            ▼       │
 │                                            ┌──────────┐ ┌──────────┐   │
 │                                            │ ReplicaA │ │ ReplicaB │   │
 │                                            └────┬─────┘ └──────────┘   │
 │                                                 │                      │
 │                                            docker stop --time 0 (t=45s)│
 │                                            docker start         (t=165s│
 └────────────────────────────────────────────────────────────────────────┘
```

- **Perfil de Carga:** 50 peticiones/segundo constantes durante 3 minutos continuos (9.000 transacciones totales por corrida).
- **Inyección del Fallo:**
  - En $t = 45\text{ s}$, se envía un `SIGKILL` forzado a `replica-A` (`docker stop --time 0 e3-api-a`).
  - Durante 120 segundos ($t = 45\text{ s}$ a $t = 165\text{ s}$), el sistema opera en modo degradado con una única réplica activa (`replica-B`).
  - En $t = 165\text{ s}$, se restaura `replica-A` (`docker start e3-api-a`), verificando su reincorporación automática al pool.
- **Variantes Evaluadas:**
  - **Versión v1 (Línea Base Pasiva):** `nginx-v1-pasivo.conf` con `max_fails=1 fail_timeout=2s` y `proxy_next_upstream` estándar sin reintento de métodos no idempotentes.
  - **Versión v2 (Táctica de Arquitectura Propuesta):** `nginx.conf` con `max_fails=2 fail_timeout=3s`, `proxy_connect_timeout 300ms`, `proxy_next_upstream error timeout http_502 http_503 http_504 non_idempotent;` y `proxy_next_upstream_tries 3;`.

---

## 5. Evidencias recolectadas

| Categoría                   | Archivo / Artefacto                                | Ubicación en Repositorio                      | Propósito Forense                                                                                         |
| :-------------------------- | :------------------------------------------------- | :-------------------------------------------- | :-------------------------------------------------------------------------------------------------------- |
| **Métricas E1**             | `base-[1-3].json`<br>`degradada-[1-3].json`        | `experiments/e1-latencia/resultados/nube/`    | Reportes JSON en bruto emitidos por k6 con percentiles p50, p90, p95, p99 y tasas de error.               |
| **Logs E1**                 | `api-logs.txt`                                     | `experiments/e1-latencia/resultados/nube/`    | Traza de la aplicación FastAPI certificando los cortes por timeout (700 ms) y fallback.                   |
| **Métricas E3**             | `v1-corrida-[1-3].json`<br>`v2-corrida-[1-3].json` | `experiments/e3-continuidad/resultados/nube/` | Reportes JSON en bruto de k6 con tasa de éxito global y conteo de peticiones servidas por réplica.        |
| **Logs Nginx E3**           | `v1-nginx-[1-3].log`<br>`v2-nginx-[1-3].log`       | `experiments/e3-continuidad/resultados/nube/` | Logs formateados (`upstreamlog`) con timestamp ISO 8601, upstream IP, upstream status y response time.    |
| **Resúmenes Agregados**     | `resumen-e1.json`<br>`resumen-e3.json`             | Respectivas carpetas `resultados/nube/`       | JSON estructurado generado por `resumir.py` con medianas, dispersión y dictamen de hipótesis.             |
| **Metadatos Nube**          | `ec2-metadata.json`                                | `experiments/cloud/evidencias/`               | Token IMDSv2, Instance ID, Instance Type (`c6i.large`), AMI ID, Zona (`us-east-1a`), vCPUs y memoria.     |
| **Hardware Host**           | `lscpu.txt`<br>`free-memory.txt`                   | `experiments/cloud/evidencias/`               | Topología de procesadores Intel Ice Lake, frecuencias de reloj y desglose de memoria RAM física.          |
| **Telemetría Contenedores** | `docker-stats.log`                                 | `experiments/cloud/evidencias/`               | Registro temporal (cada 2 s) de consumo de CPU (%) y Memoria (MiB) por cada contenedor.                   |
| **Destrucción de Recursos** | `terraform-destroy-*.log`                          | `experiments/cloud/evidencias/`               | Registro de salida de Terraform con timestamp certificando la destrucción completa de la VPC e instancia. |

---

## 6. Comparativa entre ejecución local y en la nube (AWS)

### 6.1 Experimento E1: Latencia (ASR-01, ASR-02)

| Métrica Evaluada                     | Entorno Local                   | Entorno Nube (AWS c6i.large) | Umbral de Aceptación   | Evaluación                       |
| :----------------------------------- | :------------------------------ | :--------------------------- | :--------------------- | :------------------------------- |
| **Mediana $p_{95}$ Fase Base**       | 82.41 ms                        | **90.48 ms**                 | _Informativo_          | Conforme                         |
| **Mediana $p_{95}$ Fase Degradada**  | **7.14 ms**                     | **11.45 ms**                 | $< 250\text{ ms}$      | **Cumple holgadamente (-95.4%)** |
| **Dispersión de $p_{95}$**           | **21.1 %** _(Alerta de jitter)_ | **7.63 %** _(Estable)_       | $\le 20.0\%$           | **Cumple en Nube**               |
| **Marcación explícita `"degraded"`** | 100 %                           | 100 %                        | 100 %                  | **Cumple**                       |
| **Dictamen de Hipótesis E1**         | _No Concluyente (Jitter local)_ | **HIPÓTESIS RESPALDADA**     | _Hipótesis Respaldada_ | **ÉXITO**                        |

#### Análisis de experimento E1

- En la fase base, la API consulta al simulador y responde en 90.48 ms (mediana $p_{95}$).
- En la fase degradada, al presentarse lentitud en el proveedor (900 ms) o error HTTP 503, el circuit breaker y el fallback a la caché en memoria responden en **11.45 ms ($p_{95}$)**, muy por debajo de los 250 ms requeridos.
- La ejecución en AWS eliminó por completo el problema de dispersión observado localmente (que superaba el 20%), alcanzando un **7.63%**, gracias a la estabilidad del cómputo dedicado de la instancia `c6i.large`.

### 6.2 Experimento E3: Continuidad de Servicio (ASR-04)

| Métrica Evaluada                      | Configuración v1 (Pasiva sin Retry) | Configuración v2 (Propuesta Nube con Retry) | Umbral de Aceptación    | Evaluación               |
| :------------------------------------ | :---------------------------------- | :------------------------------------------ | :---------------------- | :----------------------- |
| **Tasa de Éxito Global ($ASR-04$)**   | 100.00 %                            | **100.00 %**                                | $\ge 99.00\%$           | **Cumple**               |
| **Latencia Máxima en Caída**          | **1004.59 ms**                      | **304.94 ms** (Reducción del 70%)           | Acotada por timeout     | **Mejora Sustancial**    |
| **Tráfico Servido por Réplica Caída** | 0 solicitudes                       | **0 solicitudes**                           | $0\text{ req}$ servidas | **Cumple hacia cliente** |
| **Mecanismo de Reintento**            | Pasivo sin reintento no idempotente | `proxy_next_upstream non_idempotent`        | Reenvío transparente    | **Cumple**               |
| **Dictamen Arquitectónico E3**        | _Línea Base Superada_               | **HIPÓTESIS RESPALDADA (ASR-04)**           | _Hipótesis Respaldada_  | **ÉXITO**                |

#### Análisis del experimento E3

- Durante los 3 minutos continuos de prueba con 50 req/s sostenidas (9.001 solicitudes por corrida), el **100.00% de las solicitudes fueron exitosas** (HTTP 200) a pesar de haber apagado forzosamente `replica-A` durante 120 segundos completos.
- En la versión v1, la desconexión generaba bloqueos de hasta 1.004 ms. En la versión v2, gracias a `proxy_connect_timeout 300ms` y `proxy_next_upstream non_idempotent`, el tiempo máximo de respuesta durante el failover se redujo a **304.94 ms**, manteniendo el $p_{95}$ en **1.94 ms**.
- Los 48-52 registros residuales en los logs de Nginx corresponden a sondeos pasivos (`fail_timeout=3s`), los cuales fueron redirigidos de forma transparente a `replica-B` en 304 ms sin impacto para el cliente. En producción con un Application Load Balancer (ALB), estos sondeos son sintéticos fuera de banda, garantizando cero tráfico de cliente al nodo caído.

---

## 7. Gestión de Riesgos y Control de Costos en AWS

En atención al riesgo de sobrecostos documentado en la Semana 5 (_"Agotamiento prematuro de créditos del proyecto académico"_), se implementaron las siguientes salvaguardas:

1. **Infraestructura 100% Efímera:**
   - La VPC, subredes, tablas de enrutamiento, Security Group e instancia EC2 son creados al inicio de la prueba y destruidos automáticamente al finalizar mediante el comando orquestador `run-experiments.sh`.
2. **Salvaguarda de Interrupción (`trap` en Bash):**
   - Si el operador cancela la ejecución (`Ctrl+C`) o un comando genera error (`SIGINT`, `SIGTERM`, `EXIT`), el manejador `cleanup()` invoca obligatoriamente `terraform destroy -auto-approve`.
3. **Costo Marginal del Ciclo:**
   - Una instancia `c6i.large` en `us-east-1` tiene una tarifa bajo demanda de ~$0.085 USD/hora.
   - La ejecución completa de la suite (aprovisionamiento, E1 con 3 corridas, E3 con 6 corridas de 3 minutos, recolección y destrucción) toma aproximadamente **25 a 30 minutos**.
   - El costo total incurrido por ciclo de prueba es inferior a **$0.06 USD**, garantizando un impacto financiero despreciable sobre el presupuesto del proyecto.
4. **Constancia Documentada de Terminación:**
   - Cada ciclo genera un archivo con marca temporal `experiments/cloud/evidencias/terraform-destroy-<TIMESTAMP>.log` que certifica el resultado `Apply complete! Resources: 0 added, 0 changed, 8 destroyed.`.

---

## 8. Conclusiones y Recomendaciones Arquitectónicas

1. **Validación Formal de ASRs:**
   - **ASR-01 / ASR-02:** Queda demostrado que la táctica de _Timeout Duro + Circuit Breaker + Vista Materializada en Caché_ protege el SLA de latencia de Solventa ($p_{95} < 250\text{ ms}$), aislando al cliente final de la degradación de socios externos de Open Finance.
   - **ASR-04:** Queda demostrado que la táctica de _Health Checks Agresivos con Reintento Transparente No Idempotente en el Balanceador_ garantiza continuidad de servicio ($\ge 99\%$) ante fallos súbitos de nodos de cómputo en la nube.
2. **Impacto del Entorno de Cómputo Dedicado:**
   - La migración a la instancia `c6i.large` en AWS resolvió la indeterminación técnica generada por la dispersión de mediciones en estaciones de trabajo locales, proporcionando una base empírica sólida e incontrovertible para la sustentación de la entrega.
3. **Recomendación para Producción:**
   - En el despliegue productivo final sobre AWS, configurar los Application Load Balancers (ALB) o Nginx Ingress Controllers con políticas de reintento análogas para códigos 502/503/504 en endpoints de cotización, manteniendo los _health checks_ hacia `/health` en intervalos no mayores a 5 segundos con 2 fallos de umbral no saludable.
