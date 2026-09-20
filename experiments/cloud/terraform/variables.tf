variable "aws_region" {
  description = "Región de AWS donde se desplegará la infraestructura efímera"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "Tipo de instancia EC2. Se utiliza c6i.large para cómputo dedicado sin jitter de CPU"
  type        = string
  default     = "c6i.large"
}

variable "project_name" {
  description = "Prefijo para nombrar recursos y etiquetas de auditoría"
  type        = string
  default     = "solventa-experimentos"
}

variable "operator_cidr" {
  description = "CIDR de la IP pública del operador para restringir el acceso SSH (ej. X.X.X.X/32)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "public_key_path" {
  description = "Ruta a la llave SSH pública existente (opcional). Si se deja vacía, Terraform generará una llave efímera."
  type        = string
  default     = ""
}
