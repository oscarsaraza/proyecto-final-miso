variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "target_group_arn" {
  type = string
}

variable "ecr_image_url" {
  type = string
}

variable "db_host" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "jwt_secret_key" {
  description = "Llave de firma de los tokens del backend"
  type        = string
  sensitive   = true
}

variable "otp_secret_key" {
  description = "Llave del MAC de los códigos de un solo uso"
  type        = string
  sensitive   = true
}

variable "sqs_queue_url" {
  type = string
}

variable "s3_bucket_name" {
  type = string
}
