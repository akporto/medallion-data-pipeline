"""
Root conftest: sets up sys.path so both "src.*" and "validator.*" modules resolve.

Why the sys.path manipulation for "src/lambda":
  Python treats "lambda" as a reserved keyword, making
  `from src.lambda.validator import ...` a SyntaxError at parse time.
  Adding "src/lambda" directly to sys.path lets tests import the Lambda
  handler modules as `validator.*` — consistent with how the Lambda runtime
  itself loads them (as a flat package, not via the src.lambda path).
"""
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_LAMBDA_SRC = os.path.join(_REPO_ROOT, "src", "lambda")

if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

if _LAMBDA_SRC not in sys.path:
    sys.path.insert(0, _LAMBDA_SRC)
