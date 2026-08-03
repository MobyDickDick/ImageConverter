#!/usr/bin/env python3
"""Resolve and validate the promoted optimization-telemetry baseline alias."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineAlias:
    run_id: str
    artifact_name: str


def resolve_baseline_alias(
    *,
    input_run_id: str = "",
    input_artifact_name: str = "",
    variable_run_id: str = "",
    variable_artifact_name: str = "",
) -> BaselineAlias:
    """Resolve either a complete manual override or a complete repository alias."""

    input_run_id = input_run_id.strip()
    input_artifact_name = input_artifact_name.strip()
    if bool(input_run_id) != bool(input_artifact_name):
        raise ValueError("Provide both baseline workflow overrides or leave both empty")

    if input_run_id:
        run_id, artifact_name = input_run_id, input_artifact_name
    else:
        run_id = variable_run_id.strip()
        artifact_name = variable_artifact_name.strip()
        if not run_id or not artifact_name:
            raise ValueError(
                "Set both telemetry baseline repository variables or provide both workflow overrides"
            )

    if not re.fullmatch(r"[1-9][0-9]*", run_id):
        raise ValueError("Baseline run ID must be a positive integer")
    if not re.fullmatch(
        rf"optimization-render-telemetry-baseline-{re.escape(run_id)}-[1-9][0-9]*",
        artifact_name,
    ):
        raise ValueError("Baseline artifact name must belong to the resolved run ID")
    return BaselineAlias(run_id=run_id, artifact_name=artifact_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-run-id", default="")
    parser.add_argument("--input-artifact-name", default="")
    parser.add_argument("--variable-run-id", default="")
    parser.add_argument("--variable-artifact-name", default="")
    parser.add_argument("--github-output")
    args = parser.parse_args()

    try:
        alias = resolve_baseline_alias(
            input_run_id=args.input_run_id,
            input_artifact_name=args.input_artifact_name,
            variable_run_id=args.variable_run_id,
            variable_artifact_name=args.variable_artifact_name,
        )
    except ValueError as error:
        parser.error(str(error))

    output = f"run_id={alias.run_id}\nartifact_name={alias.artifact_name}\n"
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as output_file:
            output_file.write(output)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
