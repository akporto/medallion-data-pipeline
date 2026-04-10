"""
Pure validation logic — no AWS SDK calls here.
Responsibility: parse raw JSON and validate against the Pydantic schema.
"""
import json
import logging
from typing import Any

from pydantic import ValidationError

from src.schemas import EcommerceEvent

logger = logging.getLogger(__name__)


class ValidationResult:
    __slots__ = ("event", "errors", "is_valid")

    def __init__(self, event: EcommerceEvent | None, errors: list[dict[str, Any]]):
        self.event = event
        self.errors = errors
        self.is_valid = event is not None


def validate_raw_payload(raw_body: str) -> ValidationResult:
    """
    Deserializes and validates a raw JSON string against EcommerceEvent.
    Returns a ValidationResult regardless of outcome — never raises.
    """
    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        logger.warning("Malformed JSON payload: %s", exc)
        return ValidationResult(event=None, errors=[{"msg": f"Invalid JSON: {exc}"}])

    try:
        event = EcommerceEvent.model_validate(data)
        return ValidationResult(event=event, errors=[])
    except ValidationError as exc:
        logger.warning("Schema validation failed: %s", exc)
        return ValidationResult(event=None, errors=exc.errors())
