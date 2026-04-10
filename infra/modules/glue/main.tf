# ── Glue Catalog Database ─────────────────────────────────────────────────────

resource "aws_glue_catalog_database" "this" {
  name        = var.glue_database_name
  description = "Glue Catalog database for the ${var.project}-${var.environment} medallion pipeline."

  tags = var.tags
}

# ── PySpark Script Upload ─────────────────────────────────────────────────────
# etag with filemd5 ensures Terraform re-uploads when the source file changes,
# without requiring a manual taint of the resource.
#
# path.module resolves to the absolute path of this module directory
# (infra/modules/glue/), so ../../../ reaches the repository root.

resource "aws_s3_object" "bronze_to_silver_script" {
  bucket = var.scripts_bucket
  key    = var.bronze_to_silver_script_key
  source = "${path.module}/../../../src/glue/bronze_to_silver.py"
  etag   = filemd5("${path.module}/../../../src/glue/bronze_to_silver.py")

  tags = var.tags
}

resource "aws_s3_object" "silver_to_gold_script" {
  bucket = var.scripts_bucket
  key    = var.silver_to_gold_script_key
  source = "${path.module}/../../../src/glue/silver_to_gold.py"
  etag   = filemd5("${path.module}/../../../src/glue/silver_to_gold.py")

  tags = var.tags
}

# ── Glue Jobs ─────────────────────────────────────────────────────────────────

resource "aws_glue_job" "bronze_to_silver" {
  name              = "${var.project}-${var.environment}-bronze-to-silver"
  role_arn          = var.glue_role_arn
  glue_version      = "4.0"
  worker_type       = var.worker_type
  number_of_workers = var.number_of_workers
  execution_class   = var.execution_class
  timeout           = var.job_timeout_minutes
  max_retries       = var.max_retries

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket}/${var.bronze_to_silver_script_key}"
    python_version  = "3"
  }

  default_arguments = {
    "--job-bookmark-option"                   = "job-bookmark-enable"
    "--bronze_path"                           = "s3://${var.bronze_bucket_name}/raw/"
    "--silver_path"                           = "s3://${var.silver_bucket_name}/validated/"
    "--database_name"                         = var.glue_database_name
    "--enable-metrics"                        = "true"
    "--enable-continuous-cloudwatch-log"      = "true"
    "--enable-s3-parquet-optimized-committer" = "true"
  }

  tags = var.tags

  depends_on = [
    aws_s3_object.bronze_to_silver_script,
    aws_glue_catalog_database.this,
  ]
}

resource "aws_glue_job" "silver_to_gold" {
  name              = "${var.project}-${var.environment}-silver-to-gold"
  role_arn          = var.glue_role_arn
  glue_version      = "4.0"
  worker_type       = var.worker_type
  number_of_workers = var.number_of_workers
  execution_class   = var.execution_class
  timeout           = var.job_timeout_minutes
  max_retries       = var.max_retries

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket}/${var.silver_to_gold_script_key}"
    python_version  = "3"
  }

  default_arguments = {
    "--job-bookmark-option"                   = "job-bookmark-enable"
    "--silver_path"                           = "s3://${var.silver_bucket_name}/validated/"
    "--gold_path"                             = "s3://${var.gold_bucket_name}/features/"
    "--enable-metrics"                        = "true"
    "--enable-continuous-cloudwatch-log"      = "true"
    "--enable-s3-parquet-optimized-committer" = "true"
  }

  tags = var.tags

  depends_on = [
    aws_s3_object.silver_to_gold_script,
    aws_glue_catalog_database.this,
  ]
}
