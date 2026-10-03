#!/usr/bin/env python3
"""Run the PNG + semantic-description benchmark in isolated sandboxes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Sequence

from tools.evaluate_semantic_only_quality import evaluate_quality


SCHEMA_VERSION = "semantic_only_png_benchmark_v1"
RunCommand = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
_CASE_KEYS = {"case_id", "image_path", "semantic_description", "topology"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_cases(manifest_path: Path) -> tuple[int, list[dict[str, str]]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"manifest schema_version must be {SCHEMA_VERSION}")
    seed = payload.get("seed")
    if not isinstance(seed, int):
        raise ValueError("manifest seed must be an integer")
    if seed != 0:
        raise ValueError("deterministic-order currently requires manifest seed 0")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("manifest cases must be a non-empty list")
    normalized: list[dict[str, str]] = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != _CASE_KEYS:
            raise ValueError("every case must contain only the documented two-source fields")
        if not all(isinstance(case[key], str) and case[key].strip() for key in _CASE_KEYS):
            raise ValueError("case fields must be non-empty strings")
        image_path = Path(case["image_path"])
        if image_path.suffix.lower() != ".png":
            raise ValueError("benchmark accepts only PNG raster inputs")
        if Path(case["case_id"]).name != case["case_id"]:
            raise ValueError("case_id must be a plain filename-safe identifier")
        normalized.append(case)
    ids = [case["case_id"] for case in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError("manifest contains duplicate case_id values")
    return seed, normalized


def _default_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "TINY_ICC_OUTPUT_VARIATION": "0",
        "PYTHONHASHSEED": "0",
    }
    return subprocess.run(command, check=False, capture_output=True, text=True, env=environment)


def _find_svg(output_dir: Path, stem: str) -> Path:
    matches = [
        path for path in output_dir.rglob(f"{stem}.svg")
        if "snapshot" not in str(path).lower()
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one result SVG for {stem}, found {len(matches)}")
    return matches[0]


def _normalized_svg_digest(path: Path) -> str:
    """Hash SVG structure independently of insignificant XML formatting."""
    root = ET.fromstring(path.read_text(encoding="utf-8"))

    def normalize(element: ET.Element) -> tuple[Any, ...]:
        return (
            element.tag,
            tuple(sorted(element.attrib.items())),
            (element.text or "").strip(),
            tuple(normalize(child) for child in element),
        )

    encoded = json.dumps(normalize(root), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _write_description(path: Path, stem: str, description: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "Wurzelform", "Beschreibung"])
        writer.writerow([stem, stem, description])


def run_benchmark(
    manifest_path: Path,
    work_dir: Path,
    *,
    repetitions: int = 3,
    runner: RunCommand = _default_runner,
) -> dict[str, Any]:
    """Run each case three times, including a filename-invariance repetition."""
    if repetitions < 3:
        raise ValueError("at least three repetitions are required")
    seed, cases = _load_cases(manifest_path)
    work_dir.mkdir(parents=True, exist_ok=True)
    evaluations: list[dict[str, Any]] = []
    for case in cases:
        source = (manifest_path.parent / case["image_path"]).resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        runs: list[dict[str, Any]] = []
        for repetition in range(1, repetitions + 1):
            stem = case["case_id"] if repetition < repetitions else "renamed_input"
            run_root = work_dir / case["case_id"] / f"run-{repetition}"
            if run_root.exists():
                shutil.rmtree(run_root)
            input_dir, output_dir = run_root / "input", run_root / "output"
            input_dir.mkdir(parents=True)
            shutil.copyfile(source, input_dir / f"{stem}.png")
            description_path = run_root / "description.csv"
            _write_description(description_path, stem, case["semantic_description"])
            command = [
                sys.executable, "-m", "src.iCCModules.imageCompositeConverterCli",
                "--input-dir", str(input_dir), "--descriptions-path", str(description_path),
                "--output-dir", str(output_dir), "--execution-mode", "semantic-only",
                "--start", stem, "--end", stem, "--deterministic-order",
            ]
            completed = runner(command)
            run: dict[str, Any] = {
                "repetition": repetition,
                "renamed_input": stem != case["case_id"],
                "exit_code": completed.returncode,
            }
            if completed.returncode == 0:
                svg_path = _find_svg(output_dir, stem)
                run["svg_sha256"] = _sha256(svg_path)
                run["normalized_svg_sha256"] = _normalized_svg_digest(svg_path)
                run["quality"] = evaluate_quality(source, svg_path, case["topology"])
            else:
                run["error"] = (completed.stderr or completed.stdout).strip()[-2000:]
            runs.append(run)
        normalized_digests = [run.get("normalized_svg_sha256") for run in runs]
        stable = None not in normalized_digests and len(set(normalized_digests)) == 1
        evaluations.append({
            "case_id": case["case_id"],
            "topology": case["topology"],
            "stable": stable,
            "rename_invariant": stable and runs[-1]["renamed_input"],
            "inputs": {
                "allowed_sources": ["png", "semantic_description"],
                "image_sha256": _sha256(source),
                "description_sha256": hashlib.sha256(case["semantic_description"].encode()).hexdigest(),
            },
            "runs": runs,
            "quality": runs[0].get("quality"),
        })
    stable_count = sum(item["stable"] for item in evaluations)
    return {
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "input_contract": {
            "allowed_sources": ["png", "semantic_description"],
            "execution_mode": "semantic-only",
            "forbidden_sources": ["reference_svg", "sample_svg", "bestlist", "template_donor"],
        },
        "repetitions": repetitions,
        "summary": {
            "sample_count": len(evaluations), "stable_count": stable_count,
            "unstable_count": len(evaluations) - stable_count,
            "passed": stable_count == len(evaluations),
        },
        "evaluations": evaluations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        report = run_benchmark(args.manifest, args.work_dir, repetitions=args.repetitions)
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError, RuntimeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
