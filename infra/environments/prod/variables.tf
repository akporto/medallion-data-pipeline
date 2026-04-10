variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# ── S3 ────────────────────────────────────────────────────────────────────────

variable "force_destroy_buckets" {
  type    = bool
  default = false
}

variable "bronze_lifecycle_days" {
  type    = number
  default = 30
}

# ── SQS ───────────────────────────────────────────────────────────────────────

variable "sqs_visibility_timeout_seconds" {
  type    = number
  default = 300
}

variable "sqs_message_retention_seconds" {
  type    = number
  default = 345600
}

variable "sqs_max_receive_count" {
  type    = number
  default = 3
}

# ── DynamoDB ──────────────────────────────────────────────────────────────────

variable "enable_pitr" {
  type    = bool
  default = true
}

variable "dynamodb_deletion_protection" {
  type    = bool
  default = true
}

# ── Lambda ────────────────────────────────────────────────────────────────────

variable "log_level" {
  type    = string
  default = "WARNING"
}

variable "lambda_memory_size" {
  type    = number
  default = 256
}

variable "lambda_timeout" {
  type    = number
  default = 60
}

variable "idempotency_ttl_seconds" {
  type    = number
  default = 86400
}

variable "lambda_artifact_path" {
  description = "Path to the Lambda .zip deployment package."
  type        = string
  default     = "../../../artifacts/validator.zip"
}

# ── Glue ──────────────────────────────────────────────────────────────────────

variable "glue_worker_type" {
  type    = string
  default = "G.2X"
}

variable "glue_number_of_workers" {
  type    = number
  default = 5
}

variable "glue_execution_class" {
  description = "STANDARD guarantees SLA. Required for prod pipelines with time constraints."
  type        = string
  default     = "STANDARD"
}

# ── Tags ──────────────────────────────────────────────────────────────────────

variable "tags" {
  type    = map(string)
  default = {}
}
