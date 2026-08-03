#!/usr/bin/env python3
"""Build the repository-variable alias for a promoted telemetry baseline."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any


ALIAS_SCHEMA_VERSION = "optimization_render_telemetry_baseline_alias_v1"
GATE_WORKFLOW = "optimization-render-telemetry-gate-example.yml"
RUN_ID_VARIABLE = "OPTIMIZATION_RENDER_TELEMETRY_BASELINE_RUN_ID"
ARTIFACT_NAME_VARIABLE = "OPTIMIZATION_RENDER_TELEMETRY_BASELINE_ARTIFACT_NAME"


def build_baseline_alias(provenance: dict[str, Any]) -> dict[str, Any]:
    """Return a validated, machine-readable alias from promotion provenance."""
    if provenance.get("schema_version") != "optimization_render_telemetry_baseline_provenance_v1":
        raise ValueError("Unsupported telemetry baseline provenance schema")
    run_id = provenance.get("source_run_id")
    run_attempt = provenance.get("source_run_attempt")
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
        raise ValueError("Baseline source run ID must be a positive integer")
    if isinstance(run_attempt, bool) or not isinstance(run_attempt, int) or run_attempt <= 0:
        raise ValueError("Baseline source run attempt must be a positive integer")
    shard_start = provenance.get("shard_start")
    shard_end = provenance.get("shard_end")
    if not isinstance(shard_start, str) or not shard_start.strip():
        raise ValueError("Baseline shard start must be a non-empty string")
    if not isinstance(shard_end, str) or not shard_end.strip():
        raise ValueError("Baseline shard end must be a non-empty string")
    artifact_name = f"optimization-render-telemetry-baseline-{run_id}-{run_attempt}"
    repository_variables = {
        RUN_ID_VARIABLE: str(run_id),
        ARTIFACT_NAME_VARIABLE: artifact_name,
    }
    verification_inputs = {
        "shard_start": shard_start,
        "shard_end": shard_end,
        "promote_baseline": False,
    }
    return {
        "schema_version": ALIAS_SCHEMA_VERSION,
        "run_id": str(run_id),
        "artifact_name": artifact_name,
        "repository_variables": repository_variables,
        "activation_commands": [
            f"gh variable set {name} --body {shlex.quote(value)}"
            for name, value in repository_variables.items()
        ],
        "verification_command": (
            f"gh workflow run {GATE_WORKFLOW} "
            f"-f shard_start={shlex.quote(shard_start)} "
            f"-f shard_end={shlex.quote(shard_end)} "
            "-f promote_baseline=false"
        ),
        "verification_dispatch": {
            "workflow": GATE_WORKFLOW,
            "inputs": verification_inputs,
        },
        "source_sha": provenance.get("source_sha"),
        "shard_start": shard_start,
        "shard_end": shard_end,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provenance", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    provenance = json.loads(args.provenance.read_text(encoding="utf-8"))
    alias = build_baseline_alias(provenance)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(alias, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
