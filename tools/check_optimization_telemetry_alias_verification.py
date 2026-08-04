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
    expected_context = (expected_workflow_run_id, expected_workflow_run_attempt)
    if (expected_workflow_run_id is None) != (
        expected_workflow_run_attempt is None
    ):
        errors.append("expected workflow run ID and attempt must be provided together")
    for label, value in zip(("run ID", "run attempt"), expected_context):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
        ):
            errors.append(f"expected workflow {label} is not a positive integer")

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

    run_id = receipt.get("verification_workflow_run_id")
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
        errors.append("verification workflow run ID is not a positive integer")
    run_attempt = receipt.get("verification_workflow_run_attempt")
    if (
        isinstance(run_attempt, bool)
        or not isinstance(run_attempt, int)
        or run_attempt <= 0
    ):
        errors.append("verification workflow run attempt is not a positive integer")
    if expected_workflow_run_id is not None and run_id != expected_workflow_run_id:
        errors.append("verification workflow run ID does not match expected run")
    if (
        expected_workflow_run_attempt is not None
        and run_attempt != expected_workflow_run_attempt
    ):
        errors.append("verification workflow run attempt does not match expected run")
    if (
        isinstance(run_id, int)
        and not isinstance(run_id, bool)
        and run_id > 0
        and isinstance(run_attempt, int)
        and not isinstance(run_attempt, bool)
        and run_attempt > 0
        and receipt.get("verification_artifact_name")
        != verification_artifact_name(run_id, run_attempt)
    ):
        errors.append("verification artifact name does not match workflow attempt")
    if receipt.get("gate_status") != "passed":
        errors.append("verification gate did not pass")
    if receipt.get("verified") is not True:
        errors.append("receipt is not marked as verified")
    return errors


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
