"""
Pydantic schema definitions for e-commerce/fintech events.
This module is the single source of truth (Schema Registry) consumed by
the Lambda validator and Glue jobs alike.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class EventType(str, Enum):
    PURCHASE = "purchase"
    REFUND = "refund"
    PAGE_VIEW = "page_view"
    ADD_TO_CART = "add_to_cart"


_VALID_CURRENCIES: frozenset[str] = frozenset(
    {"USD", "EUR", "BRL", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "MXN"}
)


class EcommerceEvent(BaseModel):
    event_id: UUID
    event_type: EventType
    user_id: str = Field(..., min_length=1, max_length=128)
    session_id: str = Field(..., min_length=1, max_length=128)
    product_id: Optional[str] = Field(default=None, max_length=128)
    amount: Optional[Decimal] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def amount_required_for_financial_events(self) -> "EcommerceEvent":
        financial_events = {EventType.PURCHASE, EventType.REFUND}
        if self.event_type in financial_events and self.amount is None:
            raise ValueError(
                f"'amount' is required for event_type='{self.event_type.value}'"
            )
        return self

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in _VALID_CURRENCIES:
            raise ValueError(
                f"Unsupported currency code: '{value}'. "
                f"Allowed: {sorted(_VALID_CURRENCIES)}"
            )
        return value
