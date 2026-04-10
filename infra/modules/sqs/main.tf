resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project}-${var.environment}-ingestion-dlq"
  message_retention_seconds = 1209600 # 14 days — maximum retention for forensic inspection
  sqs_managed_sse_enabled   = true

  tags = var.tags
}

resource "aws_sqs_queue" "ingestion" {
  name                       = "${var.project}-${var.environment}-ingestion"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}
