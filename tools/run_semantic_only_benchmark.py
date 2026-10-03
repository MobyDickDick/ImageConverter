#!/usr/bin/env python3
"""Run the versioned JPEG + description benchmark without catalog knowledge."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir
from tools.evaluate_good_solution_gate import _raster_dimensions
from tools.filename_invariance import normalize_geometry_ir, normalize_svg_geometry


SCHEMA_VERSION = "semantic_only_benchmark_v1"
ALLOWED_CASE_KEYS = {"case_id", "image_path", "semantic_description", "primitive_families"}


def _digest(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def run_benchmark(manifest_path: Path, *, repeats: int = 3) -> dict[str, Any]:
    """Render every two-source case repeatedly and report deterministic output."""
    if repeats < 2:
        raise ValueError("repeats must be at least 2")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"expected schema_version {SCHEMA_VERSION}")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("manifest must contain at least one case")

    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) - ALLOWED_CASE_KEYS:
            raise ValueError("benchmark cases may contain only JPEG, description and classification metadata")
        case_id = str(case.get("case_id", "")).strip()
        description = str(case.get("semantic_description", "")).strip()
        if not case_id or case_id in seen_ids or not description:
            raise ValueError("case_id must be unique and semantic_description must be non-empty")
        seen_ids.add(case_id)
        image_path = (manifest_path.parent / str(case.get("image_path", ""))).resolve()
        if image_path.suffix.lower() not in {".jpg", ".jpeg"} or not image_path.is_file():
            raise ValueError(f"case {case_id}: image_path must reference an existing JPEG")
        width, height = _raster_dimensions(image_path)

        output_hashes: list[str] = []
        ir_hashes: list[str] = []
        for _alias_index in range(repeats):
            ir = geometry_ir.buildGeometryIrFromDescriptionImpl(description)
            if not ir:
                raise ValueError(f"case {case_id}: description produced no Geometry-IR")
            svg = geometry_ir.renderGeometryIrToSvgImpl(width, height, ir)
            ir_hashes.append(_digest(normalize_geometry_ir(ir)))
            output_hashes.append(_digest(normalize_svg_geometry(svg)))
        stable = len(set(ir_hashes)) == len(set(output_hashes)) == 1
        results.append({
            "case_id": case_id,
            "inputs": {
                "image_sha256": _digest(image_path.read_bytes()),
                "description_sha256": _digest(description),
                "width": width,
                "height": height,
            },
            "primitive_families": list(case.get("primitive_families", [])),
            "geometry_ir_sha256": ir_hashes[0],
            "svg_sha256": output_hashes[0],
            "repeat_count": repeats,
            "stable": stable,
        })

    family_count = len({family for result in results for family in result["primitive_families"]})
    stable_count = sum(result["stable"] for result in results)
    return {
        "schema_version": SCHEMA_VERSION,
        "assessment_scope": "description_render_determinism",
        "quality_assessed": False,
        "satisfactory": None,
        "source_manifest": str(manifest_path),
        "input_contract": ["jpeg", "semantic_description"],
        "case_count": len(results),
        "primitive_family_count": family_count,
        "stable_count": stable_count,
        "status": "pass" if stable_count == len(results) else "fail",
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = run_benchmark(args.manifest, repeats=args.repeats)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
