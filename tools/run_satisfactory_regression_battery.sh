#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python}"
SATISFACTORY_REGRESSION_TIMEOUT_SECONDS="${SATISFACTORY_REGRESSION_TIMEOUT_SECONDS:-900}"

# This dedicated runner is the opt-in boundary for the expensive reconversion
# battery, so it enables the heavy conversion tests by default.
export RUN_HEAVY_CONVERSION_TESTS="${RUN_HEAVY_CONVERSION_TESTS:-1}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"

PY_TAG="$(${PYTHON_BIN} - <<'PYTAG'
import sys
print(f"py{sys.version_info.major}{sys.version_info.minor}")
PYTAG
)"
VENDOR_SITE_PACKAGES="vendor/linux-${PY_TAG}/site-packages"
if [[ -d "${VENDOR_SITE_PACKAGES}" ]]; then
  export PYTHONPATH="${VENDOR_SITE_PACKAGES}:${PYTHONPATH:-}"
fi

PYTEST_ARGS=(
  -vv
  -ra
  -s
  --durations=10
  tests/test_satisfactory_regression_battery.py
)
if [[ $# -gt 0 ]]; then
  PYTEST_ARGS+=("$@")
fi

echo "==> satisfactory regression battery"
echo "    RUN_HEAVY_CONVERSION_TESTS=${RUN_HEAVY_CONVERSION_TESTS}"
echo "    SATISFACTORY_REGRESSION_TIMEOUT_SECONDS=${SATISFACTORY_REGRESSION_TIMEOUT_SECONDS}"
echo "    SATISFACTORY_REGRESSION_DEBUG_DIR=${SATISFACTORY_REGRESSION_DEBUG_DIR:-<pytest tmp_path>}"
echo "    PYTHONPATH=${PYTHONPATH:-}"
echo "    pytest args: ${PYTEST_ARGS[*]}"

if [[ "${SATISFACTORY_REGRESSION_TIMEOUT_SECONDS}" != "0" ]] && command -v timeout >/dev/null 2>&1; then
  exec timeout --foreground "${SATISFACTORY_REGRESSION_TIMEOUT_SECONDS}" \
    "${PYTHON_BIN}" -m pytest "${PYTEST_ARGS[@]}"
fi

exec "${PYTHON_BIN}" -m pytest "${PYTEST_ARGS[@]}"
