output "bucket_ids" {
  description = "Map of layer name (bronze/silver/gold) to S3 bucket ID."
  value       = { for k, v in aws_s3_bucket.medallion : k => v.id }
}

output "bucket_arns" {
  description = "Map of layer name (bronze/silver/gold) to S3 bucket ARN."
  value       = { for k, v in aws_s3_bucket.medallion : k => v.arn }
}

output "bronze_bucket_id" {
  description = "ID (name) of the Bronze S3 bucket — landing zone for raw events."
  value       = aws_s3_bucket.medallion["bronze"].id
}

output "silver_bucket_id" {
  description = "ID (name) of the Silver S3 bucket — validated Parquet events."
  value       = aws_s3_bucket.medallion["silver"].id
}

output "gold_bucket_id" {
  description = "ID (name) of the Gold S3 bucket — feature-store-ready aggregates consumed by Snowpipe."
  value       = aws_s3_bucket.medallion["gold"].id
}
