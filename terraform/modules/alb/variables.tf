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
  description = "Subredes privadas donde vive el balanceador interno"
  type        = list(string)
}
