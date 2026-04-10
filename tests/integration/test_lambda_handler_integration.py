"""
Integration tests for handler.py (Lambda entry point) against real AWS services.
Exercises the full path: SQS record → Pydantic validation → DynamoDB idempotency → S3 write.

Run with: pytest -m integration
"""
import json
import uuid
from datetime import datetime, timezone

import pytest

from validator.handler import lambda_handler

pytestmark = pytest.mark.integration


def _sqs_event(*records) -> dict:
    return {"Records": list(records)}


def _sqs_record(body: str, message_id: str | None = None) -> dict:
    return {
        "messageId": message_id or str(uuid.uuid4()),
        "body": body,
        "receiptHandle": "test-receipt",
        "attributes": {},
    }


def _valid_purchase_body(event_id: str | None = None) -> str:
    return json.dumps({
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": "purchase",
        "user_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "product_id": str(uuid.uuid4()),
        "amount": "99.99",
        "currency": "USD",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    })


class TestHandlerIntegration:
    def test_valid_record_written_to_silver_s3(self, dynamo_table, silver_bucket):
        bucket_name, s3_client = silver_bucket
        event_id = str(uuid.uuid4())
        body = _valid_purchase_body(event_id)
        msg_id = str(uuid.uuid4())

        result = lambda_handler(_sqs_event(_sqs_record(body, msg_id)), None)

        assert result["batchItemFailures"] == []
        expected_key = f"validated/purchase/{event_id}.json"
        response = s3_client.get_object(Bucket=bucket_name, Key=expected_key)
        stored = json.loads(response["Body"].read())
        assert stored["event_id"] == event_id

    def test_same_record_twice_is_idempotent(self, dynamo_table, silver_bucket):
        bucket_name, s3_client = silver_bucket
        event_id = str(uuid.uuid4())
        body = _valid_purchase_body(event_id)
        record = _sqs_record(body, str(uuid.uuid4()))

        result1 = lambda_handler(_sqs_event(record), None)
        result2 = lambda_handler(_sqs_event(record), None)

        assert result1["batchItemFailures"] == []
        assert result2["batchItemFailures"] == [], "Duplicate must be silently skipped"

        prefix = f"validated/purchase/{event_id}"
        objects = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        assert objects.get("KeyCount", 0) == 1, "Exactly one S3 object expected"

    def test_invalid_json_body_goes_to_batch_item_failures(
        self, dynamo_table, silver_bucket
    ):
        bucket_name, s3_client = silver_bucket
        msg_id = str(uuid.uuid4())

        result = lambda_handler(_sqs_event(_sqs_record("{not json}", msg_id)), None)

        assert result["batchItemFailures"] == [{"itemIdentifier": msg_id}]
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        assert objects.get("KeyCount", 0) == 0, "Nothing should be written to S3"

    def test_mixed_batch_three_valid_two_invalid(self, dynamo_table, silver_bucket):
        bucket_name, s3_client = silver_bucket

        valid_ids = [str(uuid.uuid4()) for _ in range(3)]
        invalid_msg_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

        records = [
            _sqs_record(_valid_purchase_body(valid_ids[0]), str(uuid.uuid4())),
            _sqs_record("{bad json}", invalid_msg_ids[0]),
            _sqs_record(_valid_purchase_body(valid_ids[1]), str(uuid.uuid4())),
            _sqs_record("{also bad}", invalid_msg_ids[1]),
            _sqs_record(_valid_purchase_body(valid_ids[2]), str(uuid.uuid4())),
        ]

        result = lambda_handler(_sqs_event(*records), None)

        failure_ids = {f["itemIdentifier"] for f in result["batchItemFailures"]}
        assert failure_ids == set(invalid_msg_ids)

        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        assert objects.get("KeyCount", 0) == 3, "Only 3 valid events should be in S3"
