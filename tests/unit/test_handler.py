"""
Unit tests for handler.py (Lambda entry point).
All external dependencies are mocked: S3, idempotency functions, and validate_raw_payload.
Tests verify the handler's routing logic and SQS partial-batch failure semantics.
"""
import json
import uuid
from unittest.mock import MagicMock, patch

import pytest

import validator.handler as handler_module
from validator.handler import lambda_handler
from validator.idempotency import AlreadyProcessedError
from validator.validator import ValidationResult


def _s3_notification_body(bucket: str = "test-bronze", key: str = "raw/test/event.json") -> str:
    return json.dumps({
        "Records": [{
            "s3": {
                "bucket": {"name": bucket},
                "object": {"key": key},
            }
        }]
    })


def _sqs_event(*records) -> dict:
    return {"Records": list(records)}


def _sqs_record(body: str, message_id: str = "msg-001") -> dict:
    return {
        "messageId": message_id,
        "body": body,
        "receiptHandle": f"receipt-{message_id}",
        "attributes": {},
    }


def _valid_result(event_id: str | None = None, event_type: str = "purchase") -> MagicMock:
    """Builds a ValidationResult mock that looks like a successfully parsed event."""
    result = MagicMock(spec=ValidationResult)
    result.is_valid = True
    result.event.event_id = uuid.UUID(event_id) if event_id else uuid.uuid4()
    result.event.event_type.value = event_type
    result.event.model_dump_json.return_value = '{"event_id": "test", "event_type": "purchase"}'
    return result


def _invalid_result() -> MagicMock:
    result = MagicMock(spec=ValidationResult)
    result.is_valid = False
    result.errors = [{"msg": "field required", "loc": ["event_id"]}]
    return result


@pytest.fixture
def mock_s3():
    with patch.object(handler_module, "_s3") as mock:
        body_mock = MagicMock()
        body_mock.read.return_value = b'{"raw": "content"}'
        mock.get_object.return_value = {"Body": body_mock}
        yield mock


@pytest.fixture
def mock_validate():
    with patch("validator.handler.validate_raw_payload") as mock:
        yield mock


@pytest.fixture
def mock_acquire_lock():
    with patch("validator.handler.acquire_lock") as mock:
        yield mock


@pytest.fixture
def mock_mark_succeeded():
    with patch("validator.handler.mark_succeeded") as mock:
        yield mock


@pytest.fixture
def mock_mark_failed():
    with patch("validator.handler.mark_failed") as mock:
        yield mock


class TestLambdaHandlerSuccessPath:
    def test_valid_record_produces_empty_batch_item_failures(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.return_value = _valid_result()
        event = _sqs_event(_sqs_record(_s3_notification_body(), "msg-v1"))

        result = lambda_handler(event, None)

        assert result["batchItemFailures"] == []

    def test_valid_record_writes_to_s3(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.return_value = _valid_result()
        event = _sqs_event(_sqs_record(_s3_notification_body()))

        lambda_handler(event, None)

        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == handler_module._SILVER_BUCKET
        assert call_kwargs["ContentType"] == "application/json"

    def test_valid_record_calls_mark_succeeded(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.return_value = _valid_result()
        lambda_handler(_sqs_event(_sqs_record(_s3_notification_body())), None)

        mock_mark_succeeded.assert_called_once()
        mock_mark_failed.assert_not_called()


class TestLambdaHandlerInvalidPayload:
    def test_invalid_payload_adds_to_batch_item_failures(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.return_value = _invalid_result()
        event = _sqs_event(_sqs_record(_s3_notification_body(), "msg-invalid"))

        result = lambda_handler(event, None)

        assert result["batchItemFailures"] == [{"itemIdentifier": "msg-invalid"}]

    def test_invalid_payload_does_not_touch_s3_or_idempotency(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.return_value = _invalid_result()
        lambda_handler(_sqs_event(_sqs_record(_s3_notification_body())), None)

        mock_s3.put_object.assert_not_called()
        mock_acquire_lock.assert_not_called()
        mock_mark_succeeded.assert_not_called()
        mock_mark_failed.assert_not_called()


class TestLambdaHandlerMalformedSqsBody:
    def test_malformed_json_body_adds_to_batch_item_failures(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        event = _sqs_event(_sqs_record("not-valid-json", "msg-bad"))

        result = lambda_handler(event, None)

        assert result["batchItemFailures"] == [{"itemIdentifier": "msg-bad"}]
        mock_validate.assert_not_called()


class TestLambdaHandlerDuplicateEvent:
    def test_duplicate_event_is_skipped_silently(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.return_value = _valid_result()
        mock_acquire_lock.side_effect = AlreadyProcessedError("already done")
        event = _sqs_event(_sqs_record(_s3_notification_body(), "msg-dup"))

        result = lambda_handler(event, None)

        assert result["batchItemFailures"] == []

    def test_duplicate_event_does_not_write_to_s3(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.return_value = _valid_result()
        mock_acquire_lock.side_effect = AlreadyProcessedError("already done")
        lambda_handler(_sqs_event(_sqs_record(_s3_notification_body())), None)

        mock_s3.put_object.assert_not_called()
        mock_mark_failed.assert_not_called()


class TestLambdaHandlerS3Failure:
    def test_s3_read_failure_adds_to_batch_item_failures(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_s3.get_object.side_effect = RuntimeError("S3 read unavailable")
        event = _sqs_event(_sqs_record(_s3_notification_body(), "msg-s3-read-fail"))

        result = lambda_handler(event, None)

        assert result["batchItemFailures"] == [{"itemIdentifier": "msg-s3-read-fail"}]

    def test_s3_failure_adds_to_batch_item_failures(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.return_value = _valid_result()
        mock_s3.put_object.side_effect = RuntimeError("S3 unavailable")
        event = _sqs_event(_sqs_record(_s3_notification_body(), "msg-s3-fail"))

        result = lambda_handler(event, None)

        assert result["batchItemFailures"] == [{"itemIdentifier": "msg-s3-fail"}]

    def test_s3_failure_calls_mark_failed(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.return_value = _valid_result()
        mock_s3.put_object.side_effect = RuntimeError("S3 unavailable")
        lambda_handler(_sqs_event(_sqs_record(_s3_notification_body())), None)

        mock_mark_failed.assert_called_once()
        mock_mark_succeeded.assert_not_called()


class TestLambdaHandlerMixedBatch:
    def test_mixed_batch_only_invalid_records_in_failures(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        mock_validate.side_effect = [
            _valid_result(),
            _invalid_result(),
            _valid_result(),
            _invalid_result(),
            _valid_result(),
        ]
        records = [
            _sqs_record(_s3_notification_body(), "msg-v1"),
            _sqs_record(_s3_notification_body(), "msg-i1"),
            _sqs_record(_s3_notification_body(), "msg-v2"),
            _sqs_record(_s3_notification_body(), "msg-i2"),
            _sqs_record(_s3_notification_body(), "msg-v3"),
        ]
        event = _sqs_event(*records)

        result = lambda_handler(event, None)

        failure_ids = {f["itemIdentifier"] for f in result["batchItemFailures"]}
        assert failure_ids == {"msg-i1", "msg-i2"}
        assert mock_s3.put_object.call_count == 3
        assert mock_mark_succeeded.call_count == 3
        mock_mark_failed.assert_not_called()

    def test_empty_records_list_returns_empty_failures(
        self, mock_s3, mock_validate, mock_acquire_lock, mock_mark_succeeded, mock_mark_failed
    ):
        result = lambda_handler({"Records": []}, None)

        assert result == {"batchItemFailures": []}
        mock_validate.assert_not_called()
