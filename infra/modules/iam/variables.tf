variable "project" {
  description = "Project name used as a prefix for all resource names."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, hom, prod)."
  type        = string
}

variable "ingestion_queue_arn" {
  description = "ARN of the SQS ingestion queue granted to the Lambda execution role."
  type        = string
}

variable "silver_bucket_arn" {
  description = "ARN of the Silver S3 bucket; Lambda may write validated events here."
  type        = string
}

variable "bronze_bucket_arn" {
  description = "ARN of the Bronze S3 bucket; Glue may read raw events from here."
  type        = string
}

variable "gold_bucket_arn" {
  description = "ARN of the Gold S3 bucket; Glue may write feature-store datasets here."
  type        = string
}

variable "idempotency_table_arn" {
  description = "ARN of the DynamoDB idempotency table; Lambda needs PutItem and UpdateItem access."
  type        = string
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
