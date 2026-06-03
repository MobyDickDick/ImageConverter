#!/usr/bin/env bash
set -euo pipefail

NAME=""
LOG_PATH=""
SUMMARY_PATH=""

usage() {
  cat <<'USAGE'
Usage: tools/run_test_evidence.sh --name NAME --log PATH --summary PATH -- COMMAND [ARG...]

Runs COMMAND, mirrors its output to LOG, writes a compact Markdown evidence
summary with PASS/FAIL and the command exit code, and exits with the same code.
When GITHUB_STEP_SUMMARY is set, the summary is appended there as well.
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

RUN_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
{
  echo "# Test evidence: ${NAME}"
  echo
  echo "- Verdict: ${VERDICT}"
  echo "- Exit code: ${STATUS}"
  echo "- UTC time: ${RUN_AT}"
  echo "- Git ref: ${GITHUB_REF:-local}"
  echo "- Git SHA: ${GITHUB_SHA:-local}"
  echo "- Log: ${LOG_PATH}"
} > "$SUMMARY_PATH"

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  cat "$SUMMARY_PATH" >> "$GITHUB_STEP_SUMMARY"
fi

exit "$STATUS"
