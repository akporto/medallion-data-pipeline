"""
Shared helpers for integration tests.

Import boto3_kwargs from here, not from conftest.py.
Importing directly from conftest is an anti-pattern that can cause circular
imports during pytest collection and tightly couples test files to the fixture
infrastructure.
"""
import os

_USE_LOCALSTACK = os.environ.get("USE_LOCALSTACK", "").lower() in ("1", "true", "yes")
_ENDPOINT = "http://localhost:4566" if _USE_LOCALSTACK else None
_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def boto3_kwargs() -> dict:
    """Return keyword arguments for boto3 client/resource constructors.

    Routes to LocalStack when USE_LOCALSTACK=1, otherwise targets real AWS.
    """
    kwargs: dict = {"region_name": _REGION}
    if _ENDPOINT:
        kwargs["endpoint_url"] = _ENDPOINT
    return kwargs
