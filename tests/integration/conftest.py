"""
Integration test fixtures.
Tests run against real AWS services (us-east-1) or LocalStack.

Set USE_LOCALSTACK=1 to route all calls to http://localhost:4566.
Credentials for LocalStack can be any non-empty string (e.g. via ~/.aws/credentials dummy profile).
"""
import uuid

import boto3
import pytest

from tests.integration.helpers import _REGION, _USE_LOCALSTACK, boto3_kwargs as _boto3_kwargs


@pytest.fixture(scope="function")
def dynamo_table(monkeypatch):
    """
    Creates an isolated DynamoDB table for each test function.
    Patches the idempotency module's _TABLE_NAME and _dynamodb to point to it.
    Tears down (deletes) the table after the test.
    """
    import validator.idempotency as idempotency_module

    dynamodb = boto3.resource("dynamodb", **_boto3_kwargs())
    table_name = f"test-idempotency-{uuid.uuid4().hex[:8]}"

    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "event_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()

    monkeypatch.setenv("IDEMPOTENCY_TABLE_NAME", table_name)
    monkeypatch.setenv("IDEMPOTENCY_TTL_SECONDS", "3600")
    monkeypatch.setattr(idempotency_module, "_TABLE_NAME", table_name)
    monkeypatch.setattr(idempotency_module, "_dynamodb", dynamodb)

    yield table_name

    table.delete()


@pytest.fixture(scope="function")
def silver_bucket(monkeypatch):
    """
    Creates an isolated S3 bucket for each test function.
    Patches handler._SILVER_BUCKET and handler._s3 to point to it.
    Tears down (empties and deletes) the bucket after the test.
    """
    import validator.handler as handler_module

    s3 = boto3.client("s3", **_boto3_kwargs())
    bucket_name = f"test-silver-{uuid.uuid4().hex[:8]}"

    if _USE_LOCALSTACK or _REGION == "us-east-1":
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": _REGION},
        )

    monkeypatch.setenv("SILVER_BUCKET_NAME", bucket_name)
    monkeypatch.setattr(handler_module, "_SILVER_BUCKET", bucket_name)
    monkeypatch.setattr(handler_module, "_s3", s3)

    yield bucket_name, s3

    response = s3.list_objects_v2(Bucket=bucket_name)
    for obj in response.get("Contents", []):
        s3.delete_object(Bucket=bucket_name, Key=obj["Key"])
    s3.delete_bucket(Bucket=bucket_name)


@pytest.fixture(scope="function")
def bronze_bucket(silver_bucket):
    """
    Creates an isolated Bronze S3 bucket for each test function.
    Reuses the same S3 client from silver_bucket since handler._s3 is already patched.
    Tears down (empties and deletes) the bucket after the test.
    """
    _, s3 = silver_bucket
    bucket_name = f"test-bronze-{uuid.uuid4().hex[:8]}"

    if _USE_LOCALSTACK or _REGION == "us-east-1":
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": _REGION},
        )

    yield bucket_name, s3

    response = s3.list_objects_v2(Bucket=bucket_name)
    for obj in response.get("Contents", []):
        s3.delete_object(Bucket=bucket_name, Key=obj["Key"])
    s3.delete_bucket(Bucket=bucket_name)
