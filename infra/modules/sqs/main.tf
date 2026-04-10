resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project}-${var.environment}-ingestion-dlq"
  message_retention_seconds = 1209600 # 14 days — maximum retention for forensic inspection
  kms_master_key_id         = "alias/aws/sqs"

  tags = var.tags
}

resource "aws_sqs_queue" "ingestion" {
  name                       = "${var.project}-${var.environment}-ingestion"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds
  kms_master_key_id          = "alias/aws/sqs"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}
