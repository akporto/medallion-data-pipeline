"""
Synthetic event generator using Faker.
Produces EcommerceEvent-compliant JSON payloads and uploads them to the Bronze S3 bucket.

Usage (from repo root):
    python -m src.generator.event_generator --count 1000 --bucket my-bronze-bucket

Required: repo root must be in PYTHONPATH (default when running with `python -m`).
"""
import argparse
import json
import logging
import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3
from faker import Faker

from src.schemas import EventType, _VALID_CURRENCIES

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

fake = Faker()

_FINANCIAL_EVENTS = {EventType.PURCHASE, EventType.REFUND}
_SORTED_CURRENCIES = sorted(_VALID_CURRENCIES)


def _random_event_type() -> EventType:
    return fake.random_element(list(EventType))


def generate_event() -> dict[str, Any]:
    event_type = _random_event_type()
    payload: dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type.value,
        "user_id": fake.uuid4(),
        "session_id": fake.uuid4(),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "metadata": {"ip": fake.ipv4(), "user_agent": fake.user_agent()},
    }

    if event_type in _FINANCIAL_EVENTS:
        payload["amount"] = str(
            Decimal(str(fake.pyfloat(min_value=1, max_value=5000, right_digits=2)))
        )
        payload["currency"] = random.choice(_SORTED_CURRENCIES)
        payload["product_id"] = fake.uuid4()

    return payload


def upload_to_s3(bucket: str, key: str, payload: dict[str, Any]) -> None:
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload),
        ContentType="application/json",
    )
    logger.info("Uploaded event %s to s3://%s/%s", payload["event_id"], bucket, key)


def run(count: int, bucket: str) -> None:
    for _ in range(count):
        event = generate_event()
        key = f"raw/{event['event_type']}/{event['event_id']}.json"
        upload_to_s3(bucket, key, event)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic e-commerce event generator")
    parser.add_argument("--count", type=int, default=100, help="Number of events to generate")
    parser.add_argument("--bucket", required=True, help="Target S3 Bronze bucket name")
    args = parser.parse_args()
    run(count=args.count, bucket=args.bucket)
