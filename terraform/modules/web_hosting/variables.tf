variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "alb_dns_name" {
  type        = string
  description = "DNS del Application Load Balancer para enrutar llamadas /api/* a través de CloudFront"
  default     = ""
}

