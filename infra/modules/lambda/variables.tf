variable "project" {
  description = "Project name used as a prefix for all resource names."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, hom, prod)."
  type        = string
}

variable "execution_role_arn" {
  description = "IAM role ARN for the Lambda function."
  type        = string
}

variable "artifact_path" {
  description = "Local path to the Lambda deployment package (.zip)."
  type        = string
}

variable "silver_bucket_name" {
  description = "Name of the Silver S3 bucket where validated events are written."
  type        = string
}

variable "idempotency_table_name" {
  description = "Name of the DynamoDB idempotency table."
  type        = string
}

variable "ingestion_queue_arn" {
  description = "ARN of the SQS ingestion queue that triggers this Lambda."
  type        = string
}

variable "memory_size" {
  description = "Lambda memory in MB. Higher memory also allocates proportionally more CPU."
  type        = number
  default     = 256
}

variable "timeout" {
  description = "Lambda timeout in seconds. Must be <= SQS visibility_timeout_seconds."
  type        = number
  default     = 60
}

variable "idempotency_ttl_seconds" {
  description = "TTL for idempotency records in DynamoDB."
  type        = number
  default     = 86400
}

variable "log_level" {
  description = "Python log level passed as an environment variable (DEBUG, INFO, WARNING, ERROR)."
  type        = string
  default     = "INFO"
}

variable "log_retention_days" {
  description = "Number of days to retain Lambda CloudWatch logs. 0 means never expire."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
