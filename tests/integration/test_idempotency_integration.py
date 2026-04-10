"""
Integration tests for idempotency.py against a real DynamoDB table.
Validates the atomic conditional-write semantics end-to-end.

Run with: pytest -m integration
"""
import time
import uuid

import pytest

from validator.idempotency import (
    AlreadyProcessedError,
    ProcessingStatus,
    acquire_lock,
    mark_failed,
    mark_succeeded,
)

pytestmark = pytest.mark.integration


class TestAcquireLockIntegration:
    def test_first_acquire_succeeds(self, dynamo_table):
        event_id = str(uuid.uuid4())
        acquire_lock(event_id)

    def test_second_acquire_raises_already_processed(self, dynamo_table):
        event_id = str(uuid.uuid4())
        acquire_lock(event_id)

        with pytest.raises(AlreadyProcessedError):
            acquire_lock(event_id)

    def test_failed_event_can_be_reacquired(self, dynamo_table):
        event_id = str(uuid.uuid4())
        acquire_lock(event_id)
        mark_failed(event_id)

        acquire_lock(event_id)

    def test_succeeded_event_cannot_be_reacquired(self, dynamo_table):
        event_id = str(uuid.uuid4())
        acquire_lock(event_id)
        mark_succeeded(event_id)

        with pytest.raises(AlreadyProcessedError):
            acquire_lock(event_id)

    def test_ttl_field_is_set_to_future_timestamp(self, dynamo_table):
        import boto3
        from tests.integration.helpers import boto3_kwargs as _boto3_kwargs

        event_id = str(uuid.uuid4())
        before = int(time.time())
        acquire_lock(event_id)
        after = int(time.time())

        dynamodb = boto3.resource("dynamodb", **_boto3_kwargs())
        item = dynamodb.Table(dynamo_table).get_item(Key={"event_id": event_id})["Item"]

        expires_at = int(item["expires_at"])
        assert expires_at > after, "expires_at must be in the future"
        assert expires_at <= after + 3600 + 5, "expires_at must respect TTL_SECONDS"

    def test_item_has_processing_status_after_acquire(self, dynamo_table):
        import boto3
        from tests.integration.helpers import boto3_kwargs as _boto3_kwargs

        event_id = str(uuid.uuid4())
        acquire_lock(event_id)

        dynamodb = boto3.resource("dynamodb", **_boto3_kwargs())
        item = dynamodb.Table(dynamo_table).get_item(Key={"event_id": event_id})["Item"]

        assert item["status"] == ProcessingStatus.PROCESSING

    def test_item_has_succeeded_status_after_mark_succeeded(self, dynamo_table):
        import boto3
        from tests.integration.helpers import boto3_kwargs as _boto3_kwargs

        event_id = str(uuid.uuid4())
        acquire_lock(event_id)
        mark_succeeded(event_id)

        dynamodb = boto3.resource("dynamodb", **_boto3_kwargs())
        item = dynamodb.Table(dynamo_table).get_item(Key={"event_id": event_id})["Item"]

        assert item["status"] == ProcessingStatus.SUCCEEDED
