#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/lambda-layer"
ZIP_PATH="${ROOT_DIR}/build/lambda-layer.zip"

rm -rf "${BUILD_DIR}" "${ZIP_PATH}"
mkdir -p "${BUILD_DIR}/python"

python -m pip install \
  --upgrade \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --target "${BUILD_DIR}/python" \
  -r "${ROOT_DIR}/requirements.txt"

cd "${BUILD_DIR}"
zip -qr "${ZIP_PATH}" python

echo "${ZIP_PATH}"
