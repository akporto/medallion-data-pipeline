project     = "medallion-aknp"
environment = "prod"
aws_region  = "us-east-1"

# S3
force_destroy_buckets = false
bronze_lifecycle_days = 30

# SQS
sqs_visibility_timeout_seconds = 300
sqs_message_retention_seconds  = 345600
sqs_max_receive_count          = 3

# DynamoDB
enable_pitr                  = true
dynamodb_deletion_protection = true

# Lambda
log_level               = "WARNING"
lambda_memory_size      = 256
lambda_timeout          = 60
idempotency_ttl_seconds = 86400

# Glue
glue_worker_type       = "G.2X"
glue_number_of_workers = 5
glue_execution_class   = "STANDARD"

tags = {
  Project     = "medallion"
  Environment = "prod"
  ManagedBy   = "terraform"
}
