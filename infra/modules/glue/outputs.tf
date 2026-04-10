output "bronze_to_silver_job_name" {
  description = "Name of the Glue job that processes Bronze → Silver transitions."
  value       = aws_glue_job.bronze_to_silver.name
}

output "silver_to_gold_job_name" {
  description = "Name of the Glue job that processes Silver → Gold transitions."
  value       = aws_glue_job.silver_to_gold.name
}
