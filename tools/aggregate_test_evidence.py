#!/usr/bin/env python3
"""Aggregate raw test evidence without treating expected failures as blockers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _parse_summary(path: Path) -> dict[str, str]:
    record = {"path": str(path)}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Test evidence: "):
            record["name"] = line.removeprefix("# Test evidence: ").strip()
        elif line.startswith("- ") and ": " in line:
            key, value = line[2:].split(": ", 1)
            record[key.lower().replace(" ", "_")] = value.strip()
    return record


def _is_covered_scenario(record: dict[str, str]) -> bool:
    return record.get("expectation") == "MET" or record.get("verdict") == "PASS"


def _completion_status(record: dict[str, str] | None) -> str:
    if record is None:
        return "FAIL"
    if record.get("expectation") == "UNMET":
        return "FAIL"
    return "PASS" if record.get("verdict") == "PASS" else "FAIL"


def _write_correction_task(
    path: Path,
    completion: dict[str, str] | None,
    reproduction_command: str,
) -> None:
    exit_code = completion.get("exit_code", "unknown") if completion else "missing"
    log_path = completion.get("log", "not recorded") if completion else "not recorded"
    git_sha = completion.get("git_sha", "not recorded") if completion else "not recorded"
    scenario_id = completion.get("scenario_id", "completion-profile") if completion else "completion-profile"
    symptom = (
        "Das Abschlussprofil fehlt in der Evidence."
        if completion is None
        else f"Das Abschlussprofil endete mit Exit-Code {exit_code}."
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Automatisch erzeugte Korrekturaufgabe\n\n"
        f"- Symptom: {symptom}\n"
        f"- Szenario-ID: {scenario_id}\n"
        f"- Reproduktionsbefehl: `{reproduction_command}`\n"
        "- Erwartetes Ergebnis: Abschlussprofil mit `Verdict: PASS` und Exit-Code `0`.\n"
        f"- Tatsächlicher Exit-Code: {exit_code}\n"
        f"- Logpfad: `{log_path}`\n"
        f"- Git-SHA: `{git_sha}`\n"
        "- Akzeptanztest: Derselbe Reproduktionsbefehl erzeugt ein grünes "
        "`completion-profile` und das Aggregat meldet `overall_verdict=PASS`.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate Markdown summaries produced by run_test_evidence.sh."
    )
    parser.add_argument("summaries", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--completion-scenario", default="completion-profile")
    parser.add_argument("--correction-task", type=Path)
    parser.add_argument(
        "--reproduction-command",
        default="./tools/run_local_completion_checks.sh",
    )
    args = parser.parse_args()

    records = [_parse_summary(path) for path in args.summaries]
    completion = next(
        (
            record
            for record in reversed(records)
            if record.get("scenario_id") == args.completion_scenario
            or record.get("name") == args.completion_scenario
        ),
        None,
    )
    overall_verdict = _completion_status(completion)
    covered_count = sum(_is_covered_scenario(record) for record in records)

    lines = [
        "# Test evidence aggregation",
        "",
        "## Scenario evidence",
        "",
        "| Scenario ID | Verdict | Exit code | Expectation | Classification |",
        "|---|---:|---:|---:|---|",
    ]
    for record in records:
        classification = "COVERED" if _is_covered_scenario(record) else "UNRESOLVED"
        lines.append(
            "| {scenario_id} | {verdict} | {exit_code} | {expectation} | {classification} |".format(
                scenario_id=record.get("scenario_id", record.get("name", "unknown")),
                verdict=record.get("verdict", "UNKNOWN"),
                exit_code=record.get("exit_code", "unknown"),
                expectation=record.get("expectation", "NOT_SPECIFIED"),
                classification=classification,
            )
        )
    lines.extend(
        [
            "",
            "## Completion verdict",
            "",
            f"- Overall verdict: {overall_verdict}",
            f"- Completion scenario: {args.completion_scenario}",
            f"- Completion exit code: {completion.get('exit_code', 'missing') if completion else 'missing'}",
            f"- Covered scenarios: {covered_count}/{len(records)}",
            (
                "- Correction task: not required"
                if overall_verdict == "PASS"
                else f"- Correction task: {args.correction_task or 'not configured'}"
            ),
            "",
        ]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "schema": "test_evidence_aggregation_v1",
        "overall_verdict": overall_verdict,
        "completion_scenario": args.completion_scenario,
        "completion_exit_code": (
            int(completion["exit_code"])
            if completion and completion.get("exit_code", "").isdigit()
            else None
        ),
        "covered_scenarios": covered_count,
        "scenario_count": len(records),
        "scenarios": records,
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if overall_verdict == "FAIL" and args.correction_task:
        _write_correction_task(
            args.correction_task,
            completion,
            args.reproduction_command,
        )
    elif overall_verdict == "PASS" and args.correction_task:
        args.correction_task.unlink(missing_ok=True)
    return 0 if overall_verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
