"""
Root conftest: sets up sys.path so both "src.*" and "validator.*" modules resolve.

Why the sys.path manipulation for "src/lambda":
  Python treats "lambda" as a reserved keyword, making
  `from src.lambda.validator import ...` a SyntaxError at parse time.
  Adding "src/lambda" directly to sys.path lets tests import the Lambda
  handler modules as `validator.*` — consistent with how the Lambda runtime
  itself loads them (as a flat package, not via the src.lambda path).

Why env vars are set here (root) and not only in tests/unit/conftest.py:
  idempotency.py and handler.py read env vars at module level. pytest collects
  ALL test files (including integration) before applying -m markers, so the
  imports happen during collection — before any fixture or unit conftest runs.
  Setting defaults here ensures collection never raises KeyError regardless of
  which subset of tests is being run.
"""
import os
import sys

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("IDEMPOTENCY_TABLE_NAME", "test-idempotency-table")
os.environ.setdefault("IDEMPOTENCY_TTL_SECONDS", "3600")
os.environ.setdefault("SILVER_BUCKET_NAME", "test-silver-bucket")
os.environ.setdefault("LOG_LEVEL", "ERROR")

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_LAMBDA_SRC = os.path.join(_REPO_ROOT, "src", "lambda")

if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

if _LAMBDA_SRC not in sys.path:
    sys.path.insert(0, _LAMBDA_SRC)
