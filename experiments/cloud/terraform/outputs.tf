output "instance_id" {
  description = "Identificador de la instancia EC2 creada"
  value       = aws_instance.experiment_node.id
}

output "instance_public_ip" {
  description = "Dirección IP pública de la instancia EC2"
  value       = aws_instance.experiment_node.public_ip
}

output "instance_type" {
  description = "Familia y tipo de la instancia desplegada"
  value       = aws_instance.experiment_node.instance_type
}

output "vpc_id" {
  description = "ID de la VPC dedicada"
  value       = aws_vpc.main.id
}

output "ssh_private_key_path" {
  description = "Ruta al archivo local de clave privada PEM generado"
  value       = local_sensitive_file.private_key.filename
}

output "ssh_command" {
  description = "Comando de conexión SSH listo para usar"
  value       = "ssh -i ${local_sensitive_file.private_key.filename} -o StrictHostKeyChecking=no ubuntu@${aws_instance.experiment_node.public_ip}"
}
