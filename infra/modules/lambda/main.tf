locals {
  function_name = "${var.project}-${var.environment}-validator"
  log_group_arn = "arn:aws:logs:*:*:log-group:/aws/lambda/${local.function_name}:*"
}

# Pre-create the log group so Terraform controls the retention policy.
# Without this, Lambda auto-creates the group with no expiry, incurring
# unbounded CloudWatch storage costs.
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_lambda_function" "validator" {
  function_name = local.function_name
  description   = "Validates Bronze events via Pydantic and writes valid records to Silver S3."
  role          = var.execution_role_arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = var.timeout
  memory_size   = var.memory_size

  filename         = var.artifact_path
  source_code_hash = filebase64sha256(var.artifact_path)

  environment {
    variables = {
      SILVER_BUCKET_NAME      = var.silver_bucket_name
      IDEMPOTENCY_TABLE_NAME  = var.idempotency_table_name
      IDEMPOTENCY_TTL_SECONDS = tostring(var.idempotency_ttl_seconds)
      LOG_LEVEL               = var.log_level
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags

  # Ensures the log group (with retention) is created before the function.
  # Prevents Lambda from auto-creating the group without a retention policy.
  depends_on = [aws_cloudwatch_log_group.lambda]
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn                   = var.ingestion_queue_arn
  function_name                      = aws_lambda_function.validator.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 20
  function_response_types            = ["ReportBatchItemFailures"]
}
