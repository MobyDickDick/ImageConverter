#!/usr/bin/env bash
set -euo pipefail

NAME=""
LOG_PATH=""
SUMMARY_PATH=""
EXPECTED_EXIT=""

usage() {
  cat <<'USAGE'
Usage: tools/run_test_evidence.sh --name NAME --log PATH --summary PATH [--expected-exit CODE] -- COMMAND [ARG...]

Runs COMMAND, mirrors its output to LOG, writes a compact Markdown evidence
summary with PASS/FAIL, the observed command exit code, and whether an optional
expected exit code was met. The wrapper always exits with the observed command
exit code. When GITHUB_STEP_SUMMARY is set, the summary is appended there too.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --name requires a value" >&2
        usage >&2
        exit 2
      fi
      NAME="$2"
      shift 2
      ;;
    --log)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --log requires a path" >&2
        usage >&2
        exit 2
      fi
      LOG_PATH="$2"
      shift 2
      ;;
    --summary)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --summary requires a path" >&2
        usage >&2
        exit 2
      fi
      SUMMARY_PATH="$2"
      shift 2
      ;;
    --expected-exit)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --expected-exit requires an integer from 0 to 255" >&2
        usage >&2
        exit 2
      fi
      EXPECTED_EXIT="$2"
      shift 2
      ;;
    --)
      shift
      break
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

if [[ -z "$NAME" || -z "$LOG_PATH" || -z "$SUMMARY_PATH" ]]; then
  echo "ERROR: --name, --log and --summary are required" >&2
  usage >&2
  exit 2
fi

if [[ -n "$EXPECTED_EXIT" ]] && {
  [[ ! "$EXPECTED_EXIT" =~ ^[0-9]+$ ]] ||
  (( 10#$EXPECTED_EXIT > 255 ))
}; then
  echo "ERROR: --expected-exit must be an integer from 0 to 255" >&2
  usage >&2
  exit 2
fi

if [[ $# -eq 0 ]]; then
  echo "ERROR: missing command after --" >&2
  usage >&2
  exit 2
fi

mkdir -p "$(dirname "$LOG_PATH")" "$(dirname "$SUMMARY_PATH")"

COMMAND=("$@")

printf '==> %s\n' "$NAME" | tee "$LOG_PATH"
printf 'Command:' | tee -a "$LOG_PATH"
for arg in "${COMMAND[@]}"; do
  printf ' %q' "$arg" | tee -a "$LOG_PATH"
done
printf '\n' | tee -a "$LOG_PATH"

set +e
"${COMMAND[@]}" 2>&1 | tee -a "$LOG_PATH"
STATUS=${PIPESTATUS[0]}
set -e

if [[ "$STATUS" -eq 0 ]]; then
  VERDICT="PASS"
else
  VERDICT="FAIL"
fi

if [[ -z "$EXPECTED_EXIT" ]]; then
  EXPECTATION="NOT_SPECIFIED"
  EXPECTED_EXIT_SUMMARY="not specified"
elif [[ "$STATUS" -eq "$((10#$EXPECTED_EXIT))" ]]; then
  EXPECTATION="MET"
  EXPECTED_EXIT_SUMMARY="$((10#$EXPECTED_EXIT))"
else
  EXPECTATION="UNMET"
  EXPECTED_EXIT_SUMMARY="$((10#$EXPECTED_EXIT))"
fi

RUN_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
{
  echo "# Test evidence: ${NAME}"
  echo
  echo "- Verdict: ${VERDICT}"
  echo "- Exit code: ${STATUS}"
  echo "- Expected exit code: ${EXPECTED_EXIT_SUMMARY}"
  echo "- Expectation: ${EXPECTATION}"
  echo "- UTC time: ${RUN_AT}"
  echo "- Git ref: ${GITHUB_REF:-local}"
  echo "- Git SHA: ${GITHUB_SHA:-local}"
  echo "- Log: ${LOG_PATH}"
} > "$SUMMARY_PATH"

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  cat "$SUMMARY_PATH" >> "$GITHUB_STEP_SUMMARY"
fi

exit "$STATUS"
