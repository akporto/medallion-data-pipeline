project     = "medallion-aknp"
environment = "dev"
aws_region  = "us-east-1"

# S3
force_destroy_buckets = true
bronze_lifecycle_days = 30

# SQS
sqs_visibility_timeout_seconds = 300
sqs_message_retention_seconds  = 345600
sqs_max_receive_count          = 3

# DynamoDB
enable_pitr                  = false
dynamodb_deletion_protection = false

# Lambda
log_level               = "DEBUG"
lambda_memory_size      = 256
lambda_timeout          = 60
idempotency_ttl_seconds = 86400

# Glue
glue_worker_type       = "G.1X"
glue_number_of_workers = 2
glue_execution_class   = "FLEX"

tags = {
  Project     = "medallion"
  Environment = "dev"
  ManagedBy   = "terraform"
}
