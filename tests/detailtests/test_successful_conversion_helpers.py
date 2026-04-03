from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterSuccessfulConversions as success_helpers


def test_parse_successful_conversion_manifest_line_parses_metrics() -> None:
    variant, metrics = success_helpers.parseSuccessfulConversionManifestLineImpl(
        "ac0800_s ; status=semantic_ok ; mean_delta2=1,25 ; pixel_count=42 # note"
    )

    assert variant == "AC0800_S"
    assert metrics["status"] == "semantic_ok"
    assert metrics["mean_delta2"] == 1.25
    assert metrics["pixel_count"] == 42


def test_is_candidate_better_prefers_semantic_ok() -> None:
    previous = {"status": "semantic_mismatch", "mean_delta2": 0.1}
    candidate = {"status": "semantic_ok", "mean_delta2": 5.0}

    better = success_helpers.isSuccessfulConversionCandidateBetterImpl(
        previous_metrics=previous,
        candidate_metrics=candidate,
        metrics_available_fn=lambda m: bool(m),
        evaluate_candidate_fn=lambda _p, _c: (False, "", 0.0, 0.0, 0.0, 0.0),
    )

    assert better is True


def test_format_manifest_line_keeps_comment_and_appends_metrics() -> None:
    line = "AC0800_S # baseline"
    metrics = {"variant": "AC0800_S", "status": "semantic_ok", "mean_delta2": 1.2, "pixel_count": 11}

    rendered = success_helpers.formatSuccessfulConversionManifestLineImpl(
        existing_line=line,
        metrics=metrics,
        metrics_available_fn=lambda m: bool(m),
    )

    assert "status=semantic_ok" in rendered
    assert "mean_delta2=1.200000" in rendered
    assert "pixel_count=11" in rendered
    assert rendered.endswith("# baseline")


def test_store_and_restore_successful_snapshot_roundtrip(tmp_path: Path) -> None:
    svg_out = tmp_path / "svg"
    reports = tmp_path / "reports"
    svg_out.mkdir()
    reports.mkdir()
    variant = "AC0800_S"

    (svg_out / f"{variant}.svg").write_text("<svg>new</svg>", encoding="utf-8")
    (reports / f"{variant}_element_validation.log").write_text("status=semantic_ok", encoding="utf-8")

    success_helpers.storeSuccessfulConversionSnapshotImpl(
        variant=variant,
        metrics={"variant": variant, "status": "semantic_ok"},
        svg_out_dir=str(svg_out),
        reports_out_dir=str(reports),
    )

    (svg_out / f"{variant}.svg").write_text("<svg>changed</svg>", encoding="utf-8")
    restored = success_helpers.restoreSuccessfulConversionSnapshotImpl(
        variant=variant,
        svg_out_dir=str(svg_out),
        reports_out_dir=str(reports),
    )

    assert restored is True
    assert (svg_out / f"{variant}.svg").read_text(encoding="utf-8") == "<svg>new</svg>"
