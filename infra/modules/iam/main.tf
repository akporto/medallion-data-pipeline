# ── Lambda Execution Role ────────────────────────────────────────────────────

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_validator" {
  name               = "${var.project}-${var.environment}-lambda-validator-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

# ── Least-Privilege Policy ────────────────────────────────────────────────────

locals {
  # Scoped to the specific Lambda log group — avoids granting logs:* to all functions
  lambda_log_group_arn = "arn:aws:logs:*:*:log-group:/aws/lambda/${var.project}-${var.environment}-validator:*"
}

data "aws_iam_policy_document" "lambda_validator_policy" {
  statement {
    sid    = "ReadFromIngestionQueue"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
    ]
    resources = [var.ingestion_queue_arn]
  }

  statement {
    sid     = "ReadFromBronzeBucket"
    effect  = "Allow"
    actions = ["s3:GetObject"]
    resources = ["${var.bronze_bucket_arn}/raw/*"]
  }

  statement {
    sid       = "WriteToSilverBucket"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${var.silver_bucket_arn}/validated/*"]
  }

  statement {
    sid    = "IdempotencyTableAccess"
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem",
    ]
    resources = [var.idempotency_table_arn]
  }

  statement {
    sid    = "CloudWatchLogsScoped"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [local.lambda_log_group_arn]
  }

  statement {
    sid    = "AllowXRayTracing"
    effect = "Allow"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
      "xray:GetSamplingRules",
      "xray:GetSamplingTargets",
    ]
    # X-Ray does not support resource-level restrictions per AWS documentation.
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "lambda_validator" {
  name   = "${var.project}-${var.environment}-lambda-validator-policy"
  role   = aws_iam_role.lambda_validator.id
  policy = data.aws_iam_policy_document.lambda_validator_policy.json
}

# ── Glue Service Role ────────────────────────────────────────────────────────

data "aws_iam_policy_document" "glue_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue" {
  name               = "${var.project}-${var.environment}-glue-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

data "aws_iam_policy_document" "glue_s3" {
  statement {
    sid     = "ReadFromBronzeAndSilver"
    effect  = "Allow"
    actions = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      var.bronze_bucket_arn,
      "${var.bronze_bucket_arn}/*",
      var.silver_bucket_arn,
      "${var.silver_bucket_arn}/*",
    ]
  }

  statement {
    sid     = "WriteToSilverAndGold"
    effect  = "Allow"
    actions = ["s3:PutObject", "s3:DeleteObject"]
    resources = [
      "${var.silver_bucket_arn}/*",
      "${var.gold_bucket_arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "glue_s3" {
  name   = "${var.project}-${var.environment}-glue-s3-policy"
  role   = aws_iam_role.glue.id
  policy = data.aws_iam_policy_document.glue_s3.json
}
