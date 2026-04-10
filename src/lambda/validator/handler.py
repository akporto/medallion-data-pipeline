"""
Lambda entry point — the AWS boundary layer.
Responsibility: translate SQS events into domain calls and back.
No business logic belongs here.
"""
import logging
import os
from typing import Any

import boto3

from .idempotency import AlreadyProcessedError, acquire_lock, mark_failed, mark_succeeded
from .validator import validate_raw_payload

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

_SILVER_BUCKET = os.environ["SILVER_BUCKET_NAME"]

_s3 = boto3.client("s3")


def _move_to_silver(event_id: str, event_type: str, json_body: str) -> None:
    key = f"validated/{event_type}/{event_id}.json"
    _s3.put_object(
        Bucket=_SILVER_BUCKET,
        Key=key,
        Body=json_body,
        ContentType="application/json",
    )
    logger.info("Event %s written to Silver at s3://%s/%s", event_id, _SILVER_BUCKET, key)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Processes SQS batch records. Partial batch failure is supported via
    'ReportBatchItemFailures' — failed items are returned for SQS retry/DLQ routing.
    """
    batch_item_failures: list[dict[str, str]] = []

    for record in event.get("Records", []):
        message_id = record["messageId"]
        body = record["body"]

        result = validate_raw_payload(body)

        if not result.is_valid:
            logger.error(
                "Validation failed for messageId=%s errors=%s", message_id, result.errors
            )
            batch_item_failures.append({"itemIdentifier": message_id})
            continue

        event_id = str(result.event.event_id)

        try:
            acquire_lock(event_id)
        except AlreadyProcessedError:
            logger.info("Skipping duplicate event_id=%s", event_id)
            continue

        try:
            json_string = result.event.model_dump_json()
            _move_to_silver(event_id, result.event.event_type.value, json_string)
            mark_succeeded(event_id)
        except Exception as exc:
            logger.exception("Failed to process event_id=%s: %s", event_id, exc)
            mark_failed(event_id)
            batch_item_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_item_failures}
