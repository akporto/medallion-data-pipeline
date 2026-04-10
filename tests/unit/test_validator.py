"""
Unit tests for validator.py.
Pure Python — no mocks, no AWS calls required.
"""
import json
import uuid
from datetime import datetime, timezone

import pytest

from validator.validator import ValidationResult, validate_raw_payload


def _purchase_payload(**overrides) -> str:
    data = {
        "event_id": str(uuid.uuid4()),
        "event_type": "purchase",
        "user_id": "user-abc",
        "session_id": "session-xyz",
        "product_id": "prod-001",
        "amount": "149.99",
        "currency": "USD",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
    data.update(overrides)
    return json.dumps(data)


def _page_view_payload(**overrides) -> str:
    data = {
        "event_id": str(uuid.uuid4()),
        "event_type": "page_view",
        "user_id": "user-abc",
        "session_id": "session-xyz",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
    data.update(overrides)
    return json.dumps(data)


class TestValidateRawPayload:
    def test_valid_purchase_event(self):
        result = validate_raw_payload(_purchase_payload())

        assert result.is_valid is True
        assert result.errors == []
        assert result.event is not None
        assert result.event.event_type.value == "purchase"
        assert result.event.currency == "USD"

    def test_valid_page_view_event_has_no_amount_or_currency(self):
        result = validate_raw_payload(_page_view_payload())

        assert result.is_valid is True
        assert result.event.amount is None
        assert result.event.currency is None
        assert result.event.product_id is None

    def test_malformed_json_returns_invalid_result(self):
        result = validate_raw_payload("{not: valid, json}")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Invalid JSON" in result.errors[0]["msg"]

    def test_missing_event_id_returns_invalid_result(self):
        payload = _page_view_payload()
        data = json.loads(payload)
        del data["event_id"]

        result = validate_raw_payload(json.dumps(data))

        assert result.is_valid is False
        assert any(e["loc"][0] == "event_id" for e in result.errors)

    def test_purchase_without_amount_fails(self):
        payload = _purchase_payload()
        data = json.loads(payload)
        del data["amount"]

        result = validate_raw_payload(json.dumps(data))

        assert result.is_valid is False
        assert any("amount" in str(e).lower() for e in result.errors)

    def test_lowercase_currency_fails_pattern_check(self):
        result = validate_raw_payload(_purchase_payload(currency="usd"))

        assert result.is_valid is False

    def test_unsupported_uppercase_currency_fails_semantic_check(self):
        result = validate_raw_payload(_purchase_payload(currency="XYZ"))

        assert result.is_valid is False
        assert any("Unsupported currency" in str(e) for e in result.errors)

    def test_validation_result_never_raises(self):
        result = validate_raw_payload("null")
        assert result.is_valid is False

    def test_empty_string_body_returns_invalid_result(self):
        result = validate_raw_payload("")
        assert result.is_valid is False


class TestValidationResultSlots:
    def test_slots_are_exactly_defined(self):
        assert ValidationResult.__slots__ == ("event", "errors", "is_valid")

    def test_valid_result_has_correct_attribute_values(self):
        import json
        payload = _purchase_payload()
        result = validate_raw_payload(payload)

        assert result.is_valid is True
        assert result.event is not None
        assert result.errors == []

    def test_invalid_result_has_correct_attribute_values(self):
        result = validate_raw_payload("{}")

        assert result.is_valid is False
        assert result.event is None
        assert len(result.errors) > 0
