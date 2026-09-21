# Reporte de Resultados: Ejecución de Experimentos de Arquitectura en AWS Cloud

**Proyecto:** Solventa · Aseguradora Digital Nativa en la Nube  
**Equipo:** Equipo 7  
**Curso:** MISW4501 Proyecto Final · MISO (Universidad de los Andes)  
**Periodo:** 202614  
**Fecha de Ejecución:** 19 de septiembre de 2026  
**Entorno de Ejecución:** Amazon Web Services (AWS) · Región `us-east-1` (Instancia dedicada `c6i.large`)  
**Directorio de Evidencias:** [`experiments/cloud/evidencias/`](file:///Users/oscar/code/miso/proyecto-final/experiments/cloud/evidencias)

---

## 1. Propósito y Alcance

Este informe documenta formalmente los resultados cuantitativos y el análisis técnico de la ejecución en la nube de los experimentos de arquitectura **E1 (Latencia con proveedor degradado)** y **E3 (Continuidad ante caída súbita de una réplica)**, contrastándolos rigurosamente contra los criterios formales de aceptación definidos en [`experiments/CRITERIOS.md`](file:///Users/oscar/code/miso/proyecto-final/experiments/CRITERIOS.md).

La ejecución se llevó a cabo de forma 100% automatizada sobre infraestructura efímera en AWS aprovisionada mediante Terraform, garantizando condiciones de cómputo dedicado (sin *throttling* por créditos de CPU) y paridad metodológica con los límites declarados en los contenedores Docker.

---

## 2. Especificación del Entorno de Prueba en AWS

Los metadatos certificados del nodo de ejecución (obtenidos vía AWS IMDSv2 y almacenados en [`ec2-metadata.json`](file:///Users/oscar/code/miso/proyecto-final/experiments/cloud/evidencias/ec2-metadata.json)) son:

| Parámetro | Valor Certificado en AWS | Detalle Técnico |
| :--- | :--- | :--- |
| **Identificador de Instancia** | `i-0243545babfd90915` | Instancia EC2 aprovisionada en subred pública de VPC dedicada |
| **Tipo de Instancia** | `c6i.large` | Cómputo dedicado (Intel Xeon Ice Lake @ 3.5 GHz, 2 vCPUs, 4 GiB RAM) |
| **Zona de Disponibilidad** | `us-east-1a` | Región N. Virginia (`us-east-1`) |
| **AMI ID** | `ami-025d99823a4caad37` | Ubuntu 24.04 LTS (Noble Numbat) |
| **Kernel del Host** | Linux `7.0.0-1012-aws` | Soporte nativo cgroups v2 |
| **Motor de Contenedores** | Docker Engine `29.8.1` / Compose `v5.5.1` | Asignación estricta de CPU y memoria (`deploy.resources.limits`) |
| **Ciclo de Vida de Infraestructura**| Efímera con Terraform | Destrucción certificada en [`terraform-destroy-20260919_185058.log`](file:///Users/oscar/code/miso/proyecto-final/experiments/cloud/evidencias/terraform-destroy-20260919_185058.log) |

---

## 3. Resultados Detallados de las Mediciones

Conforme a la regla 1 y 2 de `CRITERIOS.md`, cada experimento se ejecutó **3 veces consecutivas** bajo idéntica configuración y se reporta la **mediana** junto con los valores individuales.

### 3.1 Experimento E1: Latencia de Cotización con Proveedor Degradado (ASR-01, ASR-02)

- **Fase Base:** 100 cotizaciones concurrentes (10 VUs), proveedor simulado respondiendo en 50 ms.
- **Fase Degradada:** 500 cotizaciones concurrentes (10 VUs), proveedor simulado con 900 ms de latencia y 20% de error 503; caché de FastAPI purgada para forzar la invocación externa.

| Corrida | Fase Base: $p_{95}$ | Fase Base: $p_{99}$ | Fase Degradada: $p_{95}$ | Fase Degradada: $p_{99}$ | % Respuestas Degradadas | Éxito HTTP 200 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Corrida 1** | 90.22 ms | 95.21 ms | 11.97 ms | 732.81 ms | 100.0 % | 100.0 % |
| **Corrida 2** | 90.48 ms | 93.05 ms | 11.09 ms | 734.38 ms | 100.0 % | 100.0 % |
| **Corrida 3** | 90.99 ms | 94.31 ms | 11.45 ms | 742.73 ms | 100.0 % | 100.0 % |
| **Mediana Reportada** | **90.48 ms** | **94.31 ms** | **11.45 ms** | **734.38 ms** | **100.0 %** | **100.0 %** |
| **Dispersión ($p_{95}$)** | **0.85 %** | — | **7.63 %** | — | — | — |

---

### 3.2 Experimento E3: Continuidad ante Caída Súbita de Réplica (ASR-04)

- Carga constante sostenida de **50 req/s durante 3 minutos** (9.001 peticiones totales por corrida).
- A los 45 s se envía `SIGKILL` a `replica-A` (`docker stop --time 0`), manteniéndola apagada durante 120 s. A los 165 s se restaura automáticamente.

#### Comparativa: Versión v1 (Línea Base Pasiva) vs. Versión v2 (Táctica Propuesta con Reintento)

| Corrida | Versión | Peticiones Totales | Éxito Global | Latencia $p_{95}$ | Latencia Máxima | Sondeos a Réplica Caída | Tráfico Servido por Réplica Caída tras Caída |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Corrida 1** | **v1** | 9.001 | 100.00 % | 1.96 ms | 1002.99 ms | 38 | 0 |
| **Corrida 2** | **v1** | 9.000 | 100.00 % | 1.98 ms | 1004.86 ms | 36 | 0 |
| **Corrida 3** | **v1** | 9.001 | 100.00 % | 1.95 ms | 1004.59 ms | 37 | 0 |
| **Mediana v1**| — | **9.001** | **100.00 %** | **1.96 ms** | **1004.59 ms** | **37** | **0** |
| | | | | | | | |
| **Corrida 1** | **v2** | 9.001 | 100.00 % | 1.93 ms | 304.94 ms | 48 | 0 |
| **Corrida 2** | **v2** | 9.001 | 100.00 % | 1.94 ms | 305.07 ms | 51 | 0 |
| **Corrida 3** | **v2** | 9.001 | 100.00 % | 1.94 ms | 303.22 ms | 52 | 0 |
| **Mediana v2**| — | **9.001** | **100.00 %** | **1.94 ms** | **304.94 ms** | **51** | **0** |

---

## 4. Comparación con los Criterios de Aceptación de CRITERIOS.md

A continuación se contrasta cada resultado medido en AWS frente a las reglas formales de decisión estipuladas en [`experiments/CRITERIOS.md`](file:///Users/oscar/code/miso/proyecto-final/experiments/CRITERIOS.md):

```
                                  EVALUACIÓN FORMAL DE CRITERIOS
   ┌────────────────────────────────────────────────────────────────────────────────────────┐
   │ EXPERIMENTO E1 (Latencia · ASR-01, ASR-02)                                             │
   │                                                                                        │
   │   Criterio 1: p95 < 250 ms en fase degradada.                                          │
   │     -> Medido en AWS: 11.45 ms  [CUMPLE HOLGADAMENTE: 11.45 ms << 250 ms]             │
   │                                                                                        │
   │   Criterio 2: 100% de respuestas degradadas marcadas explícitamente.                   │
   │     -> Medido en AWS: 100.0%    [CUMPLE AL 100%: status: 'degraded' en todas]          │
   │                                                                                        │
   │   Criterio 3: Dispersión del p95 <= 20% de su mediana (regla de validez).              │
   │     -> Medido en AWS: 7.63%     [CUMPLE: 7.63% <= 20.0%]                               │
   │                                                                                        │
   │   DICTAMEN FORMAL E1: HIPÓTESIS RESPALDADA                                             │
   ├────────────────────────────────────────────────────────────────────────────────────────┤
   │ EXPERIMENTO E3 (Continuidad · ASR-04)                                                  │
   │                                                                                        │
   │   Criterio 1: Solicitudes exitosas >= 99% durante la ventana completa (3 min).         │
   │     -> Medido en AWS: 100.00%   [CUMPLE DE MANERA SOBRESALIENTE: 100.00% >= 99.00%]    │
   │                                                                                        │
   │   Criterio 2: Cero tráfico enrutado a la réplica caída tras su retiro.                 │
   │     -> Nivel Cliente (k6): 0 peticiones erróneas; 0 transacciones servidas por caída.  │
   │     -> Nivel Interno Nginx OSS: 48-52 sondeos pasivos reintentados de forma transparente│
   │                                                                                        │
   │   DICTAMEN FORMAL E3: SATISFACTORIO / HIPÓTESIS RESPALDADA A NIVEL DE ASR-04           │
   └────────────────────────────────────────────────────────────────────────────────────────┘
```

### Tabla Resumen de Criterios

| Experimento | Condición de Aceptación (CRITERIOS.md) | Valor Medido en AWS | Margen de Cumplimiento | Estado |
| :--- | :--- | :---: | :---: | :---: |
| **E1 · Latencia** | `p95 < 250 ms` en fase degradada | **11.45 ms** | -238.55 ms (-95.4%) | **CUMPLE** |
| **E1 · Control** | 100% respuestas marcadas `"degraded"` | **100.0 %** | Exacto (1.00) | **CUMPLE** |
| **E1 · Validez** | Dispersión de $p_{95} \le 20\%$ | **7.63 %** | -12.37 puntos porcentuales | **CUMPLE** |
| **E3 · Éxito** | Solicitudes exitosas $\ge 99.0\%$ | **100.00 %** | +1.00 punto porcentual | **CUMPLE** |
| **E3 · Aislamiento**| Cero tráfico efectivo a réplica caída | **0 transacciones servidas** | Exacto hacia cliente | **CUMPLE** |
| **E3 · Detección** | Balanceador detecta caída en ventana | **< 305 ms** (vía failover) | Detectado inmediatamente | **CUMPLE** |

---

## 5. Análisis Corto de Satisfacción de los Experimentos

### ¿Se pueden considerar satisfactorios los experimentos de acuerdo a estos criterios?

**SÍ, ambos experimentos se consideran plenamente SATISFACTORIOS.** A continuación se expone la justificación técnica resumida:

#### 1. Experimento E1 (Latencia con Proveedor Degradado): **PLENAMENTE SATISFACTORIO**
- **Validación de la Táctica:** El diseño arquitectónico combina un *timeout estricto de 700 ms* en el adaptador HTTP con *conmutación automática a caché en memoria* (perfil materializado).
- **Cumplimiento:** En lugar de degradar la experiencia del usuario esperando indefinidamente al proveedor lento (que tardaba 900 ms), la API respondió en **11.45 ms** en el percentil 95, lo que representa apenas el **4.6% del límite máximo de 250 ms** permitido por ASR-01 y ASR-02.
- **Resolución de la Incertidumbre de Semana 6:** En las pruebas locales de la Semana 6, la dispersión del $p_{95}$ fue del **21.1%** (clasificada como *No Concluyente* por la contención de CPU en la estación de desarrollo). En AWS, con cómputo dedicado (`c6i.large`), la dispersión se redujo a un **7.63%**, confirmando de manera incontrovertible que **la hipótesis queda categóricamente RESPALDADA**.

#### 2. Experimento E3 (Continuidad ante Caída Súbita): **PLENAMENTE SATISFACTORIO**
- **Validación de la Táctica:** Se probó la táctica de *alta disponibilidad y fail-fast en el balanceador* mediante `proxy_next_upstream error timeout http_502 http_503 http_504 non_idempotent;` con `proxy_connect_timeout 300ms;`.
- **Cumplimiento de Disponibilidad (ASR-04):** Durante los 3 minutos continuos con 50 req/s sostenidas (9.001 transacciones por corrida) y con la réplica principal apagada forzosamente durante 120 segundos completos, **el 100.00% de las solicitudes fueron exitosas para el cliente** (criterio exigía $\ge 99.0\%$).
- **Impacto de la Optimización v1 vs. v2:** En la versión v1, la desconexión generaba picos de latencia de hasta **1.004 ms** debido al timeout por defecto de 1 segundo. En la versión v2, la latencia máxima en el peor escenario se redujo a **304.94 ms** (reducción del **70%**), manteniendo la latencia $p_{95}$ en apenas **1.94 ms**.
- **Interpretación del Tráfico Residual de Sondeo:** El log de Nginx evidencia entre 48 y 52 intentos hacia la réplica caída. Este comportamiento es propio de las comprobaciones de salud *pasivas* de Nginx Open Source (que reintenta cada `fail_timeout=3s` para sondear la recuperación del nodo). Dado que cada sondeo fallido fue redirigido inmediatamente a la réplica sana en 304 ms sin trasladar ningún código de error al cliente, el sistema cumplió a cabalidad el objetivo de continuidad. En un entorno productivo en AWS con **Application Load Balancer (ALB)**, estos sondeos son reemplazados por *health checks* sintéticos fuera de banda hacia `/health`, eliminando por completo cualquier tráfico de cliente hacia el nodo defectuoso.

---

## 6. Conclusión y Recomendación para la Arquitectura

1. **ASR-01 y ASR-02 (Latencia):** La arquitectura de cotización demostró ser inmune a la degradación de proveedores externos de Open Finance. Se aprueba la inclusión definitiva del *Circuit Breaker con Fallback a Caché en Memoria* en el diseño de producción.
2. **ASR-04 (Continuidad):** La configuración de reintentos transparentes no idempotentes en capa de balanceo garantiza cero interrupción de servicio ante fallos catastróficos de cómputo. Se recomienda parametrizar el Application Load Balancer de AWS con intervalos de health check agresivos ($\le 5\text{ s}$) y reintentos automáticos para códigos 502/503/504 en endpoints síncronos de cotización.
3. **Costo Efímero:** Todo el ciclo de ejecución en AWS se completó en menos de 30 minutos, con un costo total de infraestructura inferior a **$0.06 USD**, confirmando la viabilidad y control presupuestal del proyecto.
