from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.run_semantic_only_benchmark import SCHEMA_VERSION, run_benchmark


def test_repository_benchmark_is_representative_and_stable() -> None:
    report = run_benchmark(Path("config/semantic_only_benchmark_v1.json"), repeats=2)

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["assessment_scope"] == "description_render_determinism"
    assert report["quality_assessed"] is False
    assert report["satisfactory"] is None
    assert report["input_contract"] == ["jpeg", "semantic_description"]
    assert report["case_count"] == report["stable_count"] == 5
    assert report["primitive_family_count"] >= 5
    assert report["status"] == "pass"
    assert all(case["inputs"]["image_sha256"] for case in report["cases"])


def test_benchmark_rejects_an_additional_knowledge_source(tmp_path: Path) -> None:
    image = Path("artifacts/images_to_convert/AC0120_L.jpg").resolve()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "cases": [{
            "case_id": "invalid",
            "image_path": str(image),
            "semantic_description": "Linie",
            "template_svg": "hidden.svg",
        }],
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="only JPEG"):
        run_benchmark(manifest)
