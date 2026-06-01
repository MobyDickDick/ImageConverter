#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python}"
SATISFACTORY_REGRESSION_TIMEOUT_SECONDS="${SATISFACTORY_REGRESSION_TIMEOUT_SECONDS:-900}"

# Keep the existing heavy-test gate semantics: callers that want the full
# reconversion battery must opt in with RUN_HEAVY_CONVERSION_TESTS=1.
export RUN_HEAVY_CONVERSION_TESTS="${RUN_HEAVY_CONVERSION_TESTS:-0}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"

PYTEST_ARGS=(
  -vv
  -ra
  --durations=10
  tests/test_satisfactory_regression_battery.py
)
if [[ $# -gt 0 ]]; then
  PYTEST_ARGS+=("$@")
fi

echo "==> satisfactory regression battery"
echo "    RUN_HEAVY_CONVERSION_TESTS=${RUN_HEAVY_CONVERSION_TESTS}"
echo "    SATISFACTORY_REGRESSION_TIMEOUT_SECONDS=${SATISFACTORY_REGRESSION_TIMEOUT_SECONDS}"
echo "    pytest args: ${PYTEST_ARGS[*]}"

if [[ "${SATISFACTORY_REGRESSION_TIMEOUT_SECONDS}" != "0" ]] && command -v timeout >/dev/null 2>&1; then
  exec timeout --foreground "${SATISFACTORY_REGRESSION_TIMEOUT_SECONDS}" \
    "${PYTHON_BIN}" -m pytest "${PYTEST_ARGS[@]}"
fi

exec "${PYTHON_BIN}" -m pytest "${PYTEST_ARGS[@]}"
