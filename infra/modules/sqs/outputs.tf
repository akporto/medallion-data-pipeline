output "ingestion_queue_arn" {
  description = "ARN of the SQS ingestion queue."
  value       = aws_sqs_queue.ingestion.arn
}

output "ingestion_queue_url" {
  description = "URL of the SQS ingestion queue."
  value       = aws_sqs_queue.ingestion.url
}

output "dlq_arn" {
  description = "ARN of the dead-letter queue."
  value       = aws_sqs_queue.dlq.arn
}

output "dlq_url" {
  description = "URL of the dead-letter queue."
  value       = aws_sqs_queue.dlq.url
}
