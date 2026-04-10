#!/usr/bin/env bash
# Build the Lambda deployment package for the validator function.
#
# Usage: ./scripts/build_lambda.sh
#
# Produces: artifacts/validator.zip
#
# The --platform manylinux2014_x86_64 flag is CRITICAL: it forces pip to
# download pre-compiled wheels built for Amazon Linux 2 (the Lambda runtime),
# not for the developer's local OS. Without this, Pydantic's C extensions
# would be incompatible with the Lambda runtime and the function would fail
# with an ImportError on cold start.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SRC="$REPO_ROOT/src/lambda/validator"
SCHEMAS="$REPO_ROOT/src/schemas"
ARTIFACTS="$REPO_ROOT/artifacts"
BUILD_DIR="$REPO_ROOT/.build/lambda"

echo "==> Cleaning build dir"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$ARTIFACTS"

echo "==> Installing dependencies (manylinux2014 wheels for Amazon Linux 2)"
# --python-version must match the Lambda runtime in infra/modules/lambda/main.tf
# Currently: python3.12. Update both places if the runtime changes.
pip install \
  --quiet \
  --target "$BUILD_DIR" \
  --requirement "$SRC/requirements.txt" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all:

echo "==> Copying Lambda source files (preserving validator package structure)"
mkdir -p "$BUILD_DIR/validator"
cp "$SRC/handler.py"      "$BUILD_DIR/validator/"
cp "$SRC/idempotency.py"  "$BUILD_DIR/validator/"
cp "$SRC/validator.py"    "$BUILD_DIR/validator/"
touch "$BUILD_DIR/validator/__init__.py"

echo "==> Copying schemas package (required by validator.py at runtime)"
mkdir -p "$BUILD_DIR/src/schemas"
cp "$SCHEMAS/__init__.py"  "$BUILD_DIR/src/schemas/"
cp "$SCHEMAS/ecommerce.py" "$BUILD_DIR/src/schemas/"
touch "$BUILD_DIR/src/__init__.py"

PYTHON_BIN=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)

echo "==> Creating artifacts/validator.zip"
cd "$BUILD_DIR"
ZIP_OUT="$ARTIFACTS/validator.zip" "$PYTHON_BIN" -c "
import zipfile, os
zip_path = os.environ['ZIP_OUT']
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('.'):
        for file in files:
            full = os.path.join(root, file)
            zf.write(full, os.path.relpath(full, '.'))
"

echo "==> Done: $ARTIFACTS/validator.zip"
