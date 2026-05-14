#!/usr/bin/env python3
"""Evaluate semantic roundtrip stability (Text -> SVG -> Raster -> back to semantic scene)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def object_index(scene: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {obj["id"]: obj for obj in scene.get("objects", []) if "id" in obj}


def relation_key(relation: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(relation.get("source", "")),
        str(relation.get("type", "")),
        str(relation.get("target", "")),
    )


def compare(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    ref_objects = object_index(reference)
    cand_objects = object_index(candidate)

    missing_objects = sorted(set(ref_objects) - set(cand_objects))
    extra_objects = sorted(set(cand_objects) - set(ref_objects))

    ref_relations = {relation_key(rel) for rel in reference.get("relations", [])}
    cand_relations = {relation_key(rel) for rel in candidate.get("relations", [])}

    missing_relations = sorted(ref_relations - cand_relations)
    extra_relations = sorted(cand_relations - ref_relations)

    invertibility_failures = []
    for rel in missing_relations:
        invertibility_failures.append(
            {
                "failure_mode": "relation_loss",
                "relation": {"source": rel[0], "type": rel[1], "target": rel[2]},
            }
        )

    for obj_id in missing_objects:
        invertibility_failures.append(
            {
                "failure_mode": "object_loss",
                "object_id": obj_id,
                "object_type": ref_objects[obj_id].get("type", "unknown"),
            }
        )

    passed = not missing_objects and not missing_relations
    return {
        "summary": {
            "passed": passed,
            "reference_objects": len(ref_objects),
            "candidate_objects": len(cand_objects),
            "missing_object_count": len(missing_objects),
            "extra_object_count": len(extra_objects),
            "missing_relation_count": len(missing_relations),
            "extra_relation_count": len(extra_relations),
        },
        "gaps": {
            "missing_objects": missing_objects,
            "extra_objects": extra_objects,
            "missing_relations": [
                {"source": src, "type": typ, "target": tgt}
                for src, typ, tgt in missing_relations
            ],
            "extra_relations": [
                {"source": src, "type": typ, "target": tgt}
                for src, typ, tgt in extra_relations
            ],
        },
        "invertibility_failures": invertibility_failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reference = load_json(args.reference)
    candidate = load_json(args.candidate)
    report = compare(reference, candidate)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"wrote semantic roundtrip report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
