output "s3_bucket_name" {
  value = aws_s3_bucket.documents.id
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.documents.arn
}

output "sqs_queue_url" {
  value = aws_sqs_queue.events.url
}

output "sqs_queue_arn" {
  value = aws_sqs_queue.events.arn
}

output "dlq_queue_url" {
  value = aws_sqs_queue.dlq.url
}
