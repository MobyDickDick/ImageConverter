#!/usr/bin/env python3
"""Record the externally executed telemetry-alias verification result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RECEIPT_SCHEMA_VERSION = "optimization_render_telemetry_alias_verification_v2"
ALIAS_SCHEMA_VERSION = "optimization_render_telemetry_baseline_alias_v1"
GATE_STATUSES = {"passed", "failed", "cancelled", "timed_out"}


def build_verification_receipt(
    alias: dict[str, Any],
    *,
    workflow_run_id: int,
    gate_status: str,
    verification_source_sha: str,
) -> dict[str, Any]:
    """Validate and bind a workflow result to the alias that it verified."""
    if alias.get("schema_version") != ALIAS_SCHEMA_VERSION:
        raise ValueError("Unsupported telemetry baseline alias schema")
    if isinstance(workflow_run_id, bool) or workflow_run_id <= 0:
        raise ValueError("Verification workflow run ID must be a positive integer")
    if gate_status not in GATE_STATUSES:
        raise ValueError(
            "Gate status must be one of: " + ", ".join(sorted(GATE_STATUSES))
        )
    baseline_source_sha = alias.get("source_sha")
    if not isinstance(baseline_source_sha, str) or not baseline_source_sha.strip():
        raise ValueError("Alias must contain a baseline source SHA")
    if verification_source_sha != baseline_source_sha:
        raise ValueError("Verification source SHA must match the baseline source SHA")

    dispatch = alias.get("verification_dispatch")
    if not isinstance(dispatch, dict) or not isinstance(dispatch.get("workflow"), str):
        raise ValueError("Alias must contain a verification dispatch")

    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "verification_workflow_run_id": workflow_run_id,
        "verification_source_sha": verification_source_sha,
        "gate_status": gate_status,
        "verified": gate_status == "passed",
        "workflow": dispatch["workflow"],
        "verification_inputs": dispatch.get("inputs"),
        "baseline_run_id": alias.get("run_id"),
        "baseline_artifact_name": alias.get("artifact_name"),
        "baseline_source_sha": baseline_source_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alias", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--workflow-run-id", required=True, type=int)
    parser.add_argument("--verification-source-sha", required=True)
    parser.add_argument("--gate-status", required=True, choices=sorted(GATE_STATUSES))
    args = parser.parse_args()

    alias = json.loads(args.alias.read_text(encoding="utf-8"))
    receipt = build_verification_receipt(
        alias,
        workflow_run_id=args.workflow_run_id,
        gate_status=args.gate_status,
        verification_source_sha=args.verification_source_sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
