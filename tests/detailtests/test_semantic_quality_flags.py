from __future__ import annotations

from pathlib import Path

import pytest

import src.imageCompositeConverter as image_composite_converter


def test_semantic_quality_flags_marks_ac0811_with_high_element_error() -> None:
    flags = image_composite_converter._semanticQualityFlags(
        "AC0811_L",
        [
            "circle: Fehler=4.200",
            "stem: Fehler=10.750",
            "text: Fehler=1.500",
        ],
    )

    assert "quality=borderline" in flags
    assert "quality_reason=semantic_ok_trotz_hohem_elementfehler:stem=10.750" in flags
    assert "quality_elevated_elements=stem" in flags


def test_semantic_quality_flags_ignores_non_ac0811_variants() -> None:
    flags = image_composite_converter._semanticQualityFlags(
        "AC0812_L",
        [
            "circle: Fehler=3.000",
            "arm: Fehler=12.000",
        ],
    )

    assert flags == []


def test_run_iteration_pipeline_logs_borderline_quality_for_ac0811(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2

    img = np.full((12, 20, 3), 240, dtype=np.uint8)
    img_path = tmp_path / "AC0811_L.jpg"
    csv_path = tmp_path / "data.csv"
    svg_dir = tmp_path / "svg"
    diff_dir = tmp_path / "diff"
    reports_dir = tmp_path / "reports"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0811;semantic\n", encoding="utf-8")
    assert cv2.imwrite(str(img_path), img)

    monkeypatch.setattr(
        image_composite_converter.Reflection,
        "parse_description",
        lambda *_args, **_kwargs: (
            "semantic",
            {"mode": "semantic_badge", "elements": ["SEMANTIC: Kreis mit Stiel"], "label": ""},
        ),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "make_badge_params",
        staticmethod(lambda *_args, **_kwargs: image_composite_converter.Action._default_ac0811_params(20, 12)),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "validate_semantic_description_alignment",
        staticmethod(lambda *_args, **_kwargs: []),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "validate_badge_by_elements",
        staticmethod(
            lambda *_args, **_kwargs: [
                "circle: Fehler=4.200",
                "stem: Fehler=10.750",
                "text: Fehler=1.500",
            ]
        ),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "generate_badge_svg",
        staticmethod(lambda w, h, _p: f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"/>'),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "render_svg_to_numpy",
        staticmethod(lambda _svg, w, h: np.full((h, w, 3), 245, dtype=np.uint8)),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "_enforce_semantic_connector_expectation",
        staticmethod(lambda *_args, **_kwargs: {"stem_enabled": True}),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "apply_redraw_variation",
        staticmethod(lambda params, _w, _h: (dict(params), ["redraw_variation: seed=123 changed_params=stem_width:1.000->1.050"])),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "calculate_error",
        staticmethod(lambda *_args, **_kwargs: 12.0),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "create_diff_image",
        staticmethod(lambda a, _b: a.copy()),
    )

    res = image_composite_converter.runIterationPipeline(
        str(img_path),
        str(csv_path),
        2,
        str(svg_dir),
        str(diff_dir),
        str(reports_dir),
    )

    assert res is not None
    log_text = (reports_dir / "AC0811_L_element_validation.log").read_text(encoding="utf-8")
    assert "status=semantic_ok" in log_text
    assert "quality=borderline" in log_text
    assert "quality_reason=semantic_ok_trotz_hohem_elementfehler:stem=10.750" in log_text
    assert "redraw_variation: seed=" in log_text


def test_write_ac08_weak_family_status_report_summarizes_ranked_outliers(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "pixel_delta2_ranking.csv").write_text(
        "image;mean_delta2;std_delta2\n"
        "AC0882_S.jpg;24.500000;1.200000\n"
        "AC0811_L.jpg;12.000000;0.800000\n",
        encoding="utf-8",
    )
    (reports_dir / "AC0882_S_element_validation.log").write_text(
        "adaptive_unlock_applied\nsmall_variant_mode_active\nstopped_due_to_stagnation\n",
        encoding="utf-8",
    )

    image_composite_converter._writeAc08WeakFamilyStatusReport(
        str(reports_dir),
        selected_variants=["AC0882_S", "AC0811_L"],
    )

    csv_text = (reports_dir / "ac08_weak_family_status.csv").read_text(encoding="utf-8")
    summary_text = (reports_dir / "ac08_weak_family_status.txt").read_text(encoding="utf-8")

    assert "AC0882_S;AC0882;stagnation;24.500000;high;left_connector" in csv_text
    assert "adaptive_unlock_applied,small_variant_mode_active,stagnation_guard_triggered" in csv_text
    assert "AC0811_L" not in csv_text
    assert "weak_variants=1" in summary_text
    assert "AC0882_S: mean_delta2=24.500000; risk=high" in summary_text


def test_write_ac08_weak_family_status_report_skips_non_ac08_selection(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    image_composite_converter._writeAc08WeakFamilyStatusReport(
        str(reports_dir),
        selected_variants=["GE0001_M"],
    )

    assert not (reports_dir / "ac08_weak_family_status.csv").exists()
    assert not (reports_dir / "ac08_weak_family_status.txt").exists()
