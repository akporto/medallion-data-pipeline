"""
Unit test conftest: sets required environment variables before any module
that reads them at import time (idempotency._TABLE_NAME, handler._SILVER_BUCKET,
idempotency._dynamodb boto3.resource which requires a region).
Must run before test collection imports those modules.
"""
import os

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

os.environ.setdefault("IDEMPOTENCY_TABLE_NAME", "unit-test-idempotency-table")
os.environ.setdefault("IDEMPOTENCY_TTL_SECONDS", "3600")
os.environ.setdefault("SILVER_BUCKET_NAME", "unit-test-silver-bucket")
os.environ.setdefault("LOG_LEVEL", "ERROR")
