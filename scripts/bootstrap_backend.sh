#!/usr/bin/env bash
# Bootstrap the Terraform remote state backend for a given environment.
# Must be run ONCE before the first `terraform init` in any environment.
#
# Usage: ./scripts/bootstrap_backend.sh [dev|prod]
#
# Creates:
#   - S3 bucket:       <project>-<env>-terraform-state  (versioned + encrypted)
#   - DynamoDB table:  <project>-<env>-tf-lock           (for state locking)
set -euo pipefail

ENVIRONMENT="${1:-dev}"
PROJECT="medallion-aknp"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
BUCKET_NAME="${PROJECT}-${ENVIRONMENT}-terraform-state"
TABLE_NAME="${PROJECT}-${ENVIRONMENT}-tf-lock"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "==> Bootstrapping Terraform backend"
echo "    Environment : $ENVIRONMENT"
echo "    Account     : $ACCOUNT_ID"
echo "    Region      : $REGION"
echo "    Bucket      : $BUCKET_NAME"
echo "    Lock table  : $TABLE_NAME"
echo ""

# ── S3 State Bucket ──────────────────────────────────────────────────────────

echo "==> Checking if S3 bucket exists..."
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
  echo "    Bucket already exists, skipping creation."
else
  echo "==> Creating S3 bucket..."
  if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket \
      --bucket "$BUCKET_NAME" \
      --region "$REGION"
  else
    aws s3api create-bucket \
      --bucket "$BUCKET_NAME" \
      --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION"
  fi
  echo "    Created."
fi

echo "==> Enabling versioning..."
aws s3api put-bucket-versioning \
  --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

echo "==> Enabling server-side encryption (AES256)..."
aws s3api put-bucket-encryption \
  --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"},
      "BucketKeyEnabled": true
    }]
  }'

echo "==> Blocking all public access..."
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# ── DynamoDB Lock Table ───────────────────────────────────────────────────────

echo "==> Checking if DynamoDB lock table exists..."
if aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" 2>/dev/null; then
  echo "    Table already exists, skipping creation."
else
  echo "==> Creating DynamoDB lock table..."
  aws dynamodb create-table \
    --table-name "$TABLE_NAME" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$REGION"
  echo "    Created."
fi

echo ""
echo "==> Bootstrap complete."
echo "    Next step: cd infra/environments/$ENVIRONMENT && terraform init"
