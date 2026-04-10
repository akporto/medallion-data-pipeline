variable "project" {
  description = "Project name used as a prefix for all resource names."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, hom, prod)."
  type        = string
}

variable "enable_pitr" {
  description = "Enable Point-In-Time Recovery. Recommended for prod."
  type        = bool
  default     = false
}

variable "deletion_protection_enabled" {
  description = "Prevents accidental table deletion via API or console. Always true in prod."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
