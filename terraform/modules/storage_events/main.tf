# Clave KMS para cifrado de almacenamiento de documentos y mensajes SQS (HA-15)
resource "aws_kms_key" "storage" {
  description             = "KMS Key para S3 y SQS de Solventa Seguros"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-storage-kms-${var.environment}"
  }
}

# Bucket S3 para pólizas, certificados y documentos (HA-08: versionado)
resource "aws_s3_bucket" "documents" {
  bucket = "${var.project_name}-documents-${var.environment}"

  tags = {
    Name = "${var.project_name}-documents-${var.environment}"
  }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.storage.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Dead Letter Queue (DLQ) para eventos fallidos
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-events-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 días
  kms_master_key_id         = aws_kms_key.storage.id

  tags = {
    Name = "${var.project_name}-events-dlq-${var.environment}"
  }
}

# Cola principal SQS para eventos con redirección a DLQ tras 3 reintentos (HA-08)
resource "aws_sqs_queue" "events" {
  name                      = "${var.project_name}-events-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600 # 4 días
  receive_wait_time_seconds = 20     # Long polling
  kms_master_key_id         = aws_kms_key.storage.id

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "${var.project_name}-events-${var.environment}"
  }
}
