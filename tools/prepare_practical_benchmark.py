"""Prepare exposed development candidates and audited CLI pilots, not a final study.

Only archived raster bytes and descriptions enter the input directory. Reference
vectors and object/relationship annotations never enter conversion inputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SELECTION = ROOT / "config/practical_benchmark_candidates.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def contained(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Path escapes its data root: " + relative)
    return path


def runtime_hashes() -> dict:
    # Include tracked configuration/model resources as well as Python modules.
    paths = subprocess.check_output(["git", "ls-files", "src", "config"], cwd=ROOT, text=True).splitlines()
    return {name: digest(ROOT / name) for name in paths}


def prepare(output: Path, selection_path: Path = DEFAULT_SELECTION, *, archive: Path | None = None) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError("Preparation output already exists: " + str(output))
    from PIL import Image
    archive = archive or ROOT / "artifacts/satisfactory_conversions"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    index = json.loads((archive / "index.json").read_text(encoding="utf-8"))
    by_variant = {row["variant"]: row for row in index["cases"]}
    chosen = selection["cases"]
    if (not chosen or len({c["family"] for c in chosen}) != len(chosen)
            or len({c["variant"] for c in chosen}) != len(chosen)):
        raise ValueError("Use distinct candidate families and variants")
    subset = selection["manual_time_subset"]
    if len(set(subset)) != len(subset) or not set(subset) <= {c["family"] for c in chosen}:
        raise ValueError("Invalid manual-time subset")
    missing = sorted({choice["variant"] for choice in chosen} - by_variant.keys())
    if missing:
        raise ValueError("Benchmark candidates missing from archive index: " + ", ".join(missing))
    # Check all sources before creating any study files. Never read archive SVGs.
    for choice in chosen:
        row = by_variant[choice["variant"]]
        if digest(contained(archive, row["image"])) != row["image_sha256"]:
            raise ValueError("Archive raster changed: " + row["variant"])
    output.mkdir(parents=True, exist_ok=False)
    (output / "inputs").mkdir()
    rows = []
    for number, choice in enumerate(chosen):
        row = by_variant[choice["variant"]]
        source = contained(archive, row["image"])
        case_id = f"case_{number:02d}"
        target = output / "inputs" / (case_id + source.suffix.lower())
        shutil.copyfile(source, target)
        with Image.open(target) as image:
            width, height = image.size
        rows.append(dict(choice, case_id=case_id, split="known_development", taxonomy_review="pending",
                         annotation_review="pending", source_image=row["image"],
                         source_sha256=row["image_sha256"], image=target.relative_to(output).as_posix(),
                         input_sha256=digest(target), width=width, height=height,
                         description=row["description"], description_origin="existing_acceptance_archive",
                         description_sha256=hashlib.sha256(row["description"].encode("utf-8")).hexdigest(),
                         prior_evidence=row["evidence"], historical_execution_mode=row["execution_mode"]))
    manifest = dict(schema="practical_benchmark_preparation_v1", status="development_candidates_only", cases=rows,
                    selection_sha256=digest(selection_path), archive_index_sha256=digest(archive / "index.json"),
                    runtime_sha256=runtime_hashes(),
                    git_revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
    write_json(output / "manifest.json", manifest)
    write_json(output / "annotations.template.json", {r["case_id"]: dict(
        objects=None, relationships=None, expected_text=None, reviewer=None, reviewed=False) for r in rows})
    methods = ["converter", "contour_pending", "structured_pending", "manual_redraw"]
    with (output / "manual_times.template.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["family", "case_id", "method", "order", "operator", "inspection_seconds",
                         "description_seconds", "editing_seconds", "accepted", "evidence", "practice_notes"])
        for number, family in enumerate(subset):
            case = next(r for r in rows if r["family"] == family)
            # Rotate order for the same operator; replicate with more operators
            # and reverse order in the actual study. Empty times are not zeros.
            for position in range(len(methods)):
                writer.writerow([family, case["case_id"], methods[(number + position) % len(methods)],
                                 position + 1, "", "", "", "", "", "", ""])
    files = [p for p in output.rglob("*") if p.is_file()]
    write_json(output / "freeze.json", {p.relative_to(output).as_posix(): digest(p) for p in files})
    return verify(output)


def verify(output: Path) -> dict:
    frozen = json.loads((output / "freeze.json").read_text(encoding="utf-8"))
    if "manifest.json" not in frozen:
        raise ValueError("Missing frozen manifest")
    for name, expected in frozen.items():
        if digest(contained(output, name)) != expected:
            raise ValueError("Frozen preparation changed: " + name)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    cases = manifest["cases"]
    ids = [r["case_id"] for r in cases]
    families = [r["family"] for r in cases]
    if not cases or len(set(ids)) != len(ids) or len(set(families)) != len(families):
        raise ValueError("Empty or duplicate candidates")
    for case in cases:
        name = case["case_id"]
        if not name or not all(c.isascii() and (c.isalnum() or c == "_") for c in name):
            raise ValueError("Unsafe case ID")
        if case["split"] != "known_development":
            raise ValueError("Archive candidates cannot be relabeled as unseen holdouts")
        if digest(contained(output, case["image"])) != case["input_sha256"]:
            raise ValueError("Input hash mismatch")
        if hashlib.sha256(case["description"].encode("utf-8")).hexdigest() != case["description_sha256"]:
            raise ValueError("Description hash mismatch")
    return dict(candidate_cases=len(cases), provisional_families=len(set(families)),
                independently_reviewed_families=0, sealed_test_families=0, study_ready=False,
                blockers=["independent_taxonomy_and_object_annotations", "new_sealed_real_families",
                          "two_versioned_external_methods_and_development_only_settings",
                          "measured_human_editing_and_redraw_times"])


def pilot(prepared: Path, output: Path, case_ids: list[str], budget: float = 5.) -> dict:
    import math
    import time
    from tools.run_plan_b_variations import run_case
    verify(prepared)
    manifest = json.loads((prepared / "manifest.json").read_text(encoding="utf-8"))
    if runtime_hashes() != manifest["runtime_sha256"]:
        raise ValueError("Runtime/configuration differs from preparation freeze")
    by_id = {r["case_id"]: r for r in manifest["cases"]}
    if not case_ids or len(set(case_ids)) != len(case_ids) or not set(case_ids) <= by_id.keys():
        raise ValueError("Select distinct prepared case IDs")
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("Budget must be positive and finite")
    output.mkdir(parents=True, exist_ok=False)
    records = []
    started = time.monotonic()
    for case_id in case_ids:
        case = by_id[case_id]
        inputs = output / case_id / "input"
        inputs.mkdir(parents=True)
        # The existing runner consumes neutral PNG names. Decode once, outside
        # conversion timing; record both JPEG and decoded PNG hashes.
        import cv2
        pixels = cv2.imread(str(contained(prepared, case["image"])))
        image = inputs / (case_id + ".png")
        if pixels is None or not cv2.imwrite(str(image), pixels):
            raise ValueError("Could not prepare decoded raster")
        table = ET.Element("root")
        entry = ET.SubElement(table, "entry")
        ET.SubElement(entry, "beschreibung").text = case["description"]
        ET.SubElement(ET.SubElement(entry, "bilder"), "bild").text = image.name
        ET.ElementTree(table).write(inputs / "descriptions.xml", encoding="utf-8", xml_declaration=True)
        result = run_case(dict(case_id=case_id, width=case["width"], height=case["height"],
                               description=case["description"]), output, timeout=budget + 30, iterations=64,
                          extra_cli_args=("--search-seconds", str(budget), "--search-max-seconds", str(budget),
                                          "--search-seed", "17"))
        result.update(pixel_satisfactory=result.pop("satisfactory"), accepted=False,
                      semantic_review="pending", family=case["family"], split=case["split"],
                      source_sha256=case["source_sha256"], input_sha256=digest(image))
        records.append(result)
    audits = {}
    for path in sorted(output.rglob("*reference_access.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        if report["blocked_svg_reads"]:
            raise ValueError("Forbidden reference SVG read")
        audits[path.relative_to(output).as_posix()] = digest(path)
    if any(not (output / c / "reference_access.json").exists() for c in case_ids):
        raise ValueError("Missing reference-access audit")
    if runtime_hashes() != manifest["runtime_sha256"]:
        raise ValueError("Runtime/configuration changed during pilot")
    from importlib.metadata import version
    report = dict(status="development_pilot_only", study_ready=False, attempts=len(records), selected_case_ids=case_ids,
                  budget_seconds=budget, seed=17,
                  accepted=0, elapsed_seconds=time.monotonic() - started, records=records,
                  preparation_freeze_sha256=digest(prepared / "freeze.json"), reference_access=audits,
                  environment=dict(python=sys.version, platform=platform.platform(), processor=platform.processor(),
                                   cpu_count=os.cpu_count(), packages={name: version(name) for name in
                                       ("numpy", "opencv-python-headless", "Pillow", "PyMuPDF")}),
                  runtime_sha256=manifest["runtime_sha256"])
    write_json(output / "pilot.json", report)
    return verify_pilot(prepared, output)


def verify_pilot(prepared: Path, output: Path) -> dict:
    """Re-render every saved pilot vector; do not trust saved acceptance flags."""
    import cv2
    import numpy as np
    from tools.run_plan_b_variations import measure_quality
    verify(prepared)
    manifest = json.loads((prepared / "manifest.json").read_text(encoding="utf-8"))
    cases = {c["case_id"]: c for c in manifest["cases"]}
    report = json.loads((output / "pilot.json").read_text(encoding="utf-8"))
    if (report["preparation_freeze_sha256"] != digest(prepared / "freeze.json")
            or report["runtime_sha256"] != manifest["runtime_sha256"]):
        raise ValueError("Pilot provenance mismatch")
    records = report["records"]
    ids = [r["case_id"] for r in records]
    if (not ids or ids != report["selected_case_ids"] or len(set(ids)) != len(ids)
            or not set(ids) <= cases.keys() or report["attempts"] != len(ids)):
        raise ValueError("Incomplete or duplicate pilot records")
    if report["accepted"] != 0 or report["study_ready"] or report["status"] != "development_pilot_only":
        raise ValueError("Pilot cannot assert full study acceptance")
    expected_audits = {p.relative_to(output).as_posix() for p in output.rglob("*reference_access.json")}
    if expected_audits != set(report["reference_access"]):
        raise ValueError("Reference-access audit inventory mismatch")
    for name, expected in report["reference_access"].items():
        path = contained(output, name)
        if digest(path) != expected or json.loads(path.read_text(encoding="utf-8"))["blocked_svg_reads"]:
            raise ValueError("Invalid reference-access audit")
    passes = 0
    for row in records:
        case = cases[row["case_id"]]
        inputs = output / row["case_id"] / "input"
        image = inputs / (row["case_id"] + ".png")
        if (row["accepted"] or row["semantic_review"] != "pending" or row["split"] != "known_development"
                or row["family"] != case["family"] or row["description"] != case["description"]
                or row["source_sha256"] != case["source_sha256"] or digest(image) != row["input_sha256"]):
            raise ValueError("Pilot input or semantic decision mismatch")
        original = cv2.imread(str(contained(prepared, case["image"])))
        pixels = cv2.imread(str(image))
        if pixels is None or not np.array_equal(original, pixels):
            raise ValueError("Decoded pilot pixels differ from frozen original")
        description = ET.parse(inputs / "descriptions.xml").find(".//beschreibung")
        if description is None or description.text != case["description"]:
            raise ValueError("CLI description differs from frozen description")
        if not (output / row["case_id"] / "reference_access.json").exists():
            raise ValueError("Missing CLI reference-access audit")
        passed = False
        if row.get("output_svg"):
            path = contained(output, row["output_svg"])
            if digest(path) != row["output_sha256"]:
                raise ValueError("Pilot SVG changed")
            quality = measure_quality(pixels, path.read_text(encoding="utf-8"))
            passed = bool(row.get("returncode") == 0 and quality["satisfactory"])
            control_path = output / row["case_id"] / "conversion/reports" / (row["case_id"] + "_deadline.json")
            if passed:
                control = json.loads(control_path.read_text(encoding="utf-8"))
                if (not control.get("isolated") or control.get("limit_seconds") != report["budget_seconds"]
                        or control.get("max_seconds") != report["budget_seconds"]):
                    raise ValueError("Fixed supervised pilot budget was not applied")
        if passed != row["pixel_satisfactory"]:
            raise ValueError("Saved pixel decision differs from independent measurement")
        passes += passed
    return dict(attempts=len(records), pixel_passes=passes, accepted=0,
                semantic_review="pending", study_ready=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", type=Path)
    action.add_argument("--verify", type=Path)
    action.add_argument("--pilot", type=Path, help="Prepared inputs for a converter-only development pilot")
    action.add_argument("--verify-pilot", type=Path)
    parser.add_argument("--prepared", type=Path, help="Frozen preparation for --verify-pilot")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cases", nargs="+", default=["case_00", "case_07"])
    parser.add_argument("--budget", type=float, default=5.)
    args = parser.parse_args()
    if args.pilot and not args.output:
        parser.error("--pilot requires a new --output directory")
    if args.verify_pilot and not args.prepared:
        parser.error("--verify-pilot requires --prepared")
    if args.prepare:
        result = prepare(args.prepare)
    elif args.verify:
        result = verify(args.verify)
    elif args.verify_pilot:
        result = verify_pilot(args.prepared, args.verify_pilot)
    else:
        result = pilot(args.pilot, args.output, args.cases, args.budget)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
