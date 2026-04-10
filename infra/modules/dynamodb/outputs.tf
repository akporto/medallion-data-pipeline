output "table_name" {
  description = "Name of the DynamoDB idempotency table."
  value       = aws_dynamodb_table.idempotency.name
}

output "table_arn" {
  description = "ARN of the DynamoDB idempotency table."
  value       = aws_dynamodb_table.idempotency.arn
}
