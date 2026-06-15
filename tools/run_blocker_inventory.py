#!/usr/bin/env python3
"""Run pytest blocker inventory and refresh its documented top-blocker list."""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

START_MARKER = "<!-- blocker-inventory:start -->"
END_MARKER = "<!-- blocker-inventory:end -->"
DEFAULT_PYTEST_ARGS = ["--maxfail=1", "-vv", "--durations=20"]
DURATION_RE = re.compile(
    r"^(?P<seconds>\d+(?:\.\d+)?)s\s+(?P<phase>call|setup|teardown)\s+"
    r"(?P<nodeid>\S.*)$"
)
FAILURE_RE = re.compile(r"^FAILED\s+(?P<nodeid>\S+)")


def parse_inventory(log_text: str, *, limit: int = 20) -> tuple[list[tuple[float, str, str]], list[str]]:
    durations: list[tuple[float, str, str]] = []
    failures: list[str] = []
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        duration = DURATION_RE.match(line)
        if duration:
            durations.append(
                (
                    float(duration.group("seconds")),
                    duration.group("phase"),
                    duration.group("nodeid"),
                )
            )
        failure = FAILURE_RE.match(line)
        if failure and failure.group("nodeid") not in failures:
            failures.append(failure.group("nodeid"))
    durations.sort(key=lambda row: row[0], reverse=True)
    return durations[:limit], failures


def render_section(
    *,
    run_id: str,
    log_path: Path,
    exit_code: int,
    command: list[str],
    durations: list[tuple[float, str, str]],
    failures: list[str],
) -> str:
    lines = [
        START_MARKER,
        "### Aktuelle automatisierte Top-Blocker-Inventur",
        "",
        f"- Run: `{run_id}`",
        f"- Log: `{log_path.as_posix()}`",
        f"- Exit-Code: `{exit_code}`",
        f"- Befehl: `{' '.join(command)}`",
        f"- Fehlgeschlagene Nodes: `{len(failures)}`",
        "",
        "| Rang | Dauer | Phase | Test-Node |",
        "| ---: | ---: | --- | --- |",
    ]
    if durations:
        lines.extend(
            f"| {rank} | {seconds:.2f}s | `{phase}` | `{nodeid}` |"
            for rank, (seconds, phase, nodeid) in enumerate(durations, start=1)
        )
    else:
        lines.append("| – | – | – | Keine Durationsdaten im Run-Log |")
    if failures:
        lines.extend(["", "**Fehlschläge**", ""])
        lines.extend(f"- `{nodeid}`" for nodeid in failures)
    lines.extend([END_MARKER, ""])
    return "\n".join(lines)


def update_document(path: Path, section: str) -> None:
    text = path.read_text(encoding="utf-8")
    if START_MARKER in text and END_MARKER in text:
        prefix, remainder = text.split(START_MARKER, 1)
        _, suffix = remainder.split(END_MARKER, 1)
        text = prefix.rstrip() + "\n\n" + section + suffix.lstrip("\n")
    else:
        text = text.rstrip() + "\n\n" + section
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    parser.add_argument("--log-dir", type=Path, default=Path("artifacts/converted_images/reports"))
    parser.add_argument("--document", type=Path, default=Path("docs/open_tasks.md"))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    pytest_args = args.pytest_args
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]
    command = [sys.executable, "-m", "pytest", *(pytest_args or DEFAULT_PYTEST_ARGS)]
    args.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.log_dir / f"blocker_inventory_{args.run_id}.log"

    with log_path.open("w", encoding="utf-8") as log_file:
        print("+", " ".join(command))
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log_file.write(line)
        exit_code = process.wait()

    durations, failures = parse_inventory(log_path.read_text(encoding="utf-8"), limit=args.limit)
    section = render_section(
        run_id=args.run_id,
        log_path=log_path,
        exit_code=exit_code,
        command=command,
        durations=durations,
        failures=failures,
    )
    update_document(args.document, section)
    print(f"inventory_log={log_path}")
    print(f"inventory_document={args.document}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
