variable "aws_region" {
  description = "Región de AWS para el despliegue Multi-AZ"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Nombre del ambiente (production, staging, dev)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Prefijo para los nombres de recursos de infraestructura"
  type        = string
  default     = "solventa"
}

variable "db_username" {
  description = "Usuario administrador de PostgreSQL en RDS"
  type        = string
  default     = "solventa_admin"
}

variable "db_password" {
  description = "Contraseña de la base de datos PostgreSQL en RDS"
  type        = string
  sensitive   = true
  default     = "SolventaSecurePass2026!"
}

variable "use_local_emulator" {
  description = "Habilitar para redirigir endpoints al emulador local Floci (http://localhost:4566)"
  type        = bool
  default     = false
}

variable "local_emulator_endpoint" {
  description = "URL del servicio de emulación local Floci"
  type        = string
  default     = "http://localhost:4566"
}

