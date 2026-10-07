output "alb_dns_name" {
  description = "DNS público del Application Load Balancer para tráfico API backend"
  value       = module.alb.alb_dns_name
}

output "ecr_repository_url" {
  description = "URL del repositorio ECR para subir imágenes Docker del backend"
  value       = module.ecr.repository_url
}

output "rds_endpoint" {
  description = "Punto de enlace de la base de datos PostgreSQL Multi-AZ"
  value       = module.rds.endpoint
}

output "s3_documents_bucket" {
  description = "Nombre del bucket S3 de almacenamiento de documentos y pólizas"
  value       = module.storage_events.s3_bucket_name
}

output "sqs_events_queue_url" {
  description = "URL de la cola SQS de eventos asíncronos"
  value       = module.storage_events.sqs_queue_url
}

output "cloudfront_domain_name" {
  description = "Nombre de dominio de CloudFront para acceso global al portal web"
  value       = module.web_hosting.cloudfront_domain_name
}
