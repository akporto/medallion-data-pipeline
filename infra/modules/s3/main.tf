resource "aws_s3_bucket" "medallion" {
  for_each = toset(var.layers)

  bucket        = "${var.project}-${var.environment}-${each.key}"
  force_destroy = var.force_destroy

  tags = merge(var.tags, { Layer = each.key })
}

resource "aws_s3_bucket_versioning" "medallion" {
  for_each = aws_s3_bucket.medallion

  bucket = each.value.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "medallion" {
  for_each = aws_s3_bucket.medallion

  bucket = each.value.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "medallion" {
  for_each = aws_s3_bucket.medallion

  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle: transition Bronze raw/ objects to STANDARD_IA to reduce storage cost
resource "aws_s3_bucket_lifecycle_configuration" "bronze_lifecycle" {
  bucket = aws_s3_bucket.medallion["bronze"].id

  rule {
    id     = "bronze-raw-to-standard-ia"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days          = var.bronze_lifecycle_days
      storage_class = "STANDARD_IA"
    }
  }

  depends_on = [aws_s3_bucket_versioning.medallion]
}
