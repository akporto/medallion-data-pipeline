"""
Lambda entry point — the AWS boundary layer.
Responsibility: translate SQS→S3 notifications into domain calls and back.
No business logic belongs here.

Flow: S3 ObjectCreated → SQS notification → this handler → validate → Silver
The SQS message body is an S3 event notification JSON, not the raw event payload.
The handler downloads the actual event file from S3 Bronze before validating.
"""
import json
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


def _read_from_bronze(bucket: str, key: str) -> str:
    response = _s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read().decode("utf-8")


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
    Processes SQS batch records triggered by S3 ObjectCreated notifications.
    Each SQS message body contains an S3 event notification; the handler reads
    the actual event file from S3 Bronze, validates it, and writes valid records
    to Silver. Partial batch failure is supported via 'ReportBatchItemFailures'.
    """
    batch_item_failures: list[dict[str, str]] = []

    for sqs_record in event.get("Records", []):
        message_id = sqs_record["messageId"]

        try:
            notification = json.loads(sqs_record["body"])
        except json.JSONDecodeError as exc:
            logger.error("Malformed SQS body for messageId=%s: %s", message_id, exc)
            batch_item_failures.append({"itemIdentifier": message_id})
            continue

        s3_records = notification.get("Records", [])
        failed = False

        for s3_record in s3_records:
            bucket = s3_record["s3"]["bucket"]["name"]
            key = s3_record["s3"]["object"]["key"]

            try:
                raw_body = _read_from_bronze(bucket, key)
            except Exception as exc:
                logger.error("Failed to read s3://%s/%s: %s", bucket, key, exc)
                failed = True
                break

            result = validate_raw_payload(raw_body)

            if not result.is_valid:
                logger.error(
                    "Validation failed for s3://%s/%s errors=%s", bucket, key, result.errors
                )
                failed = True
                break

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
                failed = True
                break

        if failed:
            batch_item_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_item_failures}
