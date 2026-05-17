#!/usr/bin/env bash
set -euo pipefail

python -m pytest tests/test_conversion_regression_smoke.py
python -m pytest tests/test_weak_family_pipeline.py
