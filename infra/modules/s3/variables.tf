variable "project" {
  description = "Project name used as a prefix for all resource names."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, hom, prod)."
  type        = string
}

variable "layers" {
  description = "List of Medallion layers to create (bronze, silver, gold)."
  type        = list(string)
  default     = ["bronze", "silver", "gold"]
}

variable "force_destroy" {
  description = "Allow bucket deletion even when non-empty. Set to true only in dev."
  type        = bool
  default     = false
}

variable "bronze_lifecycle_days" {
  description = "Days before Bronze raw/ objects transition to STANDARD_IA."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
