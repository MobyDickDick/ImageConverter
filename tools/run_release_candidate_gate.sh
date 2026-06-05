#!/usr/bin/env bash
set -uo pipefail

PYTHON_BIN="${PYTHON:-python}"
RC_GATE_NAME="${RC_GATE_NAME:-release-candidate-gate}"
RC_GATE_OUTPUT_DIR="${RC_GATE_OUTPUT_DIR:-/tmp/ic-release-candidate-gate}"
RC_GATE_EVIDENCE_DIR="${RC_GATE_EVIDENCE_DIR:-artifacts/test-evidence/${RC_GATE_NAME}}"
RC_GATE_ACCEPTED_EXCEPTIONS=",${RC_GATE_ACCEPTED_EXCEPTIONS:-},"
RC_GATE_AC08_TIMEOUT_SECONDS="${RC_GATE_AC08_TIMEOUT_SECONDS:-900}"
RC_GATE_WORK_PACKAGE="${RC_GATE_WORK_PACKAGE:-FP-D12}"
VENDOR_SITE_PACKAGES="vendor/linux-py310/site-packages"
if [[ -d "$VENDOR_SITE_PACKAGES" ]]; then
  export PYTHONPATH="${VENDOR_SITE_PACKAGES}:${PYTHONPATH:-}"
fi

usage() {
  cat <<'USAGE'
Usage: tools/run_release_candidate_gate.sh

Runs the fixed release-candidate gate checklist and records evidence for:
  1. core suite: pytest -q -rs
  2. AC08 smoke: deterministic AC08 regression-set converter run
  3. quality gate: ac08_success_metrics.csv criteria/baseline comparison

Environment overrides:
  PYTHON                         Python executable (default: python)
  RC_GATE_NAME                   Evidence subdirectory name
  RC_GATE_OUTPUT_DIR             Converter output directory for the AC08 smoke
  RC_GATE_EVIDENCE_DIR           Evidence log/summary directory
  RC_GATE_ACCEPTED_EXCEPTIONS    Comma-separated step names allowed to fail
  RC_GATE_AC08_TIMEOUT_SECONDS   AC08 smoke timeout in seconds (default: 900)
  RC_GATE_WORK_PACKAGE           Work-package label in logs (default: FP-D12)
  RC_GATE_CORE_CMD               Shell command override for the core suite
  RC_GATE_AC08_SMOKE_CMD         Shell command override for the AC08 smoke
  RC_GATE_QUALITY_CMD            Shell command override for the quality gate
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mkdir -p "$RC_GATE_OUTPUT_DIR" "$RC_GATE_EVIDENCE_DIR"

run_gate_step() {
  local step_name="$1"
  local default_command="$2"
  local command_override="$3"
  local command="${command_override:-$default_command}"
  local log_path="${RC_GATE_EVIDENCE_DIR}/${step_name}.log"
  local summary_path="${RC_GATE_EVIDENCE_DIR}/${step_name}-summary.md"

  echo "==> ${RC_GATE_WORK_PACKAGE} ${step_name}"
  set +e
  ./tools/run_test_evidence.sh \
    --name "${RC_GATE_WORK_PACKAGE} ${step_name}" \
    --log "$log_path" \
    --summary "$summary_path" \
    -- bash -lc "$command"
  local status=$?
  set -e

  local classification="PASS"
  if [[ "$status" -ne 0 ]]; then
    if [[ "$RC_GATE_ACCEPTED_EXCEPTIONS" == *",${step_name},"* ]]; then
      classification="ACCEPTED_EXCEPTION"
    else
      classification="BLOCKER"
    fi
  fi
  printf '%s;%s;%s;%s\n' "$step_name" "$status" "$classification" "$log_path" >> "${RC_GATE_EVIDENCE_DIR}/gate_status.csv"
  echo "${step_name}: ${classification} (exit ${status})"
  [[ "$classification" != "BLOCKER" ]]
}

: > "${RC_GATE_EVIDENCE_DIR}/gate_status.csv"
echo "step;exit;classification;log" > "${RC_GATE_EVIDENCE_DIR}/gate_status.csv"

CORE_DEFAULT="${PYTHON_BIN} -m pytest -q -rs"
AC08_SMOKE_DEFAULT="timeout ${RC_GATE_AC08_TIMEOUT_SECONDS} ${PYTHON_BIN} -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir ${RC_GATE_OUTPUT_DIR} --ac08-regression-set --deterministic-order"
QUALITY_DEFAULT="${PYTHON_BIN} tools/check_ac08_success_metrics_gate.py ${RC_GATE_OUTPUT_DIR}/reports/ac08_success_metrics.csv"

BLOCKERS=0
run_gate_step "core-suite" "$CORE_DEFAULT" "${RC_GATE_CORE_CMD:-}" || BLOCKERS=1

# A release-candidate decision must never consume metrics left by an earlier run.
rm -rf -- "$RC_GATE_OUTPUT_DIR"
mkdir -p "$RC_GATE_OUTPUT_DIR"
run_gate_step "ac08-smoke" "$AC08_SMOKE_DEFAULT" "${RC_GATE_AC08_SMOKE_CMD:-}" || BLOCKERS=1
run_gate_step "quality-gate" "$QUALITY_DEFAULT" "${RC_GATE_QUALITY_CMD:-}" || BLOCKERS=1

if [[ "$BLOCKERS" -eq 0 ]]; then
  echo "${RC_GATE_WORK_PACKAGE} gate status: PASS"
  exit 0
fi

echo "${RC_GATE_WORK_PACKAGE} gate status: FAIL (BLOCKER rows in ${RC_GATE_EVIDENCE_DIR}/gate_status.csv)" >&2
exit 1
