#!/usr/bin/env bash
set -uo pipefail

PYTHON_BIN="${PYTHON:-python}"
OUTPUT_DIR="${RC_GATE_OUTPUT_DIR:-/tmp/ic-release-candidate-gate}"
SEGMENTS_ROOT="${RC_GATE_AC08_SEGMENTS_DIR:-${OUTPUT_DIR}.segments}"
EVIDENCE_DIR="${RC_GATE_EVIDENCE_DIR:-artifacts/test-evidence/release-candidate-gate}"
TIMEOUT_SECONDS="${RC_GATE_AC08_SEGMENT_TIMEOUT_SECONDS:-240}"
INPUT_DIR="${RC_GATE_AC08_INPUT_DIR:-artifacts/images_to_convert}"
DESCRIPTIONS_PATH="${RC_GATE_AC08_DESCRIPTIONS_PATH:-artifacts/images_to_convert/Finale_Wurzelformen_V3.xml}"
ITERATIONS="${RC_GATE_AC08_ITERATIONS:-32}"
VENDOR_SITE_PACKAGES="vendor/linux-py310/site-packages"
if [[ -d "$VENDOR_SITE_PACKAGES" ]]; then
  export PYTHONPATH="${VENDOR_SITE_PACKAGES}:${PYTHONPATH:-}"
fi
STATUS_PATH="${EVIDENCE_DIR}/ac08_segment_status.csv"

mkdir -p "$EVIDENCE_DIR"
rm -rf -- "$SEGMENTS_ROOT" "$OUTPUT_DIR"
mkdir -p "$SEGMENTS_ROOT"
echo 'variant;exit;classification;output_dir;log' > "$STATUS_PATH"

if [[ -n "${RC_GATE_AC08_VARIANTS:-}" ]]; then
  read -r -a VARIANTS <<< "${RC_GATE_AC08_VARIANTS//,/ }"
else
  mapfile -t VARIANTS < <("$PYTHON_BIN" - <<'PY'
from src.successfulConversions import AC08_REGRESSION_VARIANTS
print("\n".join(AC08_REGRESSION_VARIANTS))
PY
  )
fi

BLOCKERS=0
for variant in "${VARIANTS[@]}"; do
  segment_dir="${SEGMENTS_ROOT}/${variant}"
  log_path="${EVIDENCE_DIR}/ac08-segment-${variant}.log"
  mkdir -p "$segment_dir"
  if [[ -n "${RC_GATE_AC08_SEGMENT_CMD_TEMPLATE:-}" ]]; then
    command="${RC_GATE_AC08_SEGMENT_CMD_TEMPLATE//\{variant\}/$variant}"
    command="${command//\{output_dir\}/$segment_dir}"
  else
    segment_input_dir="$($PYTHON_BIN tools/ac08_segment_contract.py resolve-input-dir "$INPUT_DIR" "$variant")"
    command="${PYTHON_BIN} -m src.iCCModules.imageCompositeConverterCli --input-dir ${segment_input_dir} --descriptions-path ${DESCRIPTIONS_PATH} --output-dir ${segment_dir} --ac08-regression-set --ac08-regression-variant ${variant} --deterministic-order --iterations ${ITERATIONS}"
  fi
  echo "==> AC08 segment ${variant}"
  set +e
  timeout "$TIMEOUT_SECONDS" bash -c "$command" >"$log_path" 2>&1
  status=$?
  set -e
  classification=PASS
  if [[ "$status" -eq 0 ]]; then
    if "$PYTHON_BIN" tools/ac08_segment_contract.py check-iteration-report "$segment_dir/reports/Iteration_Log.csv" "$variant"
    then
      touch "${segment_dir}/.segment-complete"
    else
      classification=BLOCKER_MISSING_REPORT
      BLOCKERS=1
      echo "AC08 segment ${variant} exited 0 but produced no matching Iteration_Log.csv row" >>"$log_path"
    fi
  else
    classification=BLOCKER
    BLOCKERS=1
  fi
  printf '%s;%s;%s;%s;%s\n' "$variant" "$status" "$classification" "$segment_dir" "$log_path" >> "$STATUS_PATH"
done

if [[ "$BLOCKERS" -ne 0 ]]; then
  echo "AC08 segmented smoke failed; aggregate metrics withheld" >&2
  exit 1
fi

if [[ -n "${RC_GATE_AC08_FINALIZE_CMD:-}" ]]; then
  bash -c "$RC_GATE_AC08_FINALIZE_CMD"
else
  "$PYTHON_BIN" tools/finalize_ac08_segmented_run.py "$SEGMENTS_ROOT" "$OUTPUT_DIR" \
    --input-dir "$INPUT_DIR" --descriptions-path "$DESCRIPTIONS_PATH" --iterations "$ITERATIONS"
fi
