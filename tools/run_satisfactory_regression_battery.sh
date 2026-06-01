#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python}"
VENDOR_SITE_PACKAGES="vendor/linux-py310/site-packages"
if [[ -d "$VENDOR_SITE_PACKAGES" ]]; then
  export PYTHONPATH="${VENDOR_SITE_PACKAGES}:${PYTHONPATH:-}"
fi

# The satisfactory battery is intentionally outside the default core-green
# pytest profile. Enable heavy conversion collection explicitly so the whole
# stored successful-conversion baseline is reconverted and quality-compared.
export RUN_HEAVY_CONVERSION_TESTS=1

"$PYTHON_BIN" -m pytest tests/test_satisfactory_regression_battery.py
