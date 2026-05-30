#!/usr/bin/env bash
set -euo pipefail

SUMMARY_PATH="artifacts/converted_images/reports/chain_phase_telemetry_summary.txt"
REQUIRE_DRIFT_SUMMARY=0
PYTHON_BIN="${PYTHON:-python}"
VENDOR_SITE_PACKAGES="vendor/linux-py310/site-packages"
if [[ -d "$VENDOR_SITE_PACKAGES" ]]; then
  export PYTHONPATH="${VENDOR_SITE_PACKAGES}:${PYTHONPATH:-}"
fi

usage() {
  cat <<'USAGE'
Usage: tools/run_local_completion_checks.sh [--summary PATH] [--require-drift-summary]

Runs the standard local completion profile:
  1. syntax/import compilation for src and tests
  2. the pytest suite
  3. the ImageConverter CLI help smoke test
  4. the chain-telemetry drift gate when a summary artifact is present

The repo vendor path is prepended to PYTHONPATH when available so CLI smoke
checks can resolve bundled runtime dependencies. By default the drift-gate
step is advisory: missing summaries are skipped, and existing drift warnings
are printed without failing code-only completion profiles. Use
--require-drift-summary to make a missing or warning summary fail the profile.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --summary requires a path" >&2
        usage >&2
        exit 2
      fi
      SUMMARY_PATH="$2"
      shift 2
      ;;
    --require-drift-summary)
      REQUIRE_DRIFT_SUMMARY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

run_step() {
  local label="$1"
  shift
  echo "==> ${label}"
  "$@"
}

run_step "compileall" "$PYTHON_BIN" -m compileall src tests
run_step "pytest" "$PYTHON_BIN" -m pytest
run_step "ImageConverter CLI help" "$PYTHON_BIN" -m src.imageCompositeConverter --help

if [[ -f "$SUMMARY_PATH" ]]; then
  echo "==> chain telemetry drift gate"
  set +e
  "$PYTHON_BIN" tools/check_chain_telemetry_drift_gate.py "$SUMMARY_PATH"
  DRIFT_STATUS=$?
  set -e
  if [[ "$DRIFT_STATUS" -ne 0 ]]; then
    if [[ "$REQUIRE_DRIFT_SUMMARY" -eq 1 ]]; then
      exit "$DRIFT_STATUS"
    fi
    echo "WARN: advisory drift gate failed for ${SUMMARY_PATH}; use --require-drift-summary to make this fatal."
  fi
elif [[ "$REQUIRE_DRIFT_SUMMARY" -eq 1 ]]; then
  echo "ERROR: required drift summary artifact is missing: ${SUMMARY_PATH}" >&2
  exit 1
else
  echo "==> chain telemetry drift gate"
  echo "SKIP: drift summary artifact is missing: ${SUMMARY_PATH}"
fi
