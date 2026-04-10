output "bronze_bucket_id" {
  description = "Name of the Bronze S3 bucket (landing zone for raw events)."
  value       = module.s3.bronze_bucket_id
}

output "silver_bucket_id" {
  description = "Name of the Silver S3 bucket (validated Parquet events)."
  value       = module.s3.silver_bucket_id
}

output "gold_bucket_id" {
  description = "Name of the Gold S3 bucket (feature-store aggregates for Snowpipe)."
  value       = module.s3.gold_bucket_id
}

output "ingestion_queue_url" {
  description = "URL of the SQS ingestion queue."
  value       = module.sqs.ingestion_queue_url
}

output "ingestion_queue_arn" {
  description = "ARN of the SQS ingestion queue."
  value       = module.sqs.ingestion_queue_arn
}

output "dlq_url" {
  description = "URL of the dead-letter queue."
  value       = module.sqs.dlq_url
}

output "lambda_function_name" {
  description = "Name of the validator Lambda function."
  value       = module.lambda.function_name
}

output "idempotency_table_name" {
  description = "Name of the DynamoDB idempotency table."
  value       = module.dynamodb.table_name
}
