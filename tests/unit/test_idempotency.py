"""
Unit tests for idempotency.py.
All DynamoDB calls are mocked via the module-level _dynamodb resource.
"""
from unittest.mock import MagicMock, call, patch

import pytest
from botocore.exceptions import ClientError

import validator.idempotency as idempotency_module
from validator.idempotency import (
    AlreadyProcessedError,
    ProcessingStatus,
    acquire_lock,
    mark_failed,
    mark_succeeded,
)


def _client_error(code: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": f"Simulated {code}"}},
        "put_item",
    )


@pytest.fixture
def mock_table():
    """Patches the module-level _dynamodb resource; yields the mocked Table."""
    with patch.object(idempotency_module, "_dynamodb") as mock_dynamo:
        table = MagicMock()
        mock_dynamo.Table.return_value = table
        yield table


class TestAcquireLock:
    def test_succeeds_on_first_call(self, mock_table):
        acquire_lock("event-new-001")

        mock_table.put_item.assert_called_once()
        kwargs = mock_table.put_item.call_args.kwargs
        assert kwargs["Item"]["event_id"] == "event-new-001"
        assert kwargs["Item"]["status"] == ProcessingStatus.PROCESSING
        assert "expires_at" in kwargs["Item"]

    def test_expires_at_is_set_to_future_timestamp(self, mock_table):
        import time

        before = int(time.time())
        acquire_lock("event-ttl-001")
        after = int(time.time())

        kwargs = mock_table.put_item.call_args.kwargs
        expires_at = kwargs["Item"]["expires_at"]
        assert expires_at > before
        assert expires_at <= after + idempotency_module._TTL_SECONDS

    def test_raises_already_processed_on_conditional_check_failed(self, mock_table):
        mock_table.put_item.side_effect = _client_error("ConditionalCheckFailedException")

        with pytest.raises(AlreadyProcessedError) as exc_info:
            acquire_lock("event-dup-001")

        assert "event-dup-001" in str(exc_info.value)

    def test_reraises_other_client_errors(self, mock_table):
        mock_table.put_item.side_effect = _client_error(
            "ProvisionedThroughputExceededException"
        )

        with pytest.raises(ClientError) as exc_info:
            acquire_lock("event-throttled-001")

        assert (
            exc_info.value.response["Error"]["Code"]
            == "ProvisionedThroughputExceededException"
        )

    def test_failed_event_can_be_reacquired(self, mock_table):
        mock_table.put_item.return_value = {}

        acquire_lock("event-retry-001")

        mock_table.put_item.assert_called_once()
        kwargs = mock_table.put_item.call_args.kwargs
        assert kwargs["Item"]["status"] == ProcessingStatus.PROCESSING
        assert ":failed" in kwargs["ExpressionAttributeValues"]
        assert kwargs["ExpressionAttributeValues"][":failed"] == ProcessingStatus.FAILED


class TestMarkStatus:
    def test_mark_succeeded_calls_update_with_succeeded_status(self, mock_table):
        mark_succeeded("event-ok-001")

        mock_table.update_item.assert_called_once()
        kwargs = mock_table.update_item.call_args.kwargs
        assert kwargs["Key"] == {"event_id": "event-ok-001"}
        assert kwargs["ExpressionAttributeValues"][":status"] == ProcessingStatus.SUCCEEDED

    def test_mark_failed_calls_update_with_failed_status(self, mock_table):
        mark_failed("event-err-001")

        mock_table.update_item.assert_called_once()
        kwargs = mock_table.update_item.call_args.kwargs
        assert kwargs["Key"] == {"event_id": "event-err-001"}
        assert kwargs["ExpressionAttributeValues"][":status"] == ProcessingStatus.FAILED

    def test_mark_succeeded_uses_correct_event_id(self, mock_table):
        mark_succeeded("specific-event-id")

        kwargs = mock_table.update_item.call_args.kwargs
        assert kwargs["Key"]["event_id"] == "specific-event-id"

    def test_mark_failed_uses_correct_event_id(self, mock_table):
        mark_failed("specific-event-id")

        kwargs = mock_table.update_item.call_args.kwargs
        assert kwargs["Key"]["event_id"] == "specific-event-id"
