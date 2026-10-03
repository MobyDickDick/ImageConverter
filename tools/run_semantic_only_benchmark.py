#!/usr/bin/env python3
"""Run a repeatable JPEG + description benchmark without donor artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Sequence


SCHEMA_VERSION = "semantic_only_benchmark_v1"
RunCommand = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _load_samples(manifest_path: Path) -> list[str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"manifest schema_version must be {SCHEMA_VERSION}")
    samples = payload.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("manifest samples must be a non-empty list")
    normalized: list[str] = []
    for sample in samples:
        if not isinstance(sample, str) or Path(sample).name != sample:
            raise ValueError("every sample must be a plain JPEG filename")
        if Path(sample).suffix.lower() not in {".jpg", ".jpeg"}:
            raise ValueError(f"sample is not a JPEG: {sample}")
        normalized.append(sample)
    if len(set(normalized)) != len(normalized):
        raise ValueError("manifest contains duplicate samples")
    return normalized


def _default_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    environment = {**os.environ, "TINY_ICC_OUTPUT_VARIATION": "0"}
    return subprocess.run(
        command, check=False, capture_output=True, text=True, env=environment
    )


def _find_svg(output_dir: Path, stem: str) -> Path:
    matches = [path for path in output_dir.rglob(f"{stem}.svg") if "snapshot" not in str(path).lower()]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one result SVG for {stem}, found {len(matches)}")
    return matches[0]


def run_benchmark(
    manifest_path: Path,
    image_dir: Path,
    descriptions_path: Path,
    work_dir: Path,
    *,
    repetitions: int = 2,
    runner: RunCommand = _default_runner,
) -> dict[str, Any]:
    """Run each sample in isolation and compare its SVG digest across repetitions."""
    if repetitions < 2:
        raise ValueError("at least two repetitions are required to prove stability")
    samples = _load_samples(manifest_path)
    if not descriptions_path.is_file():
        raise FileNotFoundError(descriptions_path)
    work_dir.mkdir(parents=True, exist_ok=True)
    evaluations: list[dict[str, Any]] = []

    for sample in samples:
        source = image_dir / sample
        if not source.is_file():
            raise FileNotFoundError(source)
        digests: list[str] = []
        runs: list[dict[str, Any]] = []
        for repetition in range(1, repetitions + 1):
            run_root = work_dir / Path(sample).stem / f"run-{repetition}"
            input_dir = run_root / "input"
            output_dir = run_root / "output"
            input_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, input_dir / sample)
            command = [
                sys.executable,
                "-m",
                "src.iCCModules.imageCompositeConverterCli",
                "--input-dir",
                str(input_dir),
                "--descriptions-path",
                str(descriptions_path),
                "--output-dir",
                str(output_dir),
                "--execution-mode",
                "semantic-only",
                "--start",
                Path(sample).stem,
                "--end",
                Path(sample).stem,
                "--deterministic-order",
            ]
            completed = runner(command)
            run: dict[str, Any] = {
                "repetition": repetition,
                "exit_code": completed.returncode,
                "execution_mode": "semantic-only",
            }
            if completed.returncode == 0:
                svg_path = _find_svg(output_dir, Path(sample).stem)
                digest = hashlib.sha256(svg_path.read_bytes()).hexdigest()
                digests.append(digest)
                run["svg_sha256"] = digest
            else:
                run["error"] = (completed.stderr or completed.stdout).strip()[-2000:]
            runs.append(run)
        stable = len(digests) == repetitions and len(set(digests)) == 1
        evaluations.append({"filename": sample, "stable": stable, "runs": runs})

    stable_count = sum(item["stable"] for item in evaluations)
    return {
        "schema_version": SCHEMA_VERSION,
        "input_contract": {
            "allowed_sources": ["jpeg", "description_table"],
            "execution_mode": "semantic-only",
            "output_variation": False,
            "template_transfer": False,
            "checkpoint_resume": False,
        },
        "repetitions": repetitions,
        "summary": {
            "sample_count": len(evaluations),
            "stable_count": stable_count,
            "unstable_count": len(evaluations) - stable_count,
            "passed": stable_count == len(evaluations),
        },
        "evaluations": evaluations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--descriptions-path", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=2)
    args = parser.parse_args(argv)
    try:
        report = run_benchmark(
            args.manifest,
            args.image_dir,
            args.descriptions_path,
            args.work_dir,
            repetitions=args.repetitions,
        )
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
