from __future__ import annotations

import os

from src import imageCompositeConverterSemanticHarmonization as semantic_harmonization_helpers


def test_needs_large_circle_overflow_guard_requires_large_co2_circle_without_connectors() -> None:
    assert semantic_harmonization_helpers.needsLargeCircleOverflowGuardImpl(
        {
            "circle_enabled": True,
            "draw_text": True,
            "text_mode": "co2",
            "template_circle_radius": 12.0,
            "arm_enabled": False,
            "stem_enabled": False,
        }
    )
    assert not semantic_harmonization_helpers.needsLargeCircleOverflowGuardImpl(
        {
            "circle_enabled": True,
            "draw_text": True,
            "text_mode": "co2",
            "template_circle_radius": 8.0,
            "arm_enabled": True,
            "stem_enabled": False,
        }
    )


def test_family_harmonized_badge_colors_boosts_contrast_and_caps_text_stem() -> None:
    colors = semantic_harmonization_helpers.familyHarmonizedBadgeColorsImpl(
        [
            {"params": {"fill_gray": 140, "stroke_gray": 120, "text_gray": 110, "stem_gray": 130}},
            {"params": {"fill_gray": 138, "stroke_gray": 118, "text_gray": 115, "stem_gray": 116}},
        ]
    )

    assert colors["fill_gray"] > colors["stroke_gray"]
    assert colors["text_gray"] <= colors["stroke_gray"]
    assert colors["stem_gray"] <= colors["stroke_gray"]


def test_scale_badge_params_enables_overflow_for_large_centered_co2_circle() -> None:
    scaled = semantic_harmonization_helpers.scaleBadgeParamsImpl(
        {
            "circle_enabled": True,
            "cx": 15.0,
            "cy": 15.0,
            "r": 12.0,
            "stroke_circle": 1.0,
            "draw_text": True,
            "text_mode": "co2",
            "arm_enabled": False,
            "stem_enabled": False,
        },
        anchor_w=30,
        anchor_h=30,
        target_w=40,
        target_h=40,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        needs_large_circle_overflow_guard_fn=semantic_harmonization_helpers.needsLargeCircleOverflowGuardImpl,
    )

    assert scaled["allow_circle_overflow"] is True
    assert float(scaled["circle_radius_lower_bound_px"]) >= 20.5


def test_harmonize_semantic_size_variants_writes_catalog_and_harmonized_svg(tmp_path) -> None:
    folder_path = str(tmp_path / "images")
    svg_out_dir = str(tmp_path / "svg")
    reports_out_dir = str(tmp_path / "reports")
    os.makedirs(folder_path)
    os.makedirs(svg_out_dir)
    os.makedirs(reports_out_dir)

    results = [
        {"base": "AC9999", "variant": "AC9999_L", "filename": "AC9999_L.jpg", "error": 2.0},
        {"base": "AC9999", "variant": "AC9999_M", "filename": "AC9999_M.jpg", "error": 2.0},
    ]

    class _Cv2Stub:
        @staticmethod
        def imread(_path):
            return object()

    def _read_svg_geometry(_path: str):
        return 30, 30, {"draw_text": False, "stem_enabled": False, "arm_enabled": False}

    semantic_harmonization_helpers.harmonizeSemanticSizeVariantsImpl(
        results=results,
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        read_svg_geometry_fn=_read_svg_geometry,
        normalized_geometry_signature_fn=lambda _w, _h, _params: {"cx": 0.5},
        max_signature_delta_fn=lambda _a, _b: 0.0,
        harmonization_anchor_priority_fn=lambda suffix, _prefer_large: {"L": 0, "M": 1}.get(suffix, 2),
        family_harmonized_badge_colors_fn=lambda _rows: {
            "fill_gray": 200,
            "stroke_gray": 120,
            "text_gray": 110,
            "stem_gray": 110,
        },
        scale_badge_params_fn=lambda _a, _aw, _ah, _tw, _th, **_kwargs: {"draw_text": False, "stem_enabled": False},
        generate_badge_svg_fn=lambda _w, _h, _params: "<svg/>",
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        calculate_error_fn=lambda _target, _rendered: 1.0,
        cv2_module=_Cv2Stub(),
    )

    assert (tmp_path / "svg" / "AC9999_L.svg").read_text(encoding="utf-8") == "<svg/>"
    assert (tmp_path / "svg" / "AC9999_M.svg").read_text(encoding="utf-8") == "<svg/>"
    catalog_path = tmp_path / "reports" / "shape_catalog.csv"
    assert catalog_path.exists()
    catalog_text = catalog_path.read_text(encoding="utf-8")
    assert "prototype_group" in catalog_text
    assert "geometry_signature_delta" in catalog_text
    assert "text_orientation_policy" in catalog_text
    assert (tmp_path / "reports" / "variant_harmonization.log").exists()


def test_harmonize_semantic_size_variants_uses_cross_family_prototype_anchor(tmp_path) -> None:
    folder_path = str(tmp_path / "images")
    svg_out_dir = str(tmp_path / "svg")
    reports_out_dir = str(tmp_path / "reports")
    os.makedirs(folder_path)
    os.makedirs(svg_out_dir)
    os.makedirs(reports_out_dir)

    results = [
        {"base": "AC0811", "variant": "AC0811_L", "filename": "AC0811_L.jpg", "error": 1.0},
        {"base": "AC0811", "variant": "AC0811_M", "filename": "AC0811_M.jpg", "error": 1.1},
        {"base": "AC0831", "variant": "AC0831_L", "filename": "AC0831_L.jpg", "error": 5.0},
        {"base": "AC0831", "variant": "AC0831_M", "filename": "AC0831_M.jpg", "error": 5.1},
    ]

    class _Cv2Stub:
        @staticmethod
        def imread(_path):
            return object()

    def _read_svg_geometry(path: str):
        variant = os.path.splitext(os.path.basename(path))[0]
        return 30, 30, {"draw_text": False, "stem_enabled": True, "arm_enabled": False, "variant": variant}

    scale_calls: list[str] = []

    def _scale(_a, _aw, _ah, _tw, _th, **_kwargs):
        scale_calls.append(str(_a.get("variant")))
        return {"draw_text": False, "stem_enabled": True}

    semantic_harmonization_helpers.harmonizeSemanticSizeVariantsImpl(
        results=results,
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        read_svg_geometry_fn=_read_svg_geometry,
        normalized_geometry_signature_fn=lambda _w, _h, _params: {"cx": 0.5},
        max_signature_delta_fn=lambda _a, _b: 0.0,
        harmonization_anchor_priority_fn=lambda suffix, _prefer_large: {"L": 0, "M": 1}.get(suffix, 2),
        family_harmonized_badge_colors_fn=lambda _rows: {
            "fill_gray": 200,
            "stroke_gray": 120,
            "text_gray": 110,
            "stem_gray": 110,
        },
        scale_badge_params_fn=_scale,
        generate_badge_svg_fn=lambda _w, _h, _params: "<svg/>",
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        calculate_error_fn=lambda _target, _rendered: 1.0,
        cv2_module=_Cv2Stub(),
    )

    assert any(call.startswith("AC0811_") for call in scale_calls)
