terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }

  backend "s3" {
    bucket         = "medallion-aknp-dev-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "medallion-aknp-dev-tf-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# ── Core modules (no cross-dependencies) ─────────────────────────────────────

module "sqs" {
  source                     = "../../modules/sqs"
  project                    = var.project
  environment                = var.environment
  visibility_timeout_seconds = var.sqs_visibility_timeout_seconds
  message_retention_seconds  = var.sqs_message_retention_seconds
  max_receive_count          = var.sqs_max_receive_count
  tags                       = var.tags
}

module "s3" {
  source                = "../../modules/s3"
  project               = var.project
  environment           = var.environment
  force_destroy         = var.force_destroy_buckets
  bronze_lifecycle_days = var.bronze_lifecycle_days
  tags                  = var.tags
}

module "dynamodb" {
  source                      = "../../modules/dynamodb"
  project                     = var.project
  environment                 = var.environment
  enable_pitr                 = var.enable_pitr
  deletion_protection_enabled = var.dynamodb_deletion_protection
  tags                        = var.tags
}

module "iam" {
  source                = "../../modules/iam"
  project               = var.project
  environment           = var.environment
  ingestion_queue_arn   = module.sqs.ingestion_queue_arn
  silver_bucket_arn     = module.s3.bucket_arns["silver"]
  bronze_bucket_arn     = module.s3.bucket_arns["bronze"]
  gold_bucket_arn       = module.s3.bucket_arns["gold"]
  idempotency_table_arn = module.dynamodb.table_arn
  tags                  = var.tags
}

module "lambda" {
  source                  = "../../modules/lambda"
  project                 = var.project
  environment             = var.environment
  execution_role_arn      = module.iam.lambda_validator_role_arn
  artifact_path           = var.lambda_artifact_path
  silver_bucket_name      = module.s3.silver_bucket_id
  idempotency_table_name  = module.dynamodb.table_name
  ingestion_queue_arn     = module.sqs.ingestion_queue_arn
  log_level               = var.log_level
  memory_size             = var.lambda_memory_size
  timeout                 = var.lambda_timeout
  idempotency_ttl_seconds = var.idempotency_ttl_seconds
  tags                    = var.tags
}

module "glue" {
  source             = "../../modules/glue"
  project            = var.project
  environment        = var.environment
  glue_role_arn      = module.iam.glue_role_arn
  scripts_bucket     = module.s3.bronze_bucket_id
  bronze_bucket_name = module.s3.bronze_bucket_id
  silver_bucket_name = module.s3.silver_bucket_id
  gold_bucket_name   = module.s3.gold_bucket_id
  glue_database_name = "${var.project}_${var.environment}"
  worker_type        = var.glue_worker_type
  number_of_workers  = var.glue_number_of_workers
  execution_class    = var.glue_execution_class
  tags               = var.tags
}

# ── Cross-module wiring (resolves the S3 ↔ SQS circular dependency) ──────────

resource "aws_sqs_queue_policy" "allow_s3" {
  queue_url = module.sqs.ingestion_queue_url

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowBronzeS3SendMessage"
        Effect    = "Allow"
        Principal = { Service = "s3.amazonaws.com" }
        Action    = "sqs:SendMessage"
        Resource  = module.sqs.ingestion_queue_arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" = module.s3.bucket_arns["bronze"]
          }
        }
      }
    ]
  })
}

resource "time_sleep" "wait_for_sqs_policy" {
  depends_on      = [aws_sqs_queue_policy.allow_s3]
  create_duration = "15s"
}

resource "aws_s3_bucket_notification" "bronze_to_sqs" {
  bucket = module.s3.bronze_bucket_id

  queue {
    queue_arn     = module.sqs.ingestion_queue_arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "raw/"
    filter_suffix = ".json"
  }

  depends_on = [time_sleep.wait_for_sqs_policy]
}
