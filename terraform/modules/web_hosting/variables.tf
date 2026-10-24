variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "alb_arn" {
  type        = string
  description = "ARN del balanceador interno al que CloudFront llega mediante un VPC origin"
  default     = ""
}

variable "alb_dns_name" {
  type        = string
  description = "DNS del Application Load Balancer para enrutar llamadas /api/* a través de CloudFront"
  default     = ""
}

