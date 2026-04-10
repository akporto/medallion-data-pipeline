"""
Idempotency guard using DynamoDB.
Responsibility: ensure each event_id is processed exactly once.
This module has zero knowledge of validation logic or AWS SQS.
"""
import logging
import os
import time
from enum import Enum

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

_TABLE_NAME = os.environ["IDEMPOTENCY_TABLE_NAME"]
_TTL_SECONDS = int(os.environ.get("IDEMPOTENCY_TTL_SECONDS", "86400"))

_dynamodb = boto3.resource("dynamodb")


class ProcessingStatus(str, Enum):
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class AlreadyProcessedError(Exception):
    """Raised when an event_id has already been successfully processed."""


def _table():
    return _dynamodb.Table(_TABLE_NAME)


def acquire_lock(event_id: str) -> None:
    """
    Atomically sets event_id status to PROCESSING.
    Raises AlreadyProcessedError if the event was already processed successfully.
    Raises botocore.exceptions.ClientError on conditional check failure (duplicate in-flight).
    """
    expires_at = int(time.time()) + _TTL_SECONDS

    try:
        _table().put_item(
            Item={
                "event_id": event_id,
                "status": ProcessingStatus.PROCESSING,
                "expires_at": expires_at,
            },
            ConditionExpression=(
                "attribute_not_exists(event_id) OR #s = :failed"
            ),
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":failed": ProcessingStatus.FAILED},
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise AlreadyProcessedError(
                f"Event '{event_id}' is already PROCESSING or SUCCEEDED."
            ) from exc
        raise


def mark_succeeded(event_id: str) -> None:
    _table().update_item(
        Key={"event_id": event_id},
        UpdateExpression="SET #s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": ProcessingStatus.SUCCEEDED},
    )


def mark_failed(event_id: str) -> None:
    _table().update_item(
        Key={"event_id": event_id},
        UpdateExpression="SET #s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": ProcessingStatus.FAILED},
    )
