#!/usr/bin/env python3
"""Check that a telemetry-alias verification receipt is valid and successful."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALIAS_SCHEMA_VERSION = "optimization_render_telemetry_baseline_alias_v1"
RECEIPT_SCHEMA_VERSION = "optimization_render_telemetry_alias_verification_v1"


def verification_errors(
    alias: dict[str, Any], receipt: dict[str, Any]
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

    run_id = receipt.get("verification_workflow_run_id")
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
        errors.append("verification workflow run ID is not a positive integer")
    if receipt.get("gate_status") != "passed":
        errors.append("verification gate did not pass")
    if receipt.get("verified") is not True:
        errors.append("receipt is not marked as verified")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alias", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()

    alias = json.loads(args.alias.read_text(encoding="utf-8"))
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    errors = verification_errors(alias, receipt)
    if errors:
        print("Telemetry alias verification: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Telemetry alias verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
