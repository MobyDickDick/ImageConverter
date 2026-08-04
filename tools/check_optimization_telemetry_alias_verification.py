#!/usr/bin/env python3
"""Check that a telemetry-alias verification receipt is valid and successful."""

from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

ALIAS_SCHEMA_VERSION = "optimization_render_telemetry_baseline_alias_v1"
RECEIPT_SCHEMA_VERSION = "optimization_render_telemetry_alias_verification_v4"
VERIFICATION_ARTIFACT_PREFIX = "optimization-render-telemetry-alias-verification"


def verification_artifact_name(workflow_run_id: int, workflow_run_attempt: int) -> str:
    """Return the required artifact name for one workflow attempt."""
    return f"{VERIFICATION_ARTIFACT_PREFIX}-{workflow_run_id}-{workflow_run_attempt}"


def verification_errors(
    alias: dict[str, Any],
    receipt: dict[str, Any],
    *,
    expected_workflow_run_id: int | None = None,
    expected_workflow_run_attempt: int | None = None,
) -> list[str]:
    """Return every reason why *receipt* does not verify *alias*."""
    errors: list[str] = []
    if alias.get("schema_version") != ALIAS_SCHEMA_VERSION:
        errors.append("unsupported telemetry baseline alias schema")
    if receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        errors.append("unsupported telemetry alias verification schema")

    dispatch = alias.get("verification_dispatch")
    if not isinstance(dispatch, dict):
        errors.append("alias has no verification dispatch")
        dispatch = {}

    expected = {
        "workflow": dispatch.get("workflow"),
        "verification_inputs": dispatch.get("inputs"),
        "baseline_run_id": alias.get("run_id"),
        "baseline_artifact_name": alias.get("artifact_name"),
        "baseline_source_sha": alias.get("source_sha"),
    }
    for field, expected_value in expected.items():
        if receipt.get(field) != expected_value:
            errors.append(f"receipt {field} does not match alias")
    if receipt.get("verification_source_sha") != alias.get("source_sha"):
        errors.append("verification source SHA does not match alias")

    run_id_value = receipt.get("verification_workflow_run_id")
    run_id = _positive_int(run_id_value)
    if run_id is None:
        errors.append("verification workflow run ID is not a positive integer")
    run_attempt_value = receipt.get("verification_workflow_run_attempt")
    run_attempt = _positive_int(run_attempt_value)
    if run_attempt is None:
        errors.append("verification workflow run attempt is not a positive integer")
    if run_id is not None and run_attempt is not None and (
        receipt.get("verification_artifact_name")
        != verification_artifact_name(run_id, run_attempt)
    ):
        errors.append("verification artifact name does not match workflow attempt")
    if expected_workflow_run_id is not None and run_id != expected_workflow_run_id:
        errors.append("run ID does not match expected run")
    if (
        expected_workflow_run_attempt is not None
        and run_attempt != expected_workflow_run_attempt
    ):
        errors.append("run attempt does not match expected run")
    if receipt.get("gate_status") != "passed":
        errors.append("verification gate did not pass")
    if receipt.get("verified") is not True:
        errors.append("receipt is not marked as verified")
    return errors


def _positive_int(value: Any) -> int | None:
    """Return a positive integer for JSON numeric/string values, else ``None``."""
    if isinstance(value, bool):
        return None
    try:
        converted = int(value)
    except (TypeError, ValueError):
        return None
    return converted if converted > 0 else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alias", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--expected-workflow-run-id", type=int)
    parser.add_argument("--expected-workflow-run-attempt", type=int)
    args = parser.parse_args()

    documents: dict[str, dict[str, Any]] = {}
    load_errors: list[str] = []
    for label, path in (("alias", args.alias), ("receipt", args.receipt)):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            load_errors.append(f"cannot read {label}: {exc}")
            continue
        except JSONDecodeError as exc:
            load_errors.append(
                f"{label} is not valid JSON: line {exc.lineno} column {exc.colno}"
            )
            continue
        if not isinstance(payload, dict):
            load_errors.append(f"{label} root must be a JSON object")
            continue
        documents[label] = payload

    if load_errors:
        print("Telemetry alias verification: FAIL")
        for error in load_errors:
            print(f"- {error}")
        return 1

    alias = documents["alias"]
    receipt = documents["receipt"]
    errors = verification_errors(
        alias,
        receipt,
        expected_workflow_run_id=args.expected_workflow_run_id,
        expected_workflow_run_attempt=args.expected_workflow_run_attempt,
    )
    if errors:
        print("Telemetry alias verification: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Telemetry alias verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
