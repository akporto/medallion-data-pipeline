variable "project" {
  description = "Project name used as a prefix for all resource names."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, hom, prod)."
  type        = string
}

variable "visibility_timeout_seconds" {
  description = "Must be >= Lambda timeout to avoid duplicate in-flight processing."
  type        = number
  default     = 300
}

variable "message_retention_seconds" {
  description = "How long SQS retains unprocessed messages. Default: 4 days."
  type        = number
  default     = 345600
}

variable "max_receive_count" {
  description = "Number of receive attempts before a message is sent to the DLQ."
  type        = number
  default     = 3
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
