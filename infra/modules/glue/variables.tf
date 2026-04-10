variable "project" {
  description = "Project name used as a prefix for all resource names."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, hom, prod)."
  type        = string
}

variable "glue_role_arn" {
  description = "ARN of the IAM service role assigned to Glue ETL jobs."
  type        = string
}

variable "scripts_bucket" {
  description = "S3 bucket where Glue PySpark scripts are stored."
  type        = string
}

variable "bronze_to_silver_script_key" {
  description = "S3 key of the Bronze → Silver PySpark script."
  type        = string
  default     = "glue-scripts/bronze_to_silver.py"
}

variable "silver_to_gold_script_key" {
  description = "S3 key of the Silver → Gold PySpark script."
  type        = string
  default     = "glue-scripts/silver_to_gold.py"
}

variable "bronze_bucket_name" {
  description = "Name of the Bronze S3 bucket (raw event landing zone)."
  type        = string
}

variable "silver_bucket_name" {
  description = "Name of the Silver S3 bucket (validated Parquet events)."
  type        = string
}

variable "gold_bucket_name" {
  description = "Name of the Gold S3 bucket (feature-store-ready aggregates)."
  type        = string
}

variable "glue_database_name" {
  description = "Glue Data Catalog database name used for schema registration."
  type        = string
}

variable "worker_type" {
  description = "G.1X for cost efficiency in dev; G.2X for prod."
  type        = string
  default     = "G.1X"
}

variable "number_of_workers" {
  description = "Number of Glue Data Processing Units (DPUs) to allocate."
  type        = number
  default     = 2
}

variable "execution_class" {
  description = "FLEX uses spare capacity (~34% cheaper) — safe for non-SLA jobs. STANDARD for prod."
  type        = string
  default     = "FLEX"

  validation {
    condition     = contains(["FLEX", "STANDARD"], var.execution_class)
    error_message = "execution_class must be either 'FLEX' or 'STANDARD'."
  }
}

variable "job_timeout_minutes" {
  description = "Maximum job run duration in minutes before Glue forces a timeout. Prevents runaway cost."
  type        = number
  default     = 60
}

variable "max_retries" {
  description = "Number of automatic retries on job failure. 0 forces explicit re-trigger for investigation."
  type        = number
  default     = 0
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
