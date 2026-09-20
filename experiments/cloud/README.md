# Ejecución de Experimentos de Arquitectura en AWS Cloud

Este directorio contiene la infraestructura como código (Terraform) y los scripts de orquestación para ejecutar los experimentos de arquitectura **E1 (Latencia con proveedor degradado)** y **E3 (Continuidad ante caída súbita de réplica)** en una instancia EC2 de cómputo dedicado (`c6i.large`) en AWS.

## Estructura

```
experiments/cloud/
├── README.md                      # Esta guía
├── run-experiments.sh             # Orquestador local automatizado (apply -> run -> collect -> destroy)
├── terraform/
│   ├── main.tf                    # VPC dedicada, Subred, Security Group, Llave SSH y EC2 c6i.large
│   ├── variables.tf               # Parámetros (región, tipo de instancia, CIDR operador)
│   ├── outputs.tf                 # IPs, identificadores y comandos de conexión
│   └── terraform.tfvars.example   # Ejemplo de valores de variables
├── scripts/
│   └── remote-runner.sh           # Script que se ejecuta en la instancia EC2
└── evidencias/                    # Directorio donde se guardan metadatos, telemetría y constancia de destrucción
```

---

## 1. Requisitos Previos y Obtención de Credenciales AWS

### 1.1 Herramientas instaladas localmente
- `aws` (AWS CLI v2)
- `terraform` (>= 1.5.0)
- `ssh`, `scp`, `rsync`
- `python3` (>= 3.9)

### 1.2 Permisos requeridos para el usuario IAM

El plan de Terraform en `experiments/cloud/terraform/` aprovisiona recursos de red y cómputo (VPC, subredes, Internet Gateway, tablas de enrutamiento, Security Group, Key Pair, instancia EC2 c6i.large y volumen EBS gp3).

Por tanto, el usuario de IAM únicamente requiere la política administrada estándar de AWS:
- **`AmazonEC2FullAccess`** (`arn:aws:iam::aws:policy/AmazonEC2FullAccess`).

---

### 1.3 Creación del usuario y obtención de claves vía AWS CLI (como Root)

**Sí, es posible y es la mejor práctica recomendada por AWS** crear el usuario de IAM y obtener las claves desde la terminal autenticado como usuario root:

#### Opción A: Usando el script automatizado
```bash
./experiments/cloud/setup-iam-user.sh solventa-experiments
```
Crea el usuario, le asocia `AmazonEC2FullAccess`, genera el par de claves y entrega los comandos `export` listos.

#### Opción B: Ejecución manual con AWS CLI
```bash
# 1. Crear el usuario IAM
aws iam create-user --user-name "solventa-experiments"

# 2. Adjuntar la política requerida
aws iam attach-user-policy \
  --user-name "solventa-experiments" \
  --policy-arn "arn:aws:iam::aws:policy/AmazonEC2FullAccess"

# 3. Generar la clave de acceso (Access Key ID y Secret Access Key)
CLAVES=$(aws iam create-access-key --user-name "solventa-experiments" --query 'AccessKey.[AccessKeyId,SecretAccessKey]' --output text)

# 4. Exportar las credenciales al entorno actual
export AWS_ACCESS_KEY_ID=$(echo "$CLAVES" | awk '{print $1}')
export AWS_SECRET_ACCESS_KEY=$(echo "$CLAVES" | awk '{print $2}')
export AWS_DEFAULT_REGION="us-east-1"
unset AWS_SESSION_TOKEN  # Clave permanente AKIA, no aplica session token
```

---

## 2. Ejecución Automatizada

Una vez exportadas las variables en la terminal:


```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_DEFAULT_REGION="us-east-1"
unset AWS_SESSION_TOKEN  # Asegura que no haya token residual

./experiments/cloud/run-experiments.sh
```


---

## 3. Flujo del Orquestador (`run-experiments.sh`)

El script realiza de punta a punta:
1. Valida herramientas locales y credenciales activas con `aws sts get-caller-identity`.
2. Detecta la IP pública del operador y restringe el Security Group SSH (`operator_cidr`).
3. Despliega la VPC e instancia `c6i.large` (cómputo dedicado sin jitter de CPU) con Terraform.
4. Espera a que la instancia termine de aprovisionar Docker CE y herramientas (`.cloud-init-ready`).
5. Sincroniza el código de los experimentos a la instancia vía `rsync`.
6. Dispara `remote-runner.sh` (recoge metadatos EC2, telemetría `docker stats`, 3 corridas de E1, 6 corridas de E3 y genera resúmenes).
7. Descarga las evidencias y extrae los resultados en `experiments/e1-latencia/resultados/nube/` y `experiments/e3-continuidad/resultados/nube/`.
8. Ejecuta `resumir.py` generando la tabla comparativa Local vs Nube.
9. **Destruye automáticamente la infraestructura con `terraform destroy`** (incluso si se cancela el script con Ctrl+C gracias a su `trap` de seguridad).
10. Guarda la constancia de terminación con timestamp en `experiments/cloud/evidencias/terraform-destroy.log`.

---

## 4. Auditoría y Evidencias Recolectadas

Al finalizar, se habrán generado los siguientes artefactos:
- **Resultados k6 y logs E1 Nube:** `experiments/e1-latencia/resultados/nube/` (`base-*.json`, `degradada-*.json`, `api-logs.txt`, `resumen-e1.json`).
- **Resultados k6 y logs E3 Nube:** `experiments/e3-continuidad/resultados/nube/` (`v1-corrida-*.json`, `v2-corrida-*.json`, `v1-nginx-*.log`, `v2-nginx-*.log`, `resumen-e3.json`).
- **Metadatos del nodo EC2:** `experiments/cloud/evidencias/ec2-metadata.json`, `lscpu.txt`, `free-memory.txt`.
- **Telemetría de consumo de contenedores:** `experiments/cloud/evidencias/docker-stats.log`.
- **Constancia de destrucción:** `experiments/cloud/evidencias/terraform-destroy-*.log`.
