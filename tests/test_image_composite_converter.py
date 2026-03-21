from __future__ import annotations

import contextlib
import sys
import shutil
from pathlib import Path

import pytest

import src.image_composite_converter as image_composite_converter
from src.image_composite_converter import Action, _clip

conv = image_composite_converter


def test_vendored_site_packages_dirs_discovers_repo_bundle() -> None:
    """Repo-local bundled site-packages should be discoverable for optional imports."""
    dirs = image_composite_converter._vendored_site_packages_dirs()

    assert any(path.as_posix().endswith(".venv/Lib/site-packages") for path in dirs)


def test_vendored_site_packages_dirs_discovers_vendor_linux_bundle(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Dedicated vendor/linux-py310 bundles should be discoverable without using .venv."""
    vendor_dir = tmp_path / "vendor" / "linux-py310" / "site-packages"
    vendor_dir.mkdir(parents=True)

    monkeypatch.setattr(image_composite_converter, "_optional_dependency_base_dir", lambda: tmp_path)

    dirs = image_composite_converter._vendored_site_packages_dirs()

    assert vendor_dir in dirs


def test_vendored_site_packages_dirs_prefers_linux_vendor_on_linux(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Linux vendor bundles should be attempted before Windows-style repo environments."""
    vendor_dir = tmp_path / "vendor" / "linux-py310" / "site-packages"
    venv_dir = tmp_path / ".venv" / "Lib" / "site-packages"
    vendor_dir.mkdir(parents=True)
    venv_dir.mkdir(parents=True)

    monkeypatch.setattr(image_composite_converter, "_optional_dependency_base_dir", lambda: tmp_path)

    dirs = image_composite_converter._vendored_site_packages_dirs()

    assert dirs.index(vendor_dir) < dirs.index(venv_dir)


def test_load_optional_module_recovers_after_failed_partial_package(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A failed import from one bundle must not poison the retry against the next bundle."""
    vendor_dir = tmp_path / "vendor" / "linux-py310" / "site-packages"
    windows_dir = tmp_path / ".venv" / "Lib" / "site-packages"
    vendor_dir.mkdir(parents=True)
    windows_dir.mkdir(parents=True)
    expected = object()
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_import(name: str):
        if name != "cv2":
            raise AssertionError(f"unexpected module request: {name}")
        calls.append((name, tuple(sys.path[:3])))
        if str(windows_dir) in sys.path and str(vendor_dir) not in sys.path:
            sys.modules["cv2"] = object()
            sys.modules["cv2.typing"] = object()
            raise ImportError("broken Windows wheel")
        if str(vendor_dir) in sys.path:
            assert "cv2" not in sys.modules
            assert "cv2.typing" not in sys.modules
            return expected
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(image_composite_converter, "_optional_dependency_base_dir", lambda: tmp_path)
    monkeypatch.setattr(image_composite_converter.importlib, "import_module", fake_import)

    result = image_composite_converter._load_optional_module("cv2")

    assert result is expected
    assert len(calls) >= 2

def test_optional_dependency_error_reports_windows_bundle_hint() -> None:
    """Dependency diagnostics should explain when a bundled Windows wheel is unusable on Linux."""
    message = image_composite_converter._describe_optional_dependency_error(
        "numpy",
        AttributeError("module 'os' has no attribute 'add_dll_directory'"),
        [Path(".venv/Lib/site-packages")],
    )

    assert "Windows-Build" in message
    assert "Linux-Umgebung" in message


def test_semantic_validation_accepts_circle_supported_by_local_mask(monkeypatch: pytest.MonkeyPatch) -> None:
    """Local ROI support should prevent false circle mismatches when Hough detection misses JPEG-soft rings."""
    if conv.np is None:
        pytest.skip("numpy not available in this environment")
    monkeypatch.setattr(conv.Action, "_detect_semantic_primitives", staticmethod(lambda _img: {"circle": False, "arm": False, "text": False}))
    monkeypatch.setattr(conv.Action, "_mask_bbox", staticmethod(lambda _mask: (2.0, 2.0, 7.0, 7.0)))
    monkeypatch.setattr(conv.Action, "_mask_centroid_radius", staticmethod(lambda _mask: (4.5, 4.5, 2.5)))

    circle_mask = conv.np.zeros((10, 10), dtype=bool)
    for y, x in [(2, 4), (3, 6), (5, 7), (7, 5), (6, 3), (4, 2)]:
        circle_mask[y, x] = True

    def fake_extract(_img, _params, element: str):
        return circle_mask if element == "circle" else None

    monkeypatch.setattr(conv.Action, "extract_badge_element_mask", staticmethod(fake_extract))

    issues = conv.Action.validate_semantic_description_alignment(
        conv.np.zeros((10, 10, 3), dtype=conv.np.uint8),
        ["SEMANTIC: Kreis mit grauem Rand"],
        {"cx": 4.5, "cy": 4.5, "r": 2.5},
    )

    assert issues == []


def test_mask_supports_circle_accepts_sparse_ring_samples() -> None:
    """Thin ring masks should still count as circle support during semantic validation."""
    if conv.np is None:
        pytest.skip("numpy not available in this environment")
    ring_mask = conv.np.zeros((12, 12), dtype=bool)
    for y, x in [(2, 5), (3, 8), (5, 9), (8, 7), (9, 5), (8, 3), (5, 2), (3, 3)]:
        ring_mask[y, x] = True

    assert conv.Action._mask_supports_circle(ring_mask) is True


def test_detect_semantic_primitives_detects_plain_ring_without_arm() -> None:
    """Small plain-circle badges should not hallucinate a horizontal arm."""
    if conv.cv2 is None or conv.np is None:
        pytest.skip("opencv/numpy not available in this environment")

    img = conv.cv2.imread("artifacts/images_to_convert/AC0800_M.jpg")
    assert img is not None

    observed = conv.Action._detect_semantic_primitives(img)

    assert observed["circle"] is True
    assert observed["arm"] is False
    assert observed["text"] is False


def test_foreground_mask_keeps_tiny_plain_ring_pixels() -> None:
    """Foreground extraction should preserve faint anti-aliased ring strokes."""
    if conv.cv2 is None or conv.np is None:
        pytest.skip("opencv/numpy not available in this environment")

    img = conv.cv2.imread("artifacts/images_to_convert/AC0800_M.jpg")
    assert img is not None

    fg = conv.Action._foreground_mask(img)

    assert int(conv.np.count_nonzero(fg)) >= 20
    assert conv.Action._circle_from_foreground_mask(fg) is not None


def test_semantic_validation_accepts_text_supported_by_local_mask(monkeypatch: pytest.MonkeyPatch) -> None:
    """Text badges should pass semantic validation when the text ROI contains enough local foreground support."""
    if conv.np is None:
        pytest.skip("numpy not available in this environment")
    monkeypatch.setattr(conv.Action, "_detect_semantic_primitives", staticmethod(lambda _img: {"circle": False, "arm": False, "text": False}))
    monkeypatch.setattr(conv.Action, "_mask_bbox", staticmethod(lambda _mask: (1.0, 1.0, 8.0, 5.0)))

    text_mask = conv.np.zeros((10, 10), dtype=bool)
    text_mask[1:6, 2:4] = True
    text_mask[2:5, 6:9] = True

    def fake_extract(_img, _params, element: str):
        return text_mask if element == "text" else None

    monkeypatch.setattr(conv.Action, "extract_badge_element_mask", staticmethod(fake_extract))

    issues = conv.Action.validate_semantic_description_alignment(
        conv.np.zeros((10, 10, 3), dtype=conv.np.uint8),
        ["SEMANTIC: waagrecht geschriebenem Buchstaben \"VOC\""],
        {"draw_text": True, "text_mode": "voc"},
    )

    assert issues == []


def test_source_loads_numpy_before_cv2() -> None:
    """cv2 must be initialized after numpy so vendored OpenCV can resolve its dependency."""
    source = Path(image_composite_converter.__file__).read_text(encoding="utf-8")

    numpy_pos = source.index('np = _load_optional_module("numpy")')
    cv2_pos = source.index('cv2 = _load_optional_module("cv2")')

    assert numpy_pos < cv2_pos


def test_family_harmonized_badge_colors_averages_family_palette() -> None:
    """L/M/S families should use averaged grayscale values as harmonization base."""
    rows = [
        {"params": {"fill_gray": 220, "stroke_gray": 150, "text_gray": 148}},
        {"params": {"fill_gray": 230, "stroke_gray": 160, "text_gray": 156}},
        {"params": {"fill_gray": 210, "stroke_gray": 140, "text_gray": 138}},
    ]

    colors = conv._family_harmonized_badge_colors(rows)

    assert colors["fill_gray"] > colors["stroke_gray"]
    assert colors["text_gray"] <= colors["stroke_gray"]
    assert 215 <= colors["fill_gray"] <= 225
    assert 145 <= colors["stroke_gray"] <= 155


def test_family_harmonized_badge_colors_boosts_low_contrast() -> None:
    """Family averaging should expand weak fill/stroke separation instead of preserving muddy contrast."""
    rows = [
        {"params": {"fill_gray": 205, "stroke_gray": 200}},
        {"params": {"fill_gray": 206, "stroke_gray": 201}},
    ]

    colors = conv._family_harmonized_badge_colors(rows)

    assert colors["fill_gray"] - colors["stroke_gray"] >= 18


def test_co2_label_defaults_use_center_co_anchor_mode() -> None:
    """Default CO₂ layout should keep center_co mode and only shift left if required."""
    params = Action._apply_co2_label(Action._default_ac0870_params(15, 15))
    layout = Action._co2_layout(params)

    assert layout["anchor_mode"] == "center_co"
    assert float(layout["co_x"]) <= float(params["cx"])
    assert float(params["co2_dx"]) == 0.0


def test_co2_layout_legacy_cluster_mode_still_supported() -> None:
    """Legacy cluster-centered mode should still shift CO left for the subscript."""
    params = Action._apply_co2_label(Action._default_ac0870_params(15, 15))
    params["co2_anchor_mode"] = "cluster"
    layout = Action._co2_layout(params)

    assert layout["anchor_mode"] == "cluster"
    assert float(layout["co_x"]) < float(params["cx"])


def test_finalize_ac0820_uses_cluster_anchor_mode() -> None:
    """AC0820 should center the full CO₂ cluster horizontally."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820", params)

    assert params["co2_anchor_mode"] == "cluster"


def test_finalize_ac0820_variant_name_uses_cluster_anchor_mode() -> None:
    """AC0820 variant names (e.g. AC0820_L) should center the full CO₂ label."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820_L", params)

    assert params["co2_anchor_mode"] == "cluster"
    assert float(params["co2_optical_bias"]) >= 0.125


def test_finalize_ac0800_keeps_ring_darker_than_fill() -> None:
    """AC0800 should preserve generic ring semantics: darker stroke than fill."""
    params = Action.make_badge_params(30, 30, "AC0800")

    assert params is not None
    assert float(params["r"]) == pytest.approx(10.8)
    assert int(params["stroke_gray"]) < int(params["fill_gray"])
    assert float(params["stroke_circle"]) >= 1.0


def test_generate_badge_svg_emits_background_rect_when_requested() -> None:
    """Badge SVG should include an explicit background rect when configured."""
    params = {
        "background_fill": "#ffffff",
        "circle_enabled": True,
        "cx": 15.0,
        "cy": 15.0,
        "r": 10.8,
        "fill_gray": 217,
        "stroke_gray": 128,
        "stroke_circle": 1.8,
        "draw_text": False,
    }

    svg = Action.generate_badge_svg(30, 30, params)

    assert '<rect x="0" y="0" width="30.0000" height="30.0000" fill="#ffffff"/>' in svg


def test_fit_semantic_badge_estimates_ring_style_for_plain_circle() -> None:
    """Plain circles should infer ring/center style from raster tones generically."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2
    if np is None or cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    img = np.full((30, 30, 3), 255, dtype=np.uint8)
    cv2.circle(img, (15, 15), 11, (128, 128, 128), thickness=2)
    cv2.circle(img, (15, 15), 10, (217, 217, 217), thickness=-1)

    defaults = {
        "cx": 15.0,
        "cy": 15.0,
        "r": 10.8,
        "stroke_circle": 1.5,
        "fill_gray": 220,
        "stroke_gray": 152,
        "draw_text": False,
    }

    fitted = Action._fit_semantic_badge_from_image(img, defaults)

    assert int(fitted["stroke_gray"]) < int(fitted["fill_gray"])
    assert float(fitted["stroke_circle"]) >= 1.0
    assert fitted.get("background_fill") == "#ffffff"


def test_parse_semantic_badge_layout_overrides_centers_full_co2_cluster() -> None:
    """Horizontal centering directive should target the full CO₂ cluster."""
    overrides = image_composite_converter.Reflection._parse_semantic_badge_layout_overrides(
        "CO_2 bezüglich des Kreises horizontal zentriert"
    )

    assert overrides["co2_anchor_mode"] == "cluster"
    assert float(overrides["co2_dx"]) == 0.0


def test_parse_description_marks_ac0833_with_right_horizontal_arm() -> None:
    """AC0833 belongs to the right-arm CO₂ family and must include that semantic element."""
    ref = image_composite_converter.Reflection({})

    _desc, params = ref.parse_description("AC0833", "AC0833_S.jpg")

    assert "SEMANTIC: waagrechter Strich rechts vom Kreis" in list(params.get("elements", []))


def test_parse_description_marks_ac0838_with_right_horizontal_arm() -> None:
    """AC0838 belongs to the right-arm VOC family and must include that semantic element."""
    ref = image_composite_converter.Reflection({})

    _desc, params = ref.parse_description("AC0838", "AC0838_L.jpg")

    assert "SEMANTIC: waagrechter Strich rechts vom Kreis" in list(params.get("elements", []))


def test_parse_description_does_not_misread_ac0130_text_as_top_source_ref() -> None:
    """AC0130 mentions 'oben mitte' and 'in beiden Diagonalen' but has no donor image reference."""
    raw = image_composite_converter._load_description_mapping(
        "artifacts/descriptions/Finale_Wurzelformen_V3.xml"
    )
    ref = image_composite_converter.Reflection(raw)

    _desc, params = ref.parse_description("AC0130", "AC0130.jpg")

    assert params["top_source_ref"] is None
    assert "OBEN: Geschnitten aus Originaldatei BEIDEN" not in list(params.get("elements", []))


def test_finalize_ac0820_locks_plain_circle_center_and_min_radius() -> None:
    """Plain AC0820 badges should keep a centered ring and preserve readable radius."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params = Action._finalize_ac08_style("AC0820", params)

    assert params["lock_circle_cx"] is True
    assert params["lock_circle_cy"] is True
    assert float(params["min_circle_radius"]) >= float(params["r"]) * 0.88


def test_finalize_ac0820_min_circle_radius_uses_template_baseline() -> None:
    """Radius floor should be anchored to template size, not a shrunken interim fit."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params["template_circle_radius"] = float(params["r"])
    params["r"] = 3.0

    params = Action._finalize_ac08_style("AC0820", params)

    assert float(params["min_circle_radius"]) >= float(params["template_circle_radius"]) * 0.92


def test_finalize_non_ac0820_text_badge_uses_less_strict_radius_floor() -> None:
    """Non-AC0820 text badges should preserve the previous 90%-template floor."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params["template_circle_radius"] = float(params["r"])
    params["r"] = 3.0

    params = Action._finalize_ac08_style("AC0831", params)

    assert float(params["min_circle_radius"]) >= float(params["template_circle_radius"]) * 0.90


def test_finalize_elongated_connector_badge_uses_stronger_radius_floor() -> None:
    """Strongly elongated connector badges should resist circle shrink during validation."""
    params = Action._default_ac0811_params(30, 45)
    params["template_circle_radius"] = float(params["r"])
    params["r"] = float(params["r"]) * 0.84

    params = Action._finalize_ac08_style("AC0811_L", params)

    assert float(params["min_circle_radius"]) >= float(params["template_circle_radius"]) * 0.95


def test_finalize_plain_ac08_badge_reanchors_circle_to_template_center() -> None:
    """Plain AC08xx badges should lock to template circle center, not drifted fit center."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params["template_circle_cx"] = 9.5
    params["template_circle_cy"] = 9.5
    params["cx"] = 8.0
    params["cy"] = 7.0

    params = Action._finalize_ac08_style("AC0820_M", params)

    assert float(params["cx"]) == 9.5
    assert float(params["cy"]) == 9.5


def test_fit_semantic_badge_records_template_center_for_finalize_locking() -> None:
    """Semantic fit should persist template center so finalize can restore canonical centering."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((20, 20, 3), 240, dtype=np.uint8)
    defaults = Action._default_ac0870_params(20, 20)

    params = Action._fit_semantic_badge_from_image(img, defaults)

    assert float(params["template_circle_cx"]) == float(defaults["cx"])
    assert float(params["template_circle_cy"]) == float(defaults["cy"])
def test_fit_semantic_badge_prevents_over_shrinking_plain_text_badge_circle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Circle fitting should keep a minimum template-relative radius for plain text badges."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2
    img = np.full((20, 20, 3), 220, dtype=np.uint8)

    defaults = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    default_r = float(defaults["r"])

    monkeypatch.setattr(
        cv2,
        "HoughCircles",
        lambda *_args, **_kwargs: np.array([[[10.0, 10.0, 2.0]]], dtype=np.float32),
    )

    fitted = Action._fit_semantic_badge_from_image(img, defaults)

    assert float(fitted["r"]) >= (default_r * 0.92) - 1e-6


def test_fit_semantic_badge_allows_lower_floor_when_connector_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """Connector badges should use a looser minimum-ratio floor than plain centered badges."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2
    img = np.full((20, 20, 3), 220, dtype=np.uint8)

    defaults = {
        "cx": 10.0,
        "cy": 10.0,
        "r": 6.0,
        "stroke_circle": 1.0,
        "fill_gray": 220,
        "stroke_gray": 152,
        "draw_text": False,
        "arm_enabled": True,
        "arm_x1": 1.0,
        "arm_y1": 10.0,
        "arm_x2": 4.0,
        "arm_y2": 10.0,
    }

    monkeypatch.setattr(
        cv2,
        "HoughCircles",
        lambda *_args, **_kwargs: np.array([[[10.0, 10.0, 2.0]]], dtype=np.float32),
    )

    fitted = Action._fit_semantic_badge_from_image(img, defaults)

    assert float(fitted["r"]) >= (float(defaults["r"]) * 0.80) - 1e-6


def test_make_badge_params_passes_text_semantics_into_connector_fit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Connector+text families must be fit with labeled defaults, not textless templates."""
    if image_composite_converter.np is None:
        pytest.skip("numpy not available in this environment")

    np = image_composite_converter.np
    img = np.full((20, 36, 3), 220, dtype=np.uint8)
    seen: list[dict] = []

    def fake_fit(_img, defaults):
        seen.append(dict(defaults))
        return dict(defaults)

    monkeypatch.setattr(Action, "_fit_ac0814_params_from_image", staticmethod(fake_fit))

    params = Action.make_badge_params(36, 20, "AC0834", img)

    assert params is not None
    assert seen, "fit helper should be called"
    assert seen[0]["draw_text"] is True
    assert seen[0]["text_mode"] == "co2"


def test_make_badge_params_passes_voc_semantics_into_vertical_fit(monkeypatch: pytest.MonkeyPatch) -> None:
    """VOC connector families must preserve text-aware defaults during image fitting."""
    if image_composite_converter.np is None:
        pytest.skip("numpy not available in this environment")

    np = image_composite_converter.np
    img = np.full((30, 20, 3), 220, dtype=np.uint8)
    seen: list[dict] = []

    def fake_fit(_img, defaults):
        seen.append(dict(defaults))
        return dict(defaults)

    monkeypatch.setattr(Action, "_fit_ac0811_params_from_image", staticmethod(fake_fit))

    params = Action.make_badge_params(20, 30, "AC0836", img)

    assert params is not None
    assert seen, "fit helper should be called"
    assert seen[0]["draw_text"] is True
    assert seen[0]["text_mode"] == "voc"


def test_fit_semantic_badge_rejects_far_off_hough_center_for_ac08_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hough candidates far from template center should not override semantic circle placement."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2
    img = np.full((15, 25, 3), 220, dtype=np.uint8)

    defaults = Action._default_ac0812_params(25, 15)

    monkeypatch.setattr(
        cv2,
        "HoughCircles",
        lambda *_args, **_kwargs: np.array([[[6.0, 9.0, 4.4]]], dtype=np.float32),
    )

    fitted = Action._fit_semantic_badge_from_image(img, defaults)

    assert abs(float(fitted["cx"]) - float(defaults["cx"])) <= 1e-6
    assert abs(float(fitted["cy"]) - float(defaults["cy"])) <= 1e-6


def test_fit_semantic_badge_keeps_near_template_hough_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    """A near-template Hough hit should still be accepted and applied."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2
    img = np.full((15, 25, 3), 220, dtype=np.uint8)

    defaults = Action._default_ac0812_params(25, 15)

    monkeypatch.setattr(
        cv2,
        "HoughCircles",
        lambda *_args, **_kwargs: np.array([[[17.4, 7.3, 5.2]]], dtype=np.float32),
    )

    fitted = Action._fit_semantic_badge_from_image(img, defaults)

    assert abs(float(fitted["cx"]) - 17.4) < 1e-6
    assert abs(float(fitted["cy"]) - 7.3) < 1e-6
    assert abs(float(fitted["r"]) - 5.2) < 1e-6


def test_quantize_clamps_circle_radius_to_canvas_bounds() -> None:
    """Quantization should keep the full ring inside the viewport."""
    params = {
        "circle_enabled": True,
        "cx": 32.5,
        "cy": 12.5,
        "r": 15.0,
        "stroke_circle": 1.0,
    }

    quantized = Action._quantize_badge_params(params, w=45, h=25)

    assert float(quantized["r"]) <= 12.0 + 1e-6


def test_circle_bounds_respect_canvas_for_locked_center() -> None:
    """Circle optimization bounds must not permit radii outside canvas limits."""
    params = {
        "cx": 32.5,
        "cy": 12.5,
        "stroke_circle": 1.0,
        "min_circle_radius": 1.0,
    }

    _x_low, _x_high, _y_low, _y_high, _r_low, r_high = Action._circle_bounds(params, w=45, h=25)

    assert float(r_high) <= 12.0 + 1e-6


def test_fit_ac0812_does_not_cap_radius_to_too_small_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC0812 fitting should allow radius growth above small defaults when image fit supports it."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((25, 45, 3), 240, dtype=np.uint8)
    defaults = Action._default_ac0812_params(45, 25)

    def fake_fit(_img, _defaults):
        return {
            **_defaults,
            "cx": 32.5,
            "cy": 12.5,
            "r": 12.0,
            "stroke_circle": 1.0,
            "draw_text": False,
            "arm_enabled": True,
        }

    monkeypatch.setattr(Action, "_fit_semantic_badge_from_image", staticmethod(fake_fit))

    fitted = Action._fit_ac0812_params_from_image(img, defaults)

    assert float(fitted["r"]) >= 11.5
    assert float(fitted["max_circle_radius"]) >= 11.5


def test_finalize_ac0820_increases_optical_bias_for_co_vertical_centering() -> None:
    """AC0820 should nudge CO down so the main run appears vertically centered in-circle."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820", params)
    layout = Action._co2_layout(params)

    assert float(layout["y_base"]) > float(params["cy"])


def test_run_iteration_pipeline_element_validation_log_contains_run_meta(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Element validation logs should always include run metadata per execution."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2

    img = np.full((12, 20, 3), 240, dtype=np.uint8)
    img_path = tmp_path / "AC0812_L.jpg"
    csv_path = tmp_path / "data.csv"
    svg_dir = tmp_path / "svg"
    diff_dir = tmp_path / "diff"
    reports_dir = tmp_path / "reports"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0812;semantic\n", encoding="utf-8")
    assert cv2.imwrite(str(img_path), img)

    monkeypatch.setattr(
        image_composite_converter.Reflection,
        "parse_description",
        lambda *_args, **_kwargs: (
            "semantic",
            {"mode": "semantic_badge", "elements": ["SEMANTIC: test"], "label": ""},
        ),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "make_badge_params",
        staticmethod(lambda *_args, **_kwargs: image_composite_converter.Action._default_ac0812_params(20, 12)),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "validate_semantic_description_alignment",
        staticmethod(lambda *_args, **_kwargs: []),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "validate_badge_by_elements",
        staticmethod(lambda *_args, **_kwargs: ["ok: element pass"]),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "_enforce_semantic_connector_expectation",
        staticmethod(lambda _base, _elements, p, _w, _h: p),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "generate_badge_svg",
        staticmethod(lambda w, h, _p: f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"/>'),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "render_svg_to_numpy",
        staticmethod(lambda _svg, w, h: np.full((h, w, 3), 240, dtype=np.uint8)),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "create_diff_image",
        staticmethod(lambda a, _b: a.copy()),
    )

    image_composite_converter.Action.STOCHASTIC_RUN_SEED = 123
    image_composite_converter.Action.STOCHASTIC_SEED_OFFSET = 7
    res = image_composite_converter.run_iteration_pipeline(
        str(img_path),
        str(csv_path),
        2,
        str(svg_dir),
        str(diff_dir),
        str(reports_dir),
    )
    assert res is not None

    log_file = reports_dir / "AC0812_L_element_validation.log"
    assert log_file.exists()
    first_line = log_file.read_text(encoding="utf-8").splitlines()[0]
    assert first_line.startswith("run-meta: ")
    assert "run_seed=123" in first_line
    assert "pass_seed_offset=7" in first_line
    assert "nonce_ns=" in first_line


def test_run_iteration_pipeline_writes_failed_best_attempt_artifacts_for_semantic_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Semantic mismatches should still emit best-effort SVG and diff artifacts."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2

    img = np.full((12, 20, 3), 240, dtype=np.uint8)
    img_path = tmp_path / "AC0814_L.jpg"
    csv_path = tmp_path / "data.csv"
    svg_dir = tmp_path / "svg"
    diff_dir = tmp_path / "diff"
    reports_dir = tmp_path / "reports"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0814;semantic\n", encoding="utf-8")
    assert cv2.imwrite(str(img_path), img)

    monkeypatch.setattr(
        image_composite_converter.Reflection,
        "parse_description",
        lambda *_args, **_kwargs: (
            "semantic",
            {"mode": "semantic_badge", "elements": ["SEMANTIC: Kreis ohne Buchstabe"], "label": ""},
        ),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "make_badge_params",
        staticmethod(lambda *_args, **_kwargs: image_composite_converter.Action._default_ac0814_params(20, 12)),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "validate_semantic_description_alignment",
        staticmethod(lambda *_args, **_kwargs: ["circle missing"]),
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
        "create_diff_image",
        staticmethod(lambda a, _b: a.copy()),
    )

    res = image_composite_converter.run_iteration_pipeline(
        str(img_path),
        str(csv_path),
        2,
        str(svg_dir),
        str(diff_dir),
        str(reports_dir),
    )

    assert res is None
    assert (svg_dir / "AC0814_L_failed.svg").exists()
    assert (diff_dir / "AC0814_L_failed_diff.png").exists()
    log_text = (reports_dir / "AC0814_L_element_validation.log").read_text(encoding="utf-8")
    assert "status=semantic_mismatch" in log_text
    assert "best_attempt_svg=AC0814_L_failed.svg" in log_text
    assert "best_attempt_diff=AC0814_L_failed_diff.png" in log_text
    assert "semantic_audit_status=semantic_mismatch" in log_text
    assert "semantic_audit_derived_elements=SEMANTIC: Kreis ohne Buchstabe" in log_text
    assert "semantic_audit_mismatch_reason=circle missing" in log_text


def test_write_semantic_audit_report_persists_csv_and_json(tmp_path: Path) -> None:
    """Semantic audit exports should summarize AC0811-AC0814 review data in CSV and JSON."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    rows = [
        image_composite_converter._semantic_audit_record(
            base_name="AC0811",
            filename="AC0811_L.jpg",
            description_fragments=[
                {"source": "base_name", "key": "AC0811", "text": "Kreis ohne Buchstabe"},
                {"source": "variant_name", "key": "AC0811_L", "text": "senkrechter Strich hinter dem Kreis"},
            ],
            semantic_elements=[
                "SEMANTIC: Kreis ohne Buchstabe",
                "SEMANTIC: senkrechter Strich hinter dem Kreis",
            ],
            status="semantic_ok",
            semantic_priority_order=["family_rule", "layout_override", "description_heuristic"],
        ),
        image_composite_converter._semantic_audit_record(
            base_name="AC0814",
            filename="AC0814_S.jpg",
            description_fragments=[{"source": "base_name", "key": "AC0814", "text": "Kreis ohne Buchstabe"}],
            semantic_elements=[
                "SEMANTIC: Kreis ohne Buchstabe",
                "SEMANTIC: waagrechter Strich rechts vom Kreis",
            ],
            status="semantic_mismatch",
            mismatch_reasons=["Text unexpectedly required"],
            semantic_priority_order=["family_rule", "layout_override", "description_heuristic"],
            semantic_conflicts=["family_rule_kept_circle_without_letter_over_description_text=SEMANTIC: Kreis + Buchstabe CO_2"],
        ),
    ]

    image_composite_converter._write_semantic_audit_report(str(reports_dir), rows)

    csv_text = (reports_dir / "semantic_audit_ac0811_ac0814.csv").read_text(encoding="utf-8")
    assert "AC0811_L.jpg" in csv_text
    assert "semantic_ok" in csv_text
    assert "Text unexpectedly required" in csv_text
    assert "family_rule > layout_override > description_heuristic" in csv_text
    assert "family_rule_kept_circle_without_letter_over_description_text=SEMANTIC: Kreis + Buchstabe CO_2" in csv_text

    payload = (reports_dir / "semantic_audit_ac0811_ac0814.json").read_text(encoding="utf-8")
    assert '"filename": "AC0814_S.jpg"' in payload
    assert '"status": "semantic_mismatch"' in payload
    assert '"semantic_conflicts": [' in payload


def test_run_iteration_pipeline_breaks_early_on_flat_composite_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Composite search should stop early once the diff error is flat for long enough."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2

    img = np.full((8, 8, 3), 200, dtype=np.uint8)
    img_path = tmp_path / "AC0001_L.jpg"
    csv_path = tmp_path / "data.csv"
    svg_dir = tmp_path / "svg"
    diff_dir = tmp_path / "diff"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0001;composite\n", encoding="utf-8")
    assert cv2.imwrite(str(img_path), img)

    monkeypatch.setattr(
        image_composite_converter.Reflection,
        "parse_description",
        lambda *_args, **_kwargs: (
            "composite",
            {"mode": "composite", "elements": ["OBEN"], "parts": [{"position": "top", "source": "DER"}]},
        ),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "generate_composite_svg",
        staticmethod(lambda *_args, **_kwargs: '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"/>'),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "render_svg_to_numpy",
        staticmethod(lambda _svg, w, h: np.full((h, w, 3), 200, dtype=np.uint8)),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "calculate_error",
        staticmethod(lambda *_args, **_kwargs: 42.0),
    )
    monkeypatch.setattr(
        image_composite_converter.Action,
        "create_diff_image",
        staticmethod(lambda a, _b: a.copy()),
    )

    res = image_composite_converter.run_iteration_pipeline(
        str(img_path),
        str(csv_path),
        128,
        str(svg_dir),
        str(diff_dir),
    )
    assert res is not None
    assert res[3] == 1
    assert float(res[4]) == pytest.approx(42.0)

    out = capsys.readouterr().out
    assert "Früher Abbruch: Diff-Fehler blieb" in out
    assert "Konvergenzdiagnose: Plateau ohne messbare Verbesserung" in out
    iter_lines = [line for line in out.splitlines() if "[Iter" in line]
    assert len(iter_lines) < 128




def test_validate_semantic_description_alignment_requires_co2_text_region(monkeypatch: pytest.MonkeyPatch) -> None:
    """CO₂ semantic badges should fail when no usable foreground text region exists."""
    if image_composite_converter.np is None:
        pytest.skip("numpy not available in this environment")

    np = image_composite_converter.np
    assert np is not None
    img = np.full((20, 20, 3), 255, dtype=np.uint8)
    badge_params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))

    monkeypatch.setattr(
        Action,
        "_detect_semantic_primitives",
        staticmethod(lambda *_args, **_kwargs: {"circle": True, "arm": False, "text": True}),
    )
    monkeypatch.setattr(Action, "extract_badge_element_mask", staticmethod(lambda *_args, **_kwargs: None))

    issues = Action.validate_semantic_description_alignment(
        img,
        ["SEMANTIC: Kreis + Buchstabe CO_2"],
        badge_params,
    )

    assert any("CO₂-Textregion" in issue for issue in issues)


def test_validate_semantic_description_alignment_rejects_non_semantic_cross_shape() -> None:
    """A plain X-shape should not pass as circle+horizontal-line+CO₂ semantic badge."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2

    h, w = 78, 51
    img = np.full((h, w, 3), 255, dtype=np.uint8)
    line_color = (180, 180, 180)
    cv2.line(img, (6, 8), (w - 8, h - 8), line_color, 3)
    cv2.line(img, (w - 8, 8), (6, h - 8), line_color, 3)

    badge_params = Action._default_ac0834_params(w, h)
    issues = Action.validate_semantic_description_alignment(
        img,
        ["SEMANTIC: Kreis + Buchstabe CO_2", "SEMANTIC: waagrechter Strich rechts vom Kreis"],
        badge_params,
    )

    assert any("Kreis" in issue for issue in issues)
    assert any("waagrechter Strich" in issue for issue in issues)
    assert any("Text" in issue or "CO₂" in issue or "CO_2" in issue for issue in issues)


def test_detect_semantic_primitives_ignores_t_glyph_bar_inside_circle() -> None:
    """A centered T glyph inside a circle should not be misread as an external arm."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2

    img = np.full((36, 36, 3), 255, dtype=np.uint8)
    cv2.circle(img, (18, 18), 10, (150, 150, 150), 2)
    cv2.line(img, (14, 15), (22, 15), (120, 120, 120), 2)
    cv2.line(img, (18, 15), (18, 23), (120, 120, 120), 2)

    observed = Action._detect_semantic_primitives(img)

    assert observed["circle"] is True
    assert observed["arm"] is False




def test_in_requested_range_accepts_cross_prefix_span() -> None:
    """Ranges spanning prefixes (e.g. AC..ZZ) should include matching intermediate symbols."""
    assert image_composite_converter._in_requested_range("AC0812_L.jpg", "AC0000", "ZZ9999") is True


def test_in_requested_range_handles_reversed_bounds() -> None:
    """If CLI bounds are swapped, filtering should still behave as an inclusive range."""
    assert image_composite_converter._in_requested_range("AC0812_L.jpg", "ZZ9999", "AC0000") is True


def test_in_requested_range_excludes_values_outside_span() -> None:
    """Symbols before the lower bound should still be filtered out."""
    assert image_composite_converter._in_requested_range("AB9999_L.jpg", "AC0000", "ZZ9999") is False




def test_in_requested_range_includes_non_reference_filenames() -> None:
    """Non XX0000 filenames should not be filtered out by broad cross-prefix range settings."""
    assert image_composite_converter._in_requested_range("LOGO.JPG", "AC0000", "ZZ9999") is True


def test_in_requested_range_excludes_non_reference_filenames_for_exact_family_filter() -> None:
    """Exact family-specific filters should not pull unrelated helper files into the batch."""
    assert image_composite_converter._in_requested_range("z_231.jpg", "AC0811", "AC0811") is False


def test_in_requested_range_supports_three_letter_prefixes() -> None:
    """Three-letter families such as DLG should respect exact range filtering."""
    assert image_composite_converter._in_requested_range("DLG0030.jpg", "AC0811", "AC0811") is False
    assert image_composite_converter._in_requested_range("DLG0030.jpg", "DLG0030", "DLG0030") is True


def test_in_requested_range_treats_identical_short_bounds_as_prefix_filter() -> None:
    """Short identical bounds should include every symbol whose base name starts with that token."""
    assert image_composite_converter._in_requested_range("AC0814_L.jpg", "AC081", "AC081") is True
    assert image_composite_converter._in_requested_range("AC0813_M.jpg", "AC081", "AC081") is True
    assert image_composite_converter._in_requested_range("AC0820_L.jpg", "AC081", "AC081") is False


def test_in_requested_range_supports_one_sided_bounds() -> None:
    """When one bound is invalid, the valid bound should still be applied."""
    assert image_composite_converter._in_requested_range("AC0812_L.jpg", "", "AC0812") is True
    assert image_composite_converter._in_requested_range("AC0813_L.jpg", "", "AC0812") is False

def test_convert_range_does_not_skip_variants_in_quality_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Global quality passes should keep all variants eligible (no per-variant skip lock)."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2

    images_dir = tmp_path / "images"
    images_dir.mkdir()
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0812;semantic\n", encoding="utf-8")
    for name in ("AC0812_L.jpg", "AC0812_M.jpg"):
        assert cv2.imwrite(str(images_dir / name), np.full((10, 10, 3), 230, dtype=np.uint8))

    monkeypatch.setattr(image_composite_converter, "_in_requested_range", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(image_composite_converter, "_load_quality_config", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(image_composite_converter, "_write_quality_pass_report", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_harmonize_semantic_size_variants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_write_pixel_delta2_ranking", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_default_converted_symbols_root", lambda: str(tmp_path / "out"))

    def fake_pipeline(img_path: str, *_args, **_kwargs):
        stem = Path(img_path).stem
        params = {"mode": "semantic_badge", "cx": 5.0, "cy": 5.0, "r": 3.0}
        return stem, "semantic", params, 1, 100.0

    monkeypatch.setattr(image_composite_converter, "run_iteration_pipeline", fake_pipeline)

    captured_cfg: dict[str, object] = {}

    def capture_quality_cfg(_reports_out_dir: str, *, allowed_error_per_pixel: float, skipped_variants: list[str], source: str) -> None:
        captured_cfg["allowed_error_per_pixel"] = allowed_error_per_pixel
        captured_cfg["skipped_variants"] = list(skipped_variants)
        captured_cfg["source"] = source

    monkeypatch.setattr(image_composite_converter, "_write_quality_config", capture_quality_cfg)

    observed_skips: list[set[str]] = []

    def capture_open_cases(rows, allowed_error_per_pixel, skip_variants=None):
        observed_skips.append(set(skip_variants or set()))
        return []

    monkeypatch.setattr(image_composite_converter, "_select_open_quality_cases", capture_open_cases)
    monkeypatch.setattr(image_composite_converter, "_select_middle_lower_tercile", lambda _rows: [])

    image_composite_converter.convert_range(str(images_dir), str(csv_path), iterations=2, start_ref="AC0812", end_ref="AC0812")

    assert captured_cfg["skipped_variants"] == []
    assert observed_skips
    assert all(not skip_set for skip_set in observed_skips)


def test_quality_pass_report_records_delta2_and_decision(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    conv._write_quality_pass_report(
        str(reports_dir),
        [
            {
                "pass": 1,
                "filename": "AC0820_L.jpg",
                "old_error_per_pixel": 0.5,
                "new_error_per_pixel": 0.4,
                "old_mean_delta2": 20.0,
                "new_mean_delta2": 18.0,
                "improved": True,
                "decision": "accepted_improvement",
                "iteration_budget": 128,
                "badge_validation_rounds": 6,
            },
            {
                "pass": 2,
                "filename": "AC0820_M.jpg",
                "old_error_per_pixel": 0.4,
                "new_error_per_pixel": 0.45,
                "old_mean_delta2": 18.0,
                "new_mean_delta2": 19.0,
                "improved": False,
                "decision": "rejected_regression",
                "iteration_budget": 132,
                "badge_validation_rounds": 7,
            },
        ],
    )

    rows = (reports_dir / "quality_tercile_passes.csv").read_text(encoding="utf-8").strip().splitlines()
    assert rows[0] == (
        "pass;filename;old_error_per_pixel;new_error_per_pixel;old_mean_delta2;new_mean_delta2;"
        "improved;decision;iteration_budget;badge_validation_rounds"
    )
    assert "accepted_improvement" in rows[1]
    assert "rejected_regression" in rows[2]


def test_evaluate_quality_pass_candidate_rejects_full_regression() -> None:
    improved, decision, old_error, new_error, old_delta2, new_delta2 = conv._evaluate_quality_pass_candidate(
        {
            "error_per_pixel": 0.20,
            "mean_delta2": 10.0,
        },
        {
            "error_per_pixel": 0.25,
            "mean_delta2": 12.0,
        },
    )

    assert improved is False
    assert decision == "rejected_regression"
    assert old_error == pytest.approx(0.20)
    assert new_error == pytest.approx(0.25)
    assert old_delta2 == pytest.approx(10.0)
    assert new_delta2 == pytest.approx(12.0)


def test_convert_range_accepts_quality_pass_when_mean_delta2_improves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2
    if np is None or cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    images_dir = tmp_path / "images"
    images_dir.mkdir()
    output_root = tmp_path / "out"
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0820;semantic\n", encoding="utf-8")
    assert cv2.imwrite(str(images_dir / "AC0820_L.jpg"), np.full((10, 10, 3), 220, dtype=np.uint8))

    monkeypatch.setattr(image_composite_converter, "_in_requested_range", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(image_composite_converter, "_load_quality_config", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(image_composite_converter, "_write_quality_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_harmonize_semantic_size_variants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_write_pixel_delta2_ranking", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_select_open_quality_cases", lambda rows, **_kwargs: list(rows))
    monkeypatch.setattr(image_composite_converter, "_select_middle_lower_tercile", lambda _rows: [])
    monkeypatch.setattr(image_composite_converter, "_try_template_transfer", lambda **_kwargs: (None, None))

    pass_reports: list[dict[str, object]] = []
    monkeypatch.setattr(image_composite_converter, "_write_quality_pass_report", lambda _dir, rows: pass_reports.extend(rows))

    state = {"count": 0}

    def fake_pipeline(img_path: str, _csv_path: str, _iterations: int, svg_out: str, diff_out: str, reports_out: str, *_args, **_kwargs):
        state["count"] += 1
        stem = Path(img_path).stem
        Path(svg_out).mkdir(parents=True, exist_ok=True)
        Path(diff_out).mkdir(parents=True, exist_ok=True)
        Path(reports_out).mkdir(parents=True, exist_ok=True)
        if state["count"] == 1:
            svg = '<svg width="10" height="10" xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10" fill="#000000"/></svg>'
            best_error = 30.0
        else:
            svg = '<svg width="10" height="10" xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10" fill="#d0d0d0"/></svg>'
            best_error = 31.0
        (Path(svg_out) / f"{stem}.svg").write_text(svg, encoding="utf-8")
        (Path(diff_out) / f"{stem}_diff.png").write_bytes(b"png")
        params = {"mode": "semantic_badge", "elements": ["circle"], "cx": 5.0, "cy": 5.0, "r": 3.0}
        return stem, "semantic", params, 1, best_error

    monkeypatch.setattr(image_composite_converter, "run_iteration_pipeline", fake_pipeline)

    result = image_composite_converter.convert_range(
        str(images_dir),
        str(csv_path),
        iterations=1,
        start_ref="AC0820",
        end_ref="AC0820",
        output_root=str(output_root),
    )

    assert result == str(output_root)
    assert pass_reports
    assert pass_reports[0]["improved"] is True
    assert pass_reports[0]["decision"] == "accepted_improvement"
    assert float(pass_reports[0]["new_error_per_pixel"]) > float(pass_reports[0]["old_error_per_pixel"])
    assert float(pass_reports[0]["new_mean_delta2"]) < float(pass_reports[0]["old_mean_delta2"])


def test_convert_range_rejects_quality_pass_regression_and_keeps_previous_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2
    if np is None or cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    images_dir = tmp_path / "images"
    images_dir.mkdir()
    output_root = tmp_path / "out"
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0820;semantic\n", encoding="utf-8")
    assert cv2.imwrite(str(images_dir / "AC0820_L.jpg"), np.full((10, 10, 3), 220, dtype=np.uint8))

    monkeypatch.setattr(image_composite_converter, "_in_requested_range", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(image_composite_converter, "_load_quality_config", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(image_composite_converter, "_write_quality_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_harmonize_semantic_size_variants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_write_pixel_delta2_ranking", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_select_open_quality_cases", lambda rows, **_kwargs: list(rows))
    monkeypatch.setattr(image_composite_converter, "_select_middle_lower_tercile", lambda _rows: [])
    monkeypatch.setattr(image_composite_converter, "_try_template_transfer", lambda **_kwargs: (None, None))

    pass_reports: list[dict[str, object]] = []
    monkeypatch.setattr(image_composite_converter, "_write_quality_pass_report", lambda _dir, rows: pass_reports.extend(rows))

    state = {"count": 0}

    def fake_pipeline(img_path: str, _csv_path: str, _iterations: int, svg_out: str, diff_out: str, reports_out: str, *_args, **_kwargs):
        state["count"] += 1
        stem = Path(img_path).stem
        Path(svg_out).mkdir(parents=True, exist_ok=True)
        Path(diff_out).mkdir(parents=True, exist_ok=True)
        Path(reports_out).mkdir(parents=True, exist_ok=True)
        if state["count"] == 1:
            svg = "<svg width=\"10\" height=\"10\" xmlns=\"http://www.w3.org/2000/svg\"><rect width=\"10\" height=\"10\" fill=\"#d0d0d0\"/></svg>"
            best_error = 30.0
        else:
            svg = "<svg width=\"10\" height=\"10\" xmlns=\"http://www.w3.org/2000/svg\"><rect width=\"10\" height=\"10\" fill=\"#000000\"/></svg>"
            best_error = 31.0
        (Path(svg_out) / f"{stem}.svg").write_text(svg, encoding="utf-8")
        (Path(diff_out) / f"{stem}_diff.png").write_bytes(b"png")
        params = {"mode": "semantic_badge", "elements": ["circle"], "cx": 5.0, "cy": 5.0, "r": 3.0}
        return stem, "semantic", params, 1, best_error

    monkeypatch.setattr(image_composite_converter, "run_iteration_pipeline", fake_pipeline)

    result = image_composite_converter.convert_range(
        str(images_dir),
        str(csv_path),
        iterations=1,
        start_ref="AC0820",
        end_ref="AC0820",
        output_root=str(output_root),
    )

    assert result == str(output_root)
    assert pass_reports
    assert pass_reports[0]["improved"] is False
    assert pass_reports[0]["decision"] == "rejected_regression"

    iteration_log = (output_root / "reports" / "Iteration_Log.csv").read_text(encoding="utf-8-sig")
    assert "0.30000000" in iteration_log
    assert "0.31000000" not in iteration_log


def test_convert_range_writes_svgs_and_diffs_to_dedicated_subfolders(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Converted SVGs and diff PNGs should be separated into stable subdirectories."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2

    images_dir = tmp_path / "images"
    images_dir.mkdir()
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0812;semantic\n", encoding="utf-8")
    assert cv2.imwrite(str(images_dir / "AC0812_L.jpg"), np.full((10, 10, 3), 230, dtype=np.uint8))

    monkeypatch.setattr(image_composite_converter, "_in_requested_range", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(image_composite_converter, "_load_quality_config", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(image_composite_converter, "_write_quality_pass_report", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_harmonize_semantic_size_variants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_write_pixel_delta2_ranking", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_select_open_quality_cases", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(image_composite_converter, "_select_middle_lower_tercile", lambda *_args, **_kwargs: [])

    def fake_pipeline(img_path: str, _csv_path: str, _iterations: int, svg_out: str, diff_out: str, reports_out: str, *_args, **_kwargs):
        stem = Path(img_path).stem
        Path(svg_out).mkdir(parents=True, exist_ok=True)
        Path(diff_out).mkdir(parents=True, exist_ok=True)
        Path(reports_out).mkdir(parents=True, exist_ok=True)
        (Path(svg_out) / f"{stem}.svg").write_text("<svg/>", encoding="utf-8")
        (Path(diff_out) / f"{stem}_diff.png").write_bytes(b"png")
        params = {"mode": "semantic_badge", "elements": ["circle"], "cx": 5.0, "cy": 5.0, "r": 3.0}
        return stem, "semantic", params, 1, 100.0

    monkeypatch.setattr(image_composite_converter, "run_iteration_pipeline", fake_pipeline)

    output_root = tmp_path / "out"
    result = image_composite_converter.convert_range(
        str(images_dir),
        str(csv_path),
        iterations=2,
        start_ref="AC0812",
        end_ref="AC0812",
        output_root=str(output_root),
    )

    assert result == str(output_root)
    assert (output_root / "converted_svgs" / "AC0812_L.svg").exists()
    assert (output_root / "diff_pngs" / "AC0812_L_diff.png").exists()
    assert (output_root / "reports" / "Iteration_Log.csv").exists()


def test_template_transfer_donor_family_compatible() -> None:
    assert image_composite_converter._template_transfer_donor_family_compatible("GE011", "GE020") is True
    assert image_composite_converter._template_transfer_donor_family_compatible("GE011", "AC0812") is False
    assert image_composite_converter._template_transfer_donor_family_compatible("DLG0000", "DLG0015") is True
    assert image_composite_converter._template_transfer_donor_family_compatible("DLG0000", "AC0812") is False
    assert image_composite_converter._template_transfer_donor_family_compatible("NAV0020", "NAV0030") is True
    assert image_composite_converter._template_transfer_donor_family_compatible("NAV0020", "AC5000") is False
    assert image_composite_converter._template_transfer_donor_family_compatible("LOGO", "AC0812") is True
    assert image_composite_converter._template_transfer_donor_family_compatible(
        "GE0000",
        "AC0010",
        documented_alias_refs={"AC0010"},
    ) is True


def test_convert_range_filters_to_explicit_selected_variants_and_writes_regression_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2
    if cv2 is None:
        pytest.skip("opencv not available in this environment")

    images_dir = tmp_path / "images"
    images_dir.mkdir()
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Wurzelform;Beschreibung\n", encoding="utf-8")
    for variant in image_composite_converter.AC08_REGRESSION_VARIANTS:
        assert cv2.imwrite(str(images_dir / f"{variant}.jpg"), np.full((10, 10, 3), 230, dtype=np.uint8))
    assert cv2.imwrite(str(images_dir / "AC0999_L.jpg"), np.full((10, 10, 3), 200, dtype=np.uint8))

    monkeypatch.setattr(image_composite_converter, "_in_requested_range", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(image_composite_converter, "_load_quality_config", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(image_composite_converter, "_write_quality_pass_report", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_harmonize_semantic_size_variants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_write_pixel_delta2_ranking", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_select_open_quality_cases", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(image_composite_converter, "_select_middle_lower_tercile", lambda *_args, **_kwargs: [])

    seen: list[str] = []

    def fake_pipeline(img_path: str, _csv_path: str, _iterations: int, svg_out: str, diff_out: str, reports_out: str, *_args, **_kwargs):
        stem = Path(img_path).stem
        seen.append(stem)
        Path(svg_out).mkdir(parents=True, exist_ok=True)
        Path(diff_out).mkdir(parents=True, exist_ok=True)
        Path(reports_out).mkdir(parents=True, exist_ok=True)
        (Path(svg_out) / f"{stem}.svg").write_text("<svg/>", encoding="utf-8")
        (Path(diff_out) / f"{stem}_diff.png").write_bytes(b"png")
        params = {"mode": "semantic_badge", "elements": ["circle"], "cx": 5.0, "cy": 5.0, "r": 3.0}
        return stem, "semantic", params, 1, 100.0

    monkeypatch.setattr(image_composite_converter, "run_iteration_pipeline", fake_pipeline)

    output_root = tmp_path / "out"
    result = image_composite_converter.convert_range(
        str(images_dir),
        str(csv_path),
        iterations=32,
        start_ref="AC0000",
        end_ref="ZZ9999",
        output_root=str(output_root),
        selected_variants=set(image_composite_converter.AC08_REGRESSION_VARIANTS),
    )

    assert result == str(output_root)
    assert sorted(seen) == sorted(image_composite_converter.AC08_REGRESSION_VARIANTS)
    reports_dir = output_root / "reports"
    manifest = (reports_dir / "ac08_regression_set.csv").read_text(encoding="utf-8")
    summary = (reports_dir / "ac08_regression_summary.txt").read_text(encoding="utf-8")
    assert "AC0999_L" not in manifest
    assert "set;variant;focus;reason" in manifest
    assert image_composite_converter.AC08_REGRESSION_SET_NAME in manifest
    assert "expected_reports=Iteration_Log.csv,quality_tercile_passes.csv,pixel_delta2_ranking.csv,pixel_delta2_summary.txt,ac08_success_metrics.csv,ac08_success_criteria.txt" in summary


def test_write_ac08_success_criteria_report_summarizes_regression_metrics(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    expected = list(image_composite_converter.AC08_REGRESSION_VARIANTS)

    (reports_dir / "Iteration_Log.csv").write_text(
        "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel\n"
        + "".join(f"{variant}.jpg;SEMANTIC: circle;2;10.00;0.01000000\n" for variant in expected),
        encoding="utf-8",
    )
    (reports_dir / "quality_tercile_passes.csv").write_text(
        "pass;filename;old_error_per_pixel;new_error_per_pixel;old_mean_delta2;new_mean_delta2;improved;decision;iteration_budget;badge_validation_rounds\n"
        "1;AC0820_L.jpg;0.03000000;0.02000000;20.000000;15.000000;1;accepted_improvement;128;6\n"
        "1;AC0835_S.jpg;0.01000000;0.01200000;10.000000;10.500000;0;rejected_regression;128;6\n",
        encoding="utf-8",
    )
    (reports_dir / "AC0811_L_element_validation.log").write_text(
        "run-meta: seed=1\nstatus=semantic_mismatch\nRunde 1: elementweise Validierung gestartet\n",
        encoding="utf-8",
    )
    (reports_dir / "AC0820_L_element_validation.log").write_text(
        "run-meta: seed=1\nRunde 1: elementweise Validierung gestartet\nRunde 2: elementweise Validierung gestartet\n",
        encoding="utf-8",
    )
    (reports_dir / "AC0835_S_element_validation.log").write_text(
        "run-meta: seed=1\nRunde 1: elementweise Validierung gestartet\nAbbruch: SVG konnte nicht gerendert werden\n",
        encoding="utf-8",
    )

    image_composite_converter._write_ac08_success_criteria_report(
        str(reports_dir),
        selected_variants=expected,
    )

    metrics = (reports_dir / "ac08_success_metrics.csv").read_text(encoding="utf-8")
    summary = (reports_dir / "ac08_success_criteria.txt").read_text(encoding="utf-8")
    assert "improved_error_per_pixel_count;1" in metrics
    assert "improved_mean_delta2_count;1" in metrics
    assert "semantic_mismatch_count;1" in metrics
    assert "batch_abort_or_render_failure_count;1" in metrics
    assert "rejected_regression_count;1" in metrics
    assert "accepted_regression_count;0" in metrics
    assert "criterion_no_new_batch_aborts=0" in summary
    assert "criterion_no_accepted_regressions=1" in summary
    assert "criterion_regression_set_improved=1" in summary
    assert "overall_success=0" in summary


def test_parse_description_extracts_documented_alias_refs() -> None:
    raw = {"GE0000": "Kreisform wie AC0010 und Kante wie in AC0501"}
    _desc, params = image_composite_converter.Reflection(raw).parse_description("GE0000", "GE0000_S.jpg")
    assert set(params.get("documented_alias_refs", [])) == {"AC0010", "AC0501"}


def test_template_transfer_skips_cross_family_donor_for_non_semantic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2
    if np is None or cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    img = np.full((12, 12, 3), 220, dtype=np.uint8)
    folder_path = tmp_path / "images"
    svg_out = tmp_path / "svg"
    diff_out = tmp_path / "diff"
    folder_path.mkdir()
    svg_out.mkdir()
    diff_out.mkdir()

    target_filename = "GE0110_S.jpg"
    assert cv2.imwrite(str(folder_path / target_filename), img)
    (svg_out / "GE0110_S.svg").write_text('<svg viewBox="0 0 12 12" xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    (svg_out / "AC0812_S.svg").write_text('<svg viewBox="0 0 12 12" xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")

    target_row = {
        "filename": target_filename,
        "variant": "GE0110_S",
        "base": "GE0110",
        "params": {"mode": "composite"},
        "best_error": 100.0,
        "error_per_pixel": 100.0 / 144.0,
        "w": 12,
        "h": 12,
    }
    donor_rows = [
        {
            "variant": "AC0812_S",
            "base": "AC0812",
            "params": {"mode": "composite"},
            "error_per_pixel": 0.1,
            "best_error": 14.0,
            "w": 12,
            "h": 12,
        }
    ]

    monkeypatch.setattr(image_composite_converter, "_rank_template_transfer_donors", lambda _t, d: d)
    monkeypatch.setattr(image_composite_converter, "_read_svg_geometry", lambda _p: None)

    called: dict[str, int] = {"build": 0}

    def fail_if_called(*_args, **_kwargs):
        called["build"] += 1
        return "<svg/>"

    monkeypatch.setattr(image_composite_converter, "_build_transformed_svg_from_template", fail_if_called)

    updated, detail = image_composite_converter._try_template_transfer(
        target_row=target_row,
        donor_rows=donor_rows,
        folder_path=str(folder_path),
        svg_out_dir=str(svg_out),
        diff_out_dir=str(diff_out),
        rng=None,
    )

    assert updated is None
    assert detail is None
    assert called["build"] == 0


def test_co2_layout_keeps_subscript_inside_inner_circle_for_centered_badges() -> None:
    """Centered CO₂ badges should keep the subscript inside the inner circle."""
    params = Action._apply_co2_label(Action._default_ac0870_params(15, 15))
    params = Action._finalize_ac08_style("AC0820", params)
    layout = Action._co2_layout(params)

    cx = float(params["cx"])
    r = float(params["r"])
    stroke = float(params["stroke_circle"])
    inner_right = cx + max(1.0, r - stroke)

    assert float(layout["x2"]) <= inner_right + 1e-6

def test_co2_layout_keeps_text_within_inner_circle_bounds() -> None:
    """CO₂ layout should not let any glyph run outside the inner circle boundary."""
    params = Action._apply_co2_label(Action._default_ac0870_params(15, 15))
    params = Action._finalize_ac08_style("AC0820", params)
    layout = Action._co2_layout(params)

    cx = float(params["cx"])
    cy = float(params["cy"])
    r = float(params["r"])
    stroke = float(params["stroke_circle"])
    inner_left = cx - max(1.0, r - stroke)
    inner_right = cx + max(1.0, r - stroke)
    inner_top = cy - max(1.0, r - stroke)
    inner_bottom = cy + max(1.0, r - stroke)

    text_top = float(layout["y_base"]) - (float(layout["height"]) / 2.0)
    text_bottom = float(layout["subscript_y"]) + (float(layout["sub_font_px"]) * 0.35)

    assert float(layout["x1"]) >= inner_left - 1e-6
    assert float(layout["x2"]) <= inner_right + 1e-6
    assert text_top >= inner_top - 1e-6
    assert text_bottom <= inner_bottom + 1e-6


def test_optimize_circle_pose_adaptive_domain_improves_and_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adaptive domain search should improve pose and report boundary/plateau hints."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((20, 20, 3), 220, dtype=np.uint8)
    params = {
        "circle_enabled": True,
        "cx": 3.0,
        "cy": 3.0,
        "r": 2.0,
        "min_circle_radius": 1.0,
    }

    def fake_error(_img: object, _params: dict, *, cx_value: float, cy_value: float, radius_value: float) -> float:
        return float((cx_value - 9.0) ** 2 + (cy_value - 10.0) ** 2 + (radius_value - 5.0) ** 2)

    monkeypatch.setattr(Action, "_element_error_for_circle_pose", staticmethod(fake_error))
    logs: list[str] = []

    changed = Action._optimize_circle_pose_adaptive_domain(img, params, logs, rounds=3, samples_per_round=14)

    assert changed is True
    assert abs(float(params["cx"]) - 9.0) <= 3.0
    assert abs(float(params["cy"]) - 10.0) <= 3.0
    assert abs(float(params["r"]) - 5.0) <= 2.0
    assert any("Adaptive-Domain-Suche übernommen" in line for line in logs)


def test_optimize_circle_pose_adaptive_domain_uses_run_seed_offset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adaptive domain RNG should incorporate run-seed and pass offset."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((20, 20, 3), 220, dtype=np.uint8)
    params = {
        "circle_enabled": True,
        "cx": 9.0,
        "cy": 10.0,
        "r": 5.0,
        "min_circle_radius": 1.0,
    }

    captured: list[int] = []

    class _DummyRng:
        def uniform(self, low: float, high: float) -> float:
            return float((low + high) / 2.0)

    monkeypatch.setattr(Action, "_element_error_for_circle_pose", staticmethod(lambda *_args, **_kwargs: 1.0))

    original_default_rng = np.random.default_rng

    def fake_default_rng(seed: int):
        captured.append(int(seed))
        return _DummyRng()

    monkeypatch.setattr(np.random, "default_rng", fake_default_rng)
    logs: list[str] = []

    Action.STOCHASTIC_RUN_SEED = 41
    Action.STOCHASTIC_SEED_OFFSET = 2
    try:
        Action._optimize_circle_pose_adaptive_domain(img, params, logs, rounds=1, samples_per_round=8)
    finally:
        Action.STOCHASTIC_RUN_SEED = 0
        Action.STOCHASTIC_SEED_OFFSET = 0
        np.random.default_rng = original_default_rng

    assert captured
    assert captured[0] == 2027 + 41 + 2


def test_optimize_circle_pose_adaptive_domain_no_improvement(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adaptive domain search should return False when no better sample exists."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((20, 20, 3), 220, dtype=np.uint8)
    params = {
        "circle_enabled": True,
        "cx": 9.0,
        "cy": 10.0,
        "r": 5.0,
        "min_circle_radius": 1.0,
    }

    monkeypatch.setattr(
        Action,
        "_element_error_for_circle_pose",
        staticmethod(lambda *_args, **_kwargs: 1.0),
    )
    logs: list[str] = []

    changed = Action._optimize_circle_pose_adaptive_domain(img, params, logs, rounds=2, samples_per_round=10)

    assert changed is False
    assert any("keine relevante Verbesserung" in line for line in logs)


def test_co2_layout_vertical_centering_ignores_subscript_for_main_text() -> None:
    """The CO run should stay centered even if the subscript is very large."""
    params = Action._apply_co2_label(Action._default_ac0870_params(15, 15))
    params = Action._finalize_ac08_style("AC0820", params)
    params["co2_sub_font_scale"] = 95.0
    layout = Action._co2_layout(params)

    assert abs(float(layout["y_base"]) - float(params["cy"])) <= 0.75


def test_co2_layout_keeps_subscript_inside_circle_without_changing_main_center() -> None:
    """Large subscripts should be constrained by offset, not by shifting the CO baseline."""
    params = Action._apply_co2_label(Action._default_ac0870_params(15, 15))
    params = Action._finalize_ac08_style("AC0820", params)
    params["co2_sub_font_scale"] = 95.0
    layout = Action._co2_layout(params)

    cy = float(params["cy"])
    r = float(params["r"])
    stroke = float(params["stroke_circle"])
    inner_top = cy - max(1.0, r - stroke)
    inner_bottom = cy + max(1.0, r - stroke)

    sub_top = float(layout["subscript_y"]) - (float(layout["sub_font_px"]) * 0.60)
    sub_bottom = float(layout["subscript_y"]) + (float(layout["sub_font_px"]) * 0.35)

    assert sub_top >= inner_top - 1e-6
    assert sub_bottom <= inner_bottom + 1e-6
    assert abs(float(layout["y_base"]) - cy) <= 0.75


def test_co2_layout_enforces_minimum_subscript_pixel_size() -> None:
    """Subscript font should keep a minimum size so the "2" remains visible."""
    params = Action._apply_co2_label(Action._default_ac0870_params(15, 15))
    params["co2_font_scale"] = 0.50
    params["co2_sub_font_scale"] = 40.0
    layout = Action._co2_layout(params)

    assert float(layout["sub_font_px"]) >= 4.0


def test_finalize_ac0820_keeps_text_scale_tunable_with_bounds() -> None:
    """AC0820 should allow bounded CO₂ scale tuning during validation rounds."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params = Action._finalize_ac08_style("AC0820", params)

    assert params["lock_text_scale"] is False
    assert float(params["co2_font_scale_min"]) < float(params["co2_font_scale"])
    assert float(params["co2_font_scale_max"]) > float(params["co2_font_scale"])


def test_finalize_non_ac0820_co2_keeps_text_scale_locked() -> None:
    """Non-AC0820 CO₂ badges should keep fixed text scale to avoid drift."""
    params = Action._apply_co2_label(Action._default_ac0881_params(20, 20))
    params = Action._finalize_ac08_style("AC0831", params)

    assert params["lock_text_scale"] is True


def test_make_badge_params_applies_ac0831_vertical_co2_tuning() -> None:
    """AC0831 should use cluster-centered CO₂ placement with a slight downward bias."""
    params = Action.make_badge_params(25, 45, "AC0831", None)

    assert params["co2_anchor_mode"] == "cluster"
    assert float(params["co2_optical_bias"]) >= 0.10
    assert float(params["co2_dy"]) > 0.0


def test_finalize_tiny_non_ac0820_co2_unlocks_bounded_text_tuning() -> None:
    """Tiny CO₂ variants should allow bounded text tuning across AC08xx families."""
    params = Action._apply_co2_label(Action._default_ac0813_params(15, 25))
    params = Action._finalize_ac08_style("AC0833_S", params)

    assert params["lock_text_scale"] is False
    assert float(params["co2_font_scale_min"]) < float(params["co2_font_scale"])
    assert float(params["co2_font_scale_max"]) > float(params["co2_font_scale"])

def test_generate_badge_svg_renders_center_co_as_split_text_nodes() -> None:
    """center_co layout should render CO and subscript as separate positioned text nodes."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    svg = Action.generate_badge_svg(30, 30, params)

    assert ">CO</text>" in svg
    assert ">2</text>" in svg
    assert "<tspan" not in svg


def test_generate_badge_svg_renders_cluster_mode_as_split_text_nodes() -> None:
    """Cluster mode should render CO₂ as explicit CO + subscript nodes."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820", params)
    svg = Action.generate_badge_svg(30, 30, params)

    assert ">CO</text>" in svg
    assert ">2</text>" in svg
    assert "<tspan" not in svg



def test_make_badge_params_ac0812_family_keeps_left_arm_without_image_fit() -> None:
    """AC0812-family semantic defaults must always preserve a visible left connector."""
    for name in ("AC0812", "AC0882", "AC0832", "AC0837"):
        params = Action.make_badge_params(45, 25, name, img=None)
        assert params is not None
        assert params.get("arm_enabled") is True
        assert abs(float(params["arm_y1"]) - float(params["cy"])) < 1e-6
        assert abs(float(params["arm_y2"]) - float(params["cy"])) < 1e-6
        assert float(params["arm_x1"]) == 0.0
        assert float(params["arm_x2"]) > 0.0
        assert float(params.get("arm_len_min", 0.0)) >= float(params["arm_x2"]) * float(params.get("arm_len_min_ratio", 0.75))


def test_enforce_left_arm_badge_geometry_restores_missing_arm() -> None:
    """Left-arm enforcement should recover connector geometry from circle-only params."""
    params = {"cx": 32.5, "cy": 12.5, "r": 10.0, "circle_enabled": True}

    fixed = Action._enforce_left_arm_badge_geometry(params, 45, 25)

    assert fixed.get("arm_enabled") is True
    assert float(fixed["arm_x1"]) == 0.0
    assert abs(float(fixed["arm_y1"]) - 12.5) < 1e-6
    assert abs(float(fixed["arm_x2"]) - 22.5) < 1e-6
    assert abs(float(fixed["arm_y2"]) - 12.5) < 1e-6
    assert float(fixed["arm_len_min"]) >= 22.5 * 0.75


def test_default_ac0812_uses_height_based_circle_radius() -> None:
    """AC0812 should size its circle from height without overfilling the frame."""
    params = Action._default_ac0812_params(25, 15)


def test_find_elements_detects_multiple_components() -> None:
    binary = [[0 for _ in range(30)] for _ in range(20)]
    for y in range(2, 7):
        for x in range(2, 7):
            binary[y][x] = 1
    for y in range(10, 17):
        for x in range(20, 27):
            binary[y][x] = 1

def test_fit_ac0812_caps_radius_to_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC0812 fit should cap radius to geometric canvas limits."""

    monkeypatch.setattr(
        Action,
        "_fit_semantic_badge_from_image",
        staticmethod(
            lambda _img, defaults: {
                **defaults,
                "cx": float(defaults["cx"]),
                "cy": float(defaults["cy"]),
                "r": float(defaults["r"]) * 1.8,
                "arm_enabled": True,
                "draw_text": False,
            }
        ),
    )

    class DummyImg:
        shape = (15, 25, 3)

    defaults = Action._default_ac0812_params(25, 15)
    fitted = Action._fit_ac0812_params_from_image(DummyImg(), defaults)

    expected_max = Action._max_circle_radius_inside_canvas(
        float(defaults["cx"]),
        float(defaults["cy"]),
        25,
        15,
        float(defaults["stroke_circle"]),
    )
    assert float(fitted["r"]) <= float(expected_max) + 1e-6


def test_fit_ac0812_elongated_variant_uses_stronger_min_arm_ratio(monkeypatch: pytest.MonkeyPatch) -> None:
    """Elongated AC0812 variants should enforce a stronger left-arm minimum ratio."""

    monkeypatch.setattr(
        Action,
        "_fit_semantic_badge_from_image",
        staticmethod(
            lambda _img, defaults: {
                **defaults,
                "cx": float(defaults["cx"]),
                "cy": float(defaults["cy"]),
                "r": float(defaults["r"]) * 1.1,
                "arm_enabled": True,
                "draw_text": False,
            }
        ),
    )

    class DummyImg:
        shape = (25, 45, 3)

    defaults = Action._default_ac0812_params(45, 25)
    fitted = Action._fit_ac0812_params_from_image(DummyImg(), defaults)

    assert float(fitted["arm_len_min_ratio"]) >= 0.82


def test_fit_ac0814_tiny_plain_variant_reanchors_circle_to_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tiny AC0814 variants should keep the circle centered on the semantic template."""

    monkeypatch.setattr(
        Action,
        "_fit_semantic_badge_from_image",
        staticmethod(
            lambda _img, defaults: {
                **defaults,
                "cx": float(defaults["cx"]) + 1.75,
                "cy": float(defaults["cy"]) + 1.25,
                "r": float(defaults["r"]) * 0.90,
                "arm_enabled": True,
                "draw_text": False,
            }
        ),
    )

    class DummyImg:
        shape = (14, 24, 3)

    defaults = Action._default_ac0814_params(24, 14)
    fitted = Action._fit_ac0814_params_from_image(DummyImg(), defaults)

    assert float(fitted["cx"]) == pytest.approx(float(defaults["cx"]))
    assert float(fitted["cy"]) == pytest.approx(float(defaults["cy"]) + 0.5)
    assert float(fitted["r"]) >= float(defaults["r"]) * 0.98
    assert fitted["lock_circle_cx"] is True
    assert fitted["lock_circle_cy"] is True
    assert fitted["lock_arm_center_to_circle"] is True


def test_fit_ac0814_tiny_plain_variant_reanchors_arm_to_adjusted_circle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tiny AC0814 arm geometry should be rebuilt from the reanchored circle pose."""

    monkeypatch.setattr(
        Action,
        "_fit_semantic_badge_from_image",
        staticmethod(
            lambda _img, defaults: {
                **defaults,
                "cx": float(defaults["cx"]) + 2.0,
                "cy": float(defaults["cy"]) - 1.0,
                "r": float(defaults["r"]),
                "arm_enabled": True,
                "draw_text": False,
            }
        ),
    )

    class DummyImg:
        shape = (14, 24, 3)

    defaults = Action._default_ac0814_params(24, 14)
    fitted = Action._fit_ac0814_params_from_image(DummyImg(), defaults)

    assert float(fitted["arm_x1"]) == pytest.approx(min(24.0, float(fitted["cx"]) + float(fitted["r"])))
    assert float(fitted["arm_y1"]) == pytest.approx(float(fitted["cy"]))
    assert float(fitted["arm_x2"]) == pytest.approx(24.0)
    assert float(fitted["arm_y2"]) == pytest.approx(float(fitted["cy"]))


def test_validate_badge_can_expand_ac0812_tiny_circle_radius() -> None:
    """Element validation should actively correct a too-small AC0812_S circle radius."""
    img_path = Path("artifacts/images_to_convert/AC0812_S.jpg")
    cv2 = pytest.importorskip("cv2", exc_type=ImportError)
    img = cv2.imread(str(img_path))
    if img is None:
        pytest.skip("AC0812_S fixture image not available")

    h, w = img.shape[:2]
    params = Action._finalize_ac08_style("AC0812", Action._default_ac0812_params(w, h))
    params["r"] = 5.0
    params["arm_x2"] = max(0.0, float(params["cx"]) - float(params["r"]))

    logs = Action.validate_badge_by_elements(img, params, max_rounds=2)

    assert float(params["r"]) > 5.0
    assert any("Radius-Bracketing r" in line for line in logs)


def test_validate_badge_logs_extent_bracketing_for_line_elements() -> None:
    """Validation should include explicit extent/length optimization for arm/stem elements."""
    img_path = Path("artifacts/images_to_convert/AC0812_S.jpg")
    cv2 = pytest.importorskip("cv2", exc_type=ImportError)
    img = cv2.imread(str(img_path))
    if img is None:
        pytest.skip("AC0812_S fixture image not available")

    h, w = img.shape[:2]
    params = Action._finalize_ac08_style("AC0812", Action._default_ac0812_params(w, h))
    logs = Action.validate_badge_by_elements(img, params, max_rounds=1)

    assert any("arm: Längen-Bracketing" in line for line in logs)


def test_validate_badge_continues_after_threshold_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validation should keep searching after crossing the error threshold by default."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.zeros((15, 15, 3), dtype=np.uint8)
    params = {"circle_enabled": True, "draw_text": False}

    round_errors = iter([7.5, 6.0])
    width_calls: list[int] = []

    monkeypatch.setattr(Action, "generate_badge_svg", staticmethod(lambda _w, _h, _params: "<svg/>"))
    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda _svg, w, h: np.zeros((h, w, 3), dtype=np.uint8)))
    monkeypatch.setattr(Action, "_fit_to_original_size", staticmethod(lambda _orig, render: render))
    monkeypatch.setattr(Action, "extract_badge_element_mask", staticmethod(lambda _img, _params, _element: np.ones((15, 15), dtype=np.uint8)))
    monkeypatch.setattr(Action, "_element_match_error", staticmethod(lambda *_args, **_kwargs: 0.0))
    monkeypatch.setattr(Action, "_optimize_element_width_bracket", staticmethod(lambda *_args, **_kwargs: width_calls.append(1) or True))
    monkeypatch.setattr(Action, "_optimize_element_extent_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_circle_center_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_circle_radius_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_element_color_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "calculate_error", staticmethod(lambda *_args, **_kwargs: next(round_errors)))

    logs = Action.validate_badge_by_elements(img, params, max_rounds=2)

    assert len(width_calls) == 2
    assert any("Suche nach besserem Optimum wird fortgesetzt" in line for line in logs)


def test_validate_badge_can_preserve_legacy_threshold_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicit flag should still allow the historical threshold-based early exit."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.zeros((15, 15, 3), dtype=np.uint8)
    params = {"circle_enabled": True, "draw_text": False}

    width_calls: list[int] = []

    monkeypatch.setattr(Action, "generate_badge_svg", staticmethod(lambda _w, _h, _params: "<svg/>"))
    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda _svg, w, h: np.zeros((h, w, 3), dtype=np.uint8)))
    monkeypatch.setattr(Action, "_fit_to_original_size", staticmethod(lambda _orig, render: render))
    monkeypatch.setattr(Action, "extract_badge_element_mask", staticmethod(lambda _img, _params, _element: np.ones((15, 15), dtype=np.uint8)))
    monkeypatch.setattr(Action, "_element_match_error", staticmethod(lambda *_args, **_kwargs: 0.0))
    monkeypatch.setattr(Action, "_optimize_element_width_bracket", staticmethod(lambda *_args, **_kwargs: width_calls.append(1) or False))
    monkeypatch.setattr(Action, "_optimize_element_extent_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_circle_center_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_circle_radius_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_element_color_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "calculate_error", staticmethod(lambda *_args, **_kwargs: 7.5))

    logs = Action.validate_badge_by_elements(img, params, max_rounds=2, stop_when_error_below_threshold=True)

    assert len(width_calls) == 1
    assert any("Gesamtfehler unter Schwellwert, Validierung beendet" in line for line in logs)


def test_element_error_for_circle_radius_uses_expanded_source_mask_for_growth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Circle growth probes should evaluate against an equally expanded source mask."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.zeros((25, 45, 3), dtype=np.uint8)
    params = Action._finalize_ac08_style("AC0812", Action._default_ac0812_params(45, 25))

    recorded_source_radii: list[float] = []

    monkeypatch.setattr(Action, "generate_badge_svg", staticmethod(lambda _w, _h, _p: "<svg/>"))
    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda _svg, w, h: np.zeros((h, w, 3), dtype=np.uint8)))
    monkeypatch.setattr(Action, "_fit_to_original_size", staticmethod(lambda _orig, rendered: rendered))
    monkeypatch.setattr(Action, "_element_match_error", staticmethod(lambda *_args, **_kwargs: 0.0))

    def fake_mask(_img: object, mask_params: dict, _element: str):
        if mask_params is not params:
            recorded_source_radii.append(float(mask_params.get("r", 0.0)))
        return np.ones((25, 45), dtype=bool)

    monkeypatch.setattr(Action, "extract_badge_element_mask", staticmethod(fake_mask))

    start_r = float(params["r"])
    probe_r = start_r + 2.0
    err = Action._element_error_for_circle_radius(img, params, probe_r)

    assert err == 0.0
    assert recorded_source_radii
    assert max(recorded_source_radii) >= probe_r




def test_tune_ac0834_co2_badge_recenters_tiny_variant_and_locks_strokes() -> None:
    """AC0834_S tuning should keep the badge centered and connector geometry stable."""
    params = Action._apply_co2_label(Action._default_ac0814_params(25, 15))
    params["cy"] = 10.0
    params["r"] = 5.0
    params["stroke_circle"] = 1.7
    params["arm_stroke"] = 1.6

    tuned = Action._tune_ac0834_co2_badge(params, 25, 15)

    assert abs(float(tuned["cy"]) - 7.5) < 1e-6
    assert abs(float(tuned["arm_y1"]) - float(tuned["cy"])) < 1e-6
    assert abs(float(tuned["arm_y2"]) - float(tuned["cy"])) < 1e-6
    assert float(tuned["arm_x2"]) == 25.0
    assert float(tuned["stroke_circle"]) == Action.AC08_STROKE_WIDTH_PX
    assert float(tuned["arm_stroke"]) == Action.AC08_STROKE_WIDTH_PX

def test_optimize_circle_radius_keeps_ac0813_vertical_arm_orientation() -> None:
    """AC0813 radius optimization must not collapse the vertical arm into a horizontal one."""

    class DummyImg:
        shape = (25, 15, 3)

    img = DummyImg()
    params = Action._default_ac0813_params(15, 25)
    params = Action._finalize_ac08_style("AC0813", params)
    logs: list[str] = []

    original = Action._element_error_for_circle_radius

    def prefer_smallest_radius(_img: object, _params: dict, radius_value: float) -> float:
        return float(radius_value)

    Action._element_error_for_circle_radius = staticmethod(prefer_smallest_radius)
    try:
        changed = Action._optimize_circle_radius_bracket(img, params, logs)
    finally:
        Action._element_error_for_circle_radius = original

    assert changed is True
    assert abs(float(params["arm_x1"]) - float(params["arm_x2"])) < 1e-6
    assert float(params["arm_y1"]) < float(params["arm_y2"])
    assert abs(float(params["arm_y2"]) - (float(params["cy"]) - float(params["r"]))) < 1e-6

def test_tiny_circle_radius_bracketing_limits_downscale() -> None:
    """Tiny symbols should not shrink circle radius by more than 10% in one step."""
    class DummyImg:
        shape = (15, 15, 3)

    img = DummyImg()
    params = {
        "circle_enabled": True,
        "r": 5.0,
    }
    logs: list[str] = []

    original = Action._element_error_for_circle_radius

    def prefer_smallest_radius(_img: object, _params: dict, radius_value: float) -> float:
        return float(radius_value)

    Action._element_error_for_circle_radius = staticmethod(prefer_smallest_radius)
    try:
        changed = Action._optimize_circle_radius_bracket(img, params, logs)
    finally:
        Action._element_error_for_circle_radius = original

    assert changed is True
    assert abs(float(params["r"]) - 4.5) < 1e-6
    assert any("Radius-Bracketing" in line for line in logs)


def test_circle_radius_bracketing_respects_configured_min_radius() -> None:
    """Radius optimization must not shrink below per-symbol min radius floors."""

    class DummyImg:
        shape = (20, 20, 3)

    img = DummyImg()
    params = {
        "circle_enabled": True,
        "r": 8.0,
        "min_circle_radius": 7.0,
    }
    logs: list[str] = []

    original = Action._element_error_for_circle_radius

    def prefer_smallest_radius(_img: object, _params: dict, radius_value: float) -> float:
        return float(radius_value)

    Action._element_error_for_circle_radius = staticmethod(prefer_smallest_radius)
    try:
        changed = Action._optimize_circle_radius_bracket(img, params, logs)
    finally:
        Action._element_error_for_circle_radius = original

    assert changed is True
    assert float(params["r"]) >= 7.0
    assert any("Radius-Bracketing" in line for line in logs)



def test_circle_error_uses_stable_source_mask_for_radius_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Circle radius scoring should keep the source mask tied to current params."""

    class DummyImg:
        shape = (20, 20, 3)

    img = DummyImg()
    params = {
        "circle_enabled": True,
        "r": 8.0,
        "cx": 10.0,
        "cy": 10.0,
    }

    monkeypatch.setattr(Action, "generate_badge_svg", staticmethod(lambda *_args, **_kwargs: "<svg />"))
    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda *_args, **_kwargs: object()))
    monkeypatch.setattr(Action, "_fit_to_original_size", staticmethod(lambda _img, rendered: rendered))

    calls: list[dict] = []

    def fake_extract(_img: object, mask_params: dict, _element: str):
        calls.append(mask_params)
        return [[True]]

    monkeypatch.setattr(Action, "extract_badge_element_mask", staticmethod(fake_extract))
    monkeypatch.setattr(Action, "_element_match_error", staticmethod(lambda *_args, **_kwargs: 1.0))

    err = Action._element_error_for_circle_radius(img, params, 3.5)

    assert err == 1.0
    assert len(calls) >= 2
    assert calls[0] is not params
    assert calls[1] is not params


def test_circle_color_error_uses_stable_photometric_mask(monkeypatch: pytest.MonkeyPatch) -> None:
    """Circle color bracketing should use stable source mask photometric scoring."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    mask = np.ones((20, 20), dtype=bool)
    params = {"circle_enabled": True, "cx": 10.0, "cy": 10.0, "r": 6.0, "fill_gray": 220, "stroke_gray": 127}

    monkeypatch.setattr(Action, "generate_badge_svg", staticmethod(lambda *_args, **_kwargs: "<svg />"))
    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda *_args, **_kwargs: object()))
    monkeypatch.setattr(Action, "_fit_to_original_size", staticmethod(lambda _img, rendered: rendered))

    monkeypatch.setattr(
        Action,
        "_element_match_error",
        staticmethod(lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not be called"))),
    )

    calls: list[tuple[object, object]] = []

    def fake_union(_img_a, _img_b, m1, m2):
        calls.append((m1, m2))
        return 3.0

    monkeypatch.setattr(Action, "_masked_union_error_in_bbox", staticmethod(fake_union))

    err = Action._element_error_for_color(img, params, "circle", "fill_gray", 210, mask)

    assert err == 3.0
    assert calls
    assert calls[0][0] is mask
    assert calls[0][1] is mask


def test_circle_match_error_penalizes_non_concentric_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Circle scoring should prefer concentric candidates when overlap is otherwise similar."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    params = {"cx": 10.0, "cy": 10.0, "r": 6.0}

def test_optimize_element_improves_or_keeps_score() -> None:
    target = [[0 for _ in range(16)] for _ in range(16)]
    for y in range(16):
        for x in range(16):
            if ((y - 8) ** 2 + (x - 8) ** 2) <= 16:
                target[y][x] = 1

    init = conv.Candidate(shape="circle", cx=8, cy=8, w=5, h=5)
    init_score = conv.score_candidate(target, init)
    best, best_score = conv.optimize_element(target, init, max_iter=80, plateau_limit=25, seed=123)

    assert isinstance(best, conv.Candidate)
    assert best_score >= init_score



def test_circle_match_error_penalizes_undersized_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Circle scoring should discourage candidates that shrink below source radius."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    params = {"cx": 10.0, "cy": 10.0, "r": 6.0}

    src_mask = np.zeros((20, 20), dtype=bool)
    src_mask[4:16, 4:16] = True

    undersized = np.zeros((20, 20), dtype=bool)
    undersized[6:14, 6:14] = True

    monkeypatch.setattr(Action, "_masked_union_error_in_bbox", staticmethod(lambda *_args, **_kwargs: 0.0))

    err_same = Action._element_match_error(
        img,
        img,
        params,
        "circle",
        mask_orig=src_mask,
        mask_svg=src_mask,
    )
    err_under = Action._element_match_error(
        img,
        img,
        params,
        "circle",
        mask_orig=src_mask,
        mask_svg=undersized,
    )

    assert err_under > err_same

def test_circle_pose_error_uses_element_match_scorer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Center/pose probing should go through the unified element match scorer."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    params = {"circle_enabled": True, "cx": 10.0, "cy": 10.0, "r": 6.0}

    monkeypatch.setattr(Action, "generate_badge_svg", staticmethod(lambda *_args, **_kwargs: "<svg />"))
    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda *_args, **_kwargs: object()))
    monkeypatch.setattr(Action, "_fit_to_original_size", staticmethod(lambda _img, rendered: rendered))
    monkeypatch.setattr(
        Action,
        "extract_badge_element_mask",
        staticmethod(lambda *_args, **_kwargs: np.ones((20, 20), dtype=bool)),
    )
    monkeypatch.setattr(Action, "_element_match_error", staticmethod(lambda *_args, **_kwargs: 2.5))

    err = Action._element_error_for_circle_pose(
        img,
        params,
        cx_value=10.5,
        cy_value=9.5,
        radius_value=5.5,
    )

    assert err == 2.5


def test_voc_font_scale_bounds_allow_larger_tiny_badge_labels() -> None:
    """Tiny VOC badges should allow expanding text scale beyond the historic cap."""
    params = {
        "draw_text": True,
        "text_mode": "voc",
        "voc_font_scale": 0.52,
    }

    info = Action._element_width_key_and_bounds("text", params, 15, 15)

    assert info is not None
    key, low, high = info
    assert key == "voc_font_scale"
    assert low <= 0.45
    assert high >= 1.60


def test_voc_font_scale_bounds_keep_broad_search_for_large_badges() -> None:
    """Large VOC badges should keep enough headroom for text-mask driven fitting."""
    params = {
        "draw_text": True,
        "text_mode": "voc",
        "voc_font_scale": 0.52,
    }

    info = Action._element_width_key_and_bounds("text", params, 45, 25)

    assert info is not None
    key, low, high = info
    assert key == "voc_font_scale"
    assert low <= 0.45
    assert high >= 1.60


def test_voc_font_scale_bounds_expand_from_original_text_bbox(monkeypatch: pytest.MonkeyPatch) -> None:
    """When original text extents are known, bounds should expand around that estimate."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    params = {
        "draw_text": True,
        "text_mode": "voc",
        "voc_font_scale": 0.52,
        "r": 5.0,
    }
    img = np.zeros((40, 40, 3), dtype=np.uint8)

    mask = np.zeros((40, 40), dtype=np.uint8)
    mask[10:18, 6:34] = 1  # wide/tall enough to imply larger VOC than defaults

    monkeypatch.setattr(Action, "extract_badge_element_mask", staticmethod(lambda *_args, **_kwargs: mask))

    info = Action._element_width_key_and_bounds("text", params, 40, 40, img_orig=img)

    assert info is not None
    key, low, high = info
    assert key == "voc_font_scale"
    assert low <= 0.90
    assert high >= 2.0


def test_finalize_ac08_style_caps_ac0835_s_voc_growth() -> None:
    """AC0835_S should keep VOC scale bounded to avoid heavy-looking labels."""
    params = Action._apply_voc_label(Action._default_ac0870_params(15, 15))

def test_convert_image_writes_svg(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")

    image = Image.new("L", (40, 40), 255)
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 24, 24), fill=0)
    draw.ellipse((26, 12, 36, 22), fill=0)

    src = tmp_path / "input.png"
    dst = tmp_path / "output.svg"
    image.save(src)

    conv.convert_image(src, dst, max_iter=60, plateau_limit=20, seed=7)

    text = dst.read_text(encoding="utf-8")
    assert "<svg" in text
    assert "<circle" in text or "<ellipse" in text




def test_compute_otsu_threshold_bimodal_distribution() -> None:
    grayscale = [[40 for _ in range(20)] for _ in range(10)]
    for y in range(5, 10):
        for x in range(20):
            grayscale[y][x] = 220

    threshold = conv._compute_otsu_threshold(grayscale)

    assert 40 <= threshold <= 220


def test_load_binary_image_with_mode_adaptive_detects_dark_patch(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")

    image = Image.new("L", (21, 21), 200)
    for y in range(8, 13):
        for x in range(8, 13):
            image.putpixel((x, y), 30)

    src = tmp_path / "adaptive.png"
    image.save(src)

    binary = conv.load_binary_image_with_mode(src, mode="adaptive")

    assert binary[10][10] == 1
    assert binary[0][0] == 0


def test_convert_image_accepts_threshold_mode_and_threshold(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")

def test_optimize_arm_extent_keeps_circle_side_anchor_for_horizontal_connectors() -> None:
    """Arm length optimization should keep the circle-side endpoint fixed for AC0812-like arms."""

    class DummyImg:
        shape = (15, 25, 3)

    img = DummyImg()
    params = Action._default_ac0812_params(25, 15)
    params = Action._finalize_ac08_style("AC0812", params)

    # Intentionally shrink the free-side arm to emulate under-length conversion output.
    params["arm_x1"] = float(params["arm_x2"] - 3.0)

    logs: list[str] = []
    original = Action._element_error_for_extent

    def prefer_longer(_img: object, _params: dict, _element: str, extent_value: float) -> float:
        return abs(float(extent_value) - 10.0)

    Action._element_error_for_extent = staticmethod(prefer_longer)
    try:
        changed = Action._optimize_element_extent_bracket(img, params, "arm", logs)
    finally:
        Action._element_error_for_extent = original

    assert changed is True
    assert abs(float(params["arm_x2"]) - (float(params["cx"]) - float(params["r"]))) < 1e-6
    assert float(params["arm_x1"]) < float(params["arm_x2"])
    assert any("arm: Längen-Bracketing" in line for line in logs)


def test_estimate_stroke_style_detects_dark_ring() -> None:
    grayscale = [[255 for _ in range(25)] for _ in range(25)]
    pixels = [[0 for _ in range(21)] for _ in range(21)]

    cx = cy = 10
    for y in range(21):
        for x in range(21):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= 100:
                pixels[y][x] = 1
                if d2 >= 72:
                    grayscale[y + 2][x + 2] = 120
                else:
                    grayscale[y + 2][x + 2] = 210

    element = conv.Element(pixels=pixels, x0=2, y0=2, x1=22, y1=22)
    candidate = conv.Candidate(shape="circle", cx=10, cy=10, w=20, h=20)

    fill, stroke, stroke_width = conv.estimate_stroke_style(grayscale, element, candidate)

    assert fill == "#d2d2d2"
    assert stroke == "#787878"
    assert stroke_width == pytest.approx(2.0, rel=0.35)

def test_optimize_stem_extent_keeps_circle_side_anchor() -> None:
    """Stem length optimization should keep stem_top attached to the circle edge."""




def test_candidate_to_svg_preserves_outer_size_with_stroke() -> None:
    candidate = conv.Candidate(shape="circle", cx=10.0, cy=10.0, w=20.0, h=20.0)

    svg = conv.candidate_to_svg(candidate, 0, 0, "#dbdbdb", "#808080", 2.0)

    assert 'r="9.00"' in svg
    assert 'stroke-width="2.00"' in svg


def test_decompose_circle_with_stem_detects_bottom_stem() -> None:
    size = 25
    grayscale = [[255 for _ in range(size)] for _ in range(size)]
    pixels = [[0 for _ in range(size)] for _ in range(size)]

    cx = cy = 12
    r = 8
    for y in range(size):
        for x in range(size):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= r * r:
                pixels[y][x] = 1
                grayscale[y][x] = 215

    for y in range(20, 24):
        for x in range(11, 14):
            pixels[y][x] = 1
            grayscale[y][x] = 128

    element = conv.Element(pixels=pixels, x0=0, y0=0, x1=24, y1=24)
    candidate = conv.Candidate(shape="circle", cx=12, cy=12, w=16, h=16)

    parts = conv.decompose_circle_with_stem(grayscale, element, candidate)

    assert parts is not None
    assert len(parts) == 2
    assert parts[0].startswith("<rect ")
    assert 'fill="#' in parts[0]
    assert parts[1].startswith("<circle ")


def test_decompose_circle_with_stem_ignores_plain_circle() -> None:
    size = 30
    grayscale = [[255 for _ in range(size)] for _ in range(size)]
    pixels = [[0 for _ in range(size)] for _ in range(size)]

    cx = cy = 14
    r = 12
    for y in range(size):
        for x in range(size):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= r * r:
                pixels[y][x] = 1
                grayscale[y][x] = 180

    element = conv.Element(pixels=pixels, x0=0, y0=0, x1=size - 1, y1=size - 1)
    candidate = conv.Candidate(shape="circle", cx=cx, cy=cy, w=r * 2, h=r * 2)

    parts = conv.decompose_circle_with_stem(grayscale, element, candidate)

    assert parts is None

def test_optimize_stem_extent_keeps_bottom_anchored_ac0811_stem_from_collapsing() -> None:
    """Bottom-anchored AC0811 stems should retain a minimum visible length during bracketing."""

    if image_composite_converter.np is None:
        pytest.skip("numpy not available in this environment")

    np = image_composite_converter.np
    img = np.zeros((15, 15, 3), dtype=np.uint8)
    params = Action._default_ac0811_params(15, 15)
    logs: list[str] = []

    params["draw_text"] = False
    params["stem_bottom"] = 15.0
    params["stem_top"] = 9.0

    original = Action._element_error_for_extent
    try:
        Action._element_error_for_extent = staticmethod(lambda *_args, **_kwargs: 0.0)
        changed = Action._optimize_element_extent_bracket(img, params, "stem", logs)
    finally:
        Action._element_error_for_extent = original

    assert changed is True
    assert float(params["stem_bottom"]) == 15.0
    assert float(params["stem_bottom"]) - float(params["stem_top"]) >= 5.5


def test_decompose_circle_with_stem_recenters_vertical_stem() -> None:
    size = 31
    grayscale = [[255 for _ in range(size)] for _ in range(size)]
    pixels = [[0 for _ in range(size)] for _ in range(size)]

    cx = cy = 15
    r = 9
    for y in range(size):
        for x in range(size):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= r * r:
                pixels[y][x] = 1
                grayscale[y][x] = 210

    for y in range(24, 29):
        for x in range(17, 20):
            pixels[y][x] = 1
            grayscale[y][x] = 120

    element = conv.Element(pixels=pixels, x0=0, y0=0, x1=size - 1, y1=size - 1)
    candidate = conv.Candidate(shape="circle", cx=15, cy=15, w=18, h=18)

    parts = conv.decompose_circle_with_stem(grayscale, element, candidate)
    assert parts is not None
    rect = parts[0]

    import re

    mx = re.search(r'x="([0-9.]+)"', rect)
    my = re.search(r'y="([0-9.]+)"', rect)
    mw = re.search(r'width="([0-9.]+)"', rect)
    assert mx and my and mw


def test_fit_ac0811_preserves_visible_stem_when_circle_estimate_reaches_bottom() -> None:
    """AC0811 fitting should keep at least a small visible stem segment."""

    class DummyImg:
        shape = (15, 15, 3)

    img = DummyImg()
    defaults = Action._default_ac0811_params(15, 15)

    original_fit = Action._fit_semantic_badge_from_image
    original_upper = Action._estimate_upper_circle_from_foreground
    try:
        Action._fit_semantic_badge_from_image = staticmethod(
            lambda _img, _defaults: {
                **dict(defaults),
                "cx": float(defaults["cx"]),
                "cy": float(defaults["cy"]),
                # Simulate a noisy fit where the circle radius grows so much
                # that stem_top would otherwise land at/below image bottom.
                "r": float(img.shape[0]),
                "stem_width": float(defaults["stem_width"]),
            }
        )
        Action._estimate_upper_circle_from_foreground = staticmethod(lambda _img, _defaults: None)

        params = Action._fit_ac0811_params_from_image(img, defaults)
    finally:
        Action._fit_semantic_badge_from_image = original_fit
        Action._estimate_upper_circle_from_foreground = original_upper

    assert float(params["stem_bottom"]) == float(img.shape[0])
    assert float(params["stem_top"]) <= float(img.shape[0]) - 1.0
    assert float(params["stem_bottom"]) - float(params["stem_top"]) >= 1.0


def test_estimate_vertical_stem_from_mask_ignores_circle_junction_bulge() -> None:
    """Stem width estimate should prefer the lower stem over top junction bulges."""


    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    mask = np.zeros((20, 15), dtype=bool)

    # Simulate anti-aliased widening near the circle/stem transition.
    mask[0:6, 4:11] = True   # wide top bulge (7 px)
    mask[6:20, 6:9] = True   # actual slim stem (3 px)

    est = Action._estimate_vertical_stem_from_mask(mask, expected_cx=7.0, y_start=0, y_end=20)
    assert est is not None

    est_cx, est_width = est
    assert abs(float(est_cx) - 7.0) <= 0.6
    assert abs(float(est_width) - 3.0) <= 0.25

def test_text_width_bracketing_keeps_fractional_font_scale_precision() -> None:
    """Text scale optimization should not quantize font scale to half-pixel steps."""

    class DummyImg:
        shape = (30, 30, 3)

    img = DummyImg()
    params = {
        "draw_text": True,
        "text_mode": "voc",
        "voc_font_scale": 0.52,
    }
    logs: list[str] = []



def test_decompose_circle_with_stem_recenters_horizontal_stem() -> None:
    size = 31
    grayscale = [[255 for _ in range(size)] for _ in range(size)]
    pixels = [[0 for _ in range(size)] for _ in range(size)]

    cx = cy = 15
    r = 9
    for y in range(size):
        for x in range(size):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= r * r:
                pixels[y][x] = 1
                grayscale[y][x] = 210

    for y in range(17, 20):
        for x in range(24, 29):
            pixels[y][x] = 1
            grayscale[y][x] = 120

    element = conv.Element(pixels=pixels, x0=0, y0=0, x1=size - 1, y1=size - 1)
    candidate = conv.Candidate(shape="circle", cx=15, cy=15, w=18, h=18)

    parts = conv.decompose_circle_with_stem(grayscale, element, candidate)

    assert parts is not None
    rect = parts[0]
    assert rect.startswith("<rect ")

    import re

    mx = re.search(r'x="([0-9.]+)"', rect)
    my = re.search(r'y="([0-9.]+)"', rect)
    mh = re.search(r'height="([0-9.]+)"', rect)
    assert mx and my and mh

    stem_x = float(mx.group(1))
    stem_y = float(my.group(1))
    stem_h = float(mh.group(1))
    stem_cy = stem_y + stem_h / 2.0

    assert stem_x >= 23.8
    assert abs(stem_cy - 15.0) <= 0.2

def test_generate_badges_reconverted_svg_contains_text(tmp_path: Path) -> None:
    gen = pytest.importorskip("tools.generate_badge_comparison_set")

    class DummyImg:
        shape = (30, 30, 3)

    img = DummyImg()
    params = {
        "draw_text": True,
        "text_mode": "voc",
        "voc_font_scale": 0.52,
    }
    logs: list[str] = []
    original = Action._element_error_for_width

    def prefer_target_scale(_img: object, _params: dict, _element: str, width_value: float) -> float:
        return abs(float(width_value) - 0.85)

    Action._element_error_for_width = staticmethod(prefer_target_scale)
    try:
        changed = Action._optimize_element_width_bracket(img, params, "text", logs)
    finally:
        Action._element_error_for_width = original

    assert changed is True
    assert abs(float(params["voc_font_scale"]) - 0.52) > 0.05
    assert abs((float(params["voc_font_scale"]) * 2.0) - round(float(params["voc_font_scale"]) * 2.0)) > 1e-6
    assert any("Breiten-Bracketing" in line for line in logs)


def test_co2_layout_prioritizes_co_centering_before_cluster_centering() -> None:
    """center_co mode should keep the main CO run centered, even with a large subscript."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params["co2_anchor_mode"] = "center_co"
    params["co2_sub_font_scale"] = 130.0

    layout = Action._co2_layout(params)
    cx = float(params["cx"])
    r = float(params["r"])
    stroke = float(params["stroke_circle"])
    inner_padding = float(params.get("co2_inner_padding_px", 0.35))

    inner_left = cx - max(1.0, r - stroke) + inner_padding
    inner_right = cx + max(1.0, r - stroke) - inner_padding

    assert abs(float(layout["co_x"]) - cx) <= 0.20
    assert float(layout["x1"]) >= inner_left - 1e-6
    assert float(layout["x2"]) <= inner_right + 1e-6


def test_co2_layout_can_shrink_subscript_before_moving_co() -> None:
    """When space is tight, subscript should shrink to preserve CO placement first."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params = Action._finalize_ac08_style("AC0820_M", params)
    params["co2_sub_font_scale"] = 160.0

    requested_sub_font_px = max(4.0, float(params["r"]) * float(params["co2_font_scale"]) * (float(params["co2_sub_font_scale"]) / 100.0))
    layout = Action._co2_layout(params)

    assert float(layout["sub_font_px"]) < requested_sub_font_px

def test_co2_layout_caps_font_size_to_inner_circle_ratio() -> None:
    """CO font size must stay proportionate even for inflated co2_font_scale values."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820_L", params)
    params["co2_font_scale"] = 1.50
    layout = Action._co2_layout(params)

    r = float(params["r"])
    stroke = float(params["stroke_circle"])
    inner_diameter = (2.0 * r) - stroke
    assert float(layout["font_size"]) <= (inner_diameter * 0.50) + 1e-6


def test_co2_text_width_bracketing_is_bounded_for_ac0820() -> None:
    """AC0820 CO₂ badges should allow bounded text tuning during width bracketing."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820", params)

    key, low, high = Action._element_width_key_and_bounds("text", params, 30, 30)
    assert key == "co2_font_scale"
    assert float(low) <= float(params["co2_font_scale"]) <= float(high)
    assert float(low) >= float(params["co2_font_scale_min"]) - 1e-9
    assert float(high) <= float(params["co2_font_scale_max"]) + 1e-9


def test_finalize_ac0820_locks_palette_against_color_bracketing() -> None:
    """AC08xx semantic badges should keep canonical fill/stroke grayscale values."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820", params)

    assert params["lock_colors"] is True


def test_optimize_element_color_bracket_skips_when_colors_locked() -> None:
    """Color tuning must be skipped when lock_colors is enabled."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.zeros((8, 8, 3), dtype=np.uint8)
    mask = np.ones((8, 8), dtype=np.uint8)
    params = {
        "circle_enabled": True,
        "fill_gray": 242,
        "stroke_gray": 127,
        "lock_colors": True,
    }
    logs: list[str] = []

    changed = Action._optimize_element_color_bracket(img, params, "circle", mask, logs)

    assert changed is False
    assert any("Farben gesperrt" in line for line in logs)

def test_validate_badge_runs_color_bracketing_after_geometry_steps() -> None:
    """Validation should optimize color only after extent/radius geometry updates."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    class DummyImg:
        shape = (15, 15, 3)

    img = DummyImg()
    params = {"circle_enabled": True, "draw_text": False}
    call_order: list[str] = []

    original_generate_badge_svg = Action.generate_badge_svg
    original_render_svg_to_numpy = Action.render_svg_to_numpy
    original_fit_to_original_size = Action._fit_to_original_size
    original_extract_badge_element_mask = Action.extract_badge_element_mask
    original_mask_min_rect_center_diag = Action._mask_min_rect_center_diag
    original_masked_error = Action._masked_error
    original_calculate_error = Action.calculate_error
    original_width = Action._optimize_element_width_bracket
    original_extent = Action._optimize_element_extent_bracket
    original_center = Action._optimize_circle_center_bracket
    original_radius = Action._optimize_circle_radius_bracket
    original_color = Action._optimize_element_color_bracket

    Action.generate_badge_svg = staticmethod(lambda _w, _h, _params: "<svg/>")
    Action.render_svg_to_numpy = staticmethod(lambda _svg, w, h: np.zeros((h, w, 3), dtype=np.uint8))
    Action._fit_to_original_size = staticmethod(lambda _orig, render: render)
    Action.extract_badge_element_mask = staticmethod(lambda _img, _params, _element: np.ones((15, 15), dtype=np.uint8))
    Action._mask_min_rect_center_diag = staticmethod(lambda _mask: None)
    Action._masked_error = staticmethod(lambda _orig, _render, _mask: 0.0)
    Action.calculate_error = staticmethod(lambda _orig, _render: 0.0)

    Action._optimize_element_width_bracket = staticmethod(
        lambda _img, _params, _element, _logs: call_order.append("width") or False
    )
    Action._optimize_element_extent_bracket = staticmethod(
        lambda _img, _params, _element, _logs: call_order.append("extent") or False
    )
    Action._optimize_circle_center_bracket = staticmethod(
        lambda _img, _params, _logs: call_order.append("center") or False
    )
    Action._optimize_circle_radius_bracket = staticmethod(
        lambda _img, _params, _logs: call_order.append("radius") or False
    )
    Action._optimize_element_color_bracket = staticmethod(
        lambda _img, _params, _element, _mask, _logs: call_order.append("color") or False
    )

    try:
        Action.validate_badge_by_elements(img, params, max_rounds=1)
    finally:
        Action.generate_badge_svg = original_generate_badge_svg
        Action.render_svg_to_numpy = original_render_svg_to_numpy
        Action._fit_to_original_size = original_fit_to_original_size
        Action.extract_badge_element_mask = original_extract_badge_element_mask
        Action._mask_min_rect_center_diag = original_mask_min_rect_center_diag
        Action._masked_error = original_masked_error
        Action.calculate_error = original_calculate_error
        Action._optimize_element_width_bracket = original_width
        Action._optimize_element_extent_bracket = original_extent
        Action._optimize_circle_center_bracket = original_center
        Action._optimize_circle_radius_bracket = original_radius
        Action._optimize_element_color_bracket = original_color

    assert call_order == ["width", "extent", "center", "radius", "color"]


def test_optimize_circle_pose_multistart_can_escape_local_center_radius_plateau(monkeypatch: pytest.MonkeyPatch) -> None:
    """Joint circle pose search should improve cx/cy/r together when independent steps stall."""

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    params = {
        "circle_enabled": True,
        "cx": 10.0,
        "cy": 10.0,
        "r": 6.0,
        "min_circle_radius": 4.0,
    }
    logs: list[str] = []

    def fake_error(_img, _params, *, cx_value: float, cy_value: float, radius_value: float) -> float:
        return ((cx_value - 11.0) ** 2) + ((cy_value - 9.0) ** 2) + ((radius_value - 6.5) ** 2)

    monkeypatch.setattr(Action, "_element_error_for_circle_pose", staticmethod(fake_error))

    changed = Action._optimize_circle_pose_multistart(img, params, logs)

    assert changed is True
    assert float(params["cx"]) == 11.0
    assert float(params["cy"]) == 9.0
    assert float(params["r"]) == 6.5
    assert any("Joint-Multistart" in line for line in logs)


def test_make_badge_params_supports_ac0810_variants() -> None:
    """AC0810 and variant names should map to the semantic right-arm badge model."""
    params = Action.make_badge_params(25, 15, "AC0810")

    assert params is not None
    assert params.get("arm_enabled") is True
    assert float(params["arm_x2"]) > float(params["arm_x1"])
    assert float(params["arm_x2"]) >= 22.0


def test_parse_description_marks_ac0810_as_semantic_badge() -> None:
    """Reflection parsing should treat AC0810 as a semantic circle+right-arm badge."""
    desc, params = image_composite_converter.Reflection({}).parse_description("AC0810", "AC0810_L.jpg")

    assert desc == ""
    assert params["mode"] == "semantic_badge"
    assert "SEMANTIC: Kreis ohne Buchstabe" in params["elements"]
    assert "SEMANTIC: waagrechter Strich rechts vom Kreis" in params["elements"]


def test_parse_description_marks_ac0811_as_semantic_badge() -> None:
    """Reflection parsing should treat AC0811 as a semantic circle+down-stem badge."""
    desc, params = image_composite_converter.Reflection({}).parse_description("AC0811", "AC0811_L.jpg")

    assert desc == ""
    assert params["mode"] == "semantic_badge"
    assert "SEMANTIC: Kreis ohne Buchstabe" in params["elements"]
    assert "SEMANTIC: senkrechter Strich hinter dem Kreis" in params["elements"]


def test_parse_description_keeps_ac0814_family_rule_over_text_heuristic() -> None:
    """AC0811-AC0814 family rules must outrank soft description hints about badge text."""
    raw = {
        "AC0814": "Kreis ohne Buchstabe",
        "AC0814_L": "Kreis mit Buchstabe CO2 und waagrechter Strich rechts",
    }

    _desc, params = image_composite_converter.Reflection(raw).parse_description("AC0814", "AC0814_L.jpg")

    assert "SEMANTIC: Kreis ohne Buchstabe" in params["elements"]
    assert not any("Kreis + Buchstabe" in element for element in params["elements"])
    assert params["semantic_priority_order"] == ["family_rule", "layout_override", "description_heuristic"]
    assert "family_rule_kept_circle_without_letter_over_description_text=SEMANTIC: Kreis + Buchstabe CO_2" in params["semantic_conflicts"]


def test_validate_semantic_alignment_accepts_merged_co2_blob_for_ac0831_artifact() -> None:
    """Merged JPEG text blobs should still count as valid CO₂ evidence for AC0831_L."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    cv2 = image_composite_converter.cv2
    img = cv2.imread("artifacts/images_to_convert/AC0831_L.jpg")
    assert img is not None

    params = Action.make_badge_params(img.shape[1], img.shape[0], "AC0831", img)
    issues = Action.validate_semantic_description_alignment(
        img,
        ["SEMANTIC: Kreis + Buchstabe CO_2", "SEMANTIC: senkrechter Strich hinter dem Kreis"],
        params,
    )

    assert "Strukturprüfung: Erwartete CO₂-Glyphenstruktur nicht ausreichend belegt" not in issues


@pytest.mark.parametrize(
    ("symbol", "expected_element"),
    [
        ("AC0814", "SEMANTIC: waagrechter Strich rechts vom Kreis"),
        ("AC0834", "SEMANTIC: waagrechter Strich rechts vom Kreis"),
        ("AC0837", "SEMANTIC: waagrechter Strich links vom Kreis"),
        ("AC0831", "SEMANTIC: senkrechter Strich hinter dem Kreis"),
    ],
)
def test_parse_description_infers_semantic_connectors_for_derived_ac08_badges(symbol: str, expected_element: str) -> None:
    """Derived AC08 badges should carry the same connector semantics as their base geometry."""
    _desc, params = image_composite_converter.Reflection({}).parse_description(symbol, f"{symbol}_L.jpg")

    assert params["mode"] == "semantic_badge"
    assert expected_element in params["elements"]


def test_template_transfer_skips_nonsemantic_donors_for_semantic_targets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Semantic target badges must not accept generic donor transforms that can drop connector semantics."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2

    folder = tmp_path / "images"
    svg_dir = tmp_path / "svg"
    diff_dir = tmp_path / "diff"
    folder.mkdir()
    svg_dir.mkdir()
    diff_dir.mkdir()

    img = np.full((25, 45, 3), 240, dtype=np.uint8)
    target_filename = "AC0812_L.jpg"
    cv2.imwrite(str(folder / target_filename), img)

    target_params = Action.make_badge_params(45, 25, "AC0812")
    assert target_params is not None
    target_params["mode"] = "semantic_badge"
    target_svg = Action.generate_badge_svg(45, 25, target_params)
    (svg_dir / "AC0812_L.svg").write_text(target_svg, encoding="utf-8")

    donor_params = Action.make_badge_params(30, 30, "AC0800")
    assert donor_params is not None
    donor_params["mode"] = "auto"
    donor_svg = Action.generate_badge_svg(30, 30, donor_params)
    (svg_dir / "AC0800_S.svg").write_text(donor_svg, encoding="utf-8")

    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda _svg, w, h: np.full((h, w, 3), 240, dtype=np.uint8)))
    monkeypatch.setattr(Action, "calculate_error", staticmethod(lambda _a, _b: 0.0))
    monkeypatch.setattr(Action, "create_diff_image", staticmethod(lambda a, _b: a.copy()))

    target_row = {
        "filename": target_filename,
        "variant": "AC0812_L",
        "base": "AC0812",
        "params": target_params,
        "best_error": 9999.0,
        "error_per_pixel": 1.0,
        "w": 45,
        "h": 25,
    }
    donor_rows = [
        {
            "variant": "AC0800_S",
            "base": "AC0800",
            "params": donor_params,
            "error_per_pixel": 0.01,
            "w": 30,
            "h": 30,
        }
    ]

    updated_row, detail = image_composite_converter._try_template_transfer(
        target_row=target_row,
        donor_rows=donor_rows,
        folder_path=str(folder),
        svg_out_dir=str(svg_dir),
        diff_out_dir=str(diff_dir),
        rng=None,
    )

    assert updated_row is None
    assert detail is None


def test_template_transfer_skips_semantic_but_incompatible_donors_for_connector_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Semantic transfer should reject semantic donors that cannot preserve connector geometry."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    cv2 = image_composite_converter.cv2

    folder = tmp_path / "images"
    svg_dir = tmp_path / "svg"
    diff_dir = tmp_path / "diff"
    folder.mkdir()
    svg_dir.mkdir()
    diff_dir.mkdir()

    img = np.full((25, 45, 3), 240, dtype=np.uint8)
    target_filename = "AC0812_L.jpg"
    cv2.imwrite(str(folder / target_filename), img)

    target_params = Action.make_badge_params(45, 25, "AC0812")
    assert target_params is not None
    target_params["mode"] = "semantic_badge"
    (svg_dir / "AC0812_L.svg").write_text(Action.generate_badge_svg(45, 25, target_params), encoding="utf-8")

    # Semantic donor without arm connector (plain circle).
    donor_params = Action.make_badge_params(30, 30, "AC0870")
    assert donor_params is not None
    donor_params["mode"] = "semantic_badge"
    (svg_dir / "AC0870_S.svg").write_text(Action.generate_badge_svg(30, 30, donor_params), encoding="utf-8")

    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda _svg, w, h: np.full((h, w, 3), 240, dtype=np.uint8)))
    monkeypatch.setattr(Action, "calculate_error", staticmethod(lambda _a, _b: 0.0))
    monkeypatch.setattr(Action, "create_diff_image", staticmethod(lambda a, _b: a.copy()))

    target_row = {
        "filename": target_filename,
        "variant": "AC0812_L",
        "base": "AC0812",
        "params": target_params,
        "best_error": 9999.0,
        "error_per_pixel": 1.0,
        "w": 45,
        "h": 25,
    }
    donor_rows = [
        {
            "variant": "AC0870_S",
            "base": "AC0870",
            "params": donor_params,
            "error_per_pixel": 0.01,
            "w": 30,
            "h": 30,
        }
    ]

    updated_row, detail = image_composite_converter._try_template_transfer(
        target_row=target_row,
        donor_rows=donor_rows,
        folder_path=str(folder),
        svg_out_dir=str(svg_dir),
        diff_out_dir=str(diff_dir),
        rng=None,
    )

    assert updated_row is None
    assert detail is None


def test_semantic_transfer_rejects_opposite_arm_directions() -> None:
    """Semantic transfer must not mix right-arm donors into left-arm targets."""
    target = Action.make_badge_params(45, 25, "AC0812")
    donor = Action.make_badge_params(45, 25, "AC0810")

    assert target is not None
    assert donor is not None
    assert target.get("arm_enabled") is True
    assert donor.get("arm_enabled") is True

    assert image_composite_converter._semantic_transfer_is_compatible(target, donor) is False


def test_enforce_semantic_connector_expectation_restores_left_arm_for_ac0812() -> None:
    params = {
        "circle_enabled": True,
        "cx": 32.5,
        "cy": 12.5,
        "r": 8.0,
        "arm_enabled": False,
    }

    restored = Action._enforce_semantic_connector_expectation(
        "AC0812",
        ["SEMANTIC: Kreis ohne Buchstabe", "SEMANTIC: waagrechter Strich links vom Kreis"],
        params,
        45,
        25,
    )

    assert restored["arm_enabled"] is True
    assert float(restored["arm_x1"]) == 0.0
    assert abs(float(restored["arm_x2"]) - (float(restored["cx"]) - float(restored["r"]))) < 1e-6


def test_enforce_semantic_connector_expectation_handles_variant_base_name_for_ac0812() -> None:
    """Variant names (AC0812_L/M/S) should still trigger left-arm semantic guard."""
    params = {
        "circle_enabled": True,
        "cx": 32.5,
        "cy": 12.5,
        "r": 8.0,
        "arm_enabled": False,
    }

    restored = Action._enforce_semantic_connector_expectation(
        "AC0812_L",
        ["SEMANTIC: Kreis ohne Buchstabe", "SEMANTIC: waagrechter Strich links vom Kreis"],
        params,
        45,
        25,
    )

    assert restored["arm_enabled"] is True
    assert float(restored["arm_x1"]) == 0.0
    assert abs(float(restored["arm_x2"]) - (float(restored["cx"]) - float(restored["r"]))) < 1e-6


def test_optimize_circle_pose_adaptive_domain_logs_random_domain_steps() -> None:

    class DummyImg:
        shape = (25, 45, 3)

    img = DummyImg()
    params = Action._default_ac0812_params(45, 25)
    params = Action._finalize_ac08_style("AC0812", params)

    original_eval = Action._element_error_for_circle_pose

    def paraboloid(_img: object, _params: dict, *, cx_value: float, cy_value: float, radius_value: float) -> float:
        return (
            ((float(cx_value) - 32.5) ** 2)
            + ((float(cy_value) - 12.5) ** 2)
            + ((float(radius_value) - 8.0) ** 2)
        )

    logs: list[str] = []
    Action._element_error_for_circle_pose = staticmethod(paraboloid)
    try:
        changed = Action._optimize_circle_pose_adaptive_domain(
            img,
            params,
            logs,
            rounds=2,
            samples_per_round=8,
        )
    finally:
        Action._element_error_for_circle_pose = original_eval

    assert changed is True
    assert any("Möglichkeitsraum" in line for line in logs)
    assert any("random-samples" in line for line in logs)
    assert any("Möglichkeitsraum eingegrenzt" in line for line in logs)


def test_clip_scalar_inverted_bounds_collapse_to_upper_bound() -> None:
    """Scalar clip fallback should mirror numpy for inverted bounds (low > high)."""
    assert _clip(3.0, 5.0, 2.0) == 2.0
    assert _clip(8.0, 5.0, 2.0) == 2.0


def test_circle_sampling_clip_preserves_upper_cap_with_inverted_bounds() -> None:
    """Inverted circle radius bounds should still clamp sampled radii to the upper cap."""
    params = {"shape": "circle", "cx": 12.0, "cy": 12.0, "r": 10.0, "min_circle_radius": 20.0}
    _x_low, _x_high, _y_low, _y_high, r_low, r_high = Action._circle_bounds(params, w=24, h=24)

    assert r_low > r_high
    assert _clip(100.0, r_low, r_high) == r_high


def test_parse_args_allows_two_positional_paths_with_default_iterations() -> None:
    """CLI should accept `folder output_dir` without requiring iterations."""
    args = conv.parse_args(["in_folder", "out_folder"])

    assert args.folder_path == "in_folder"
    assert args.csv_or_output == "out_folder"
    assert int(args.iterations) == 128


def test_parse_args_keeps_legacy_three_positional_arguments() -> None:
    """Backward compatibility: `folder csv iterations` still parses unchanged."""
    args = conv.parse_args(["in_folder", "table.csv", "64"])

    assert args.folder_path == "in_folder"
    assert args.csv_or_output == "table.csv"
    assert int(args.iterations) == 64


def test_parse_args_accepts_log_file_option() -> None:
    args = conv.parse_args(["in_folder", "out_folder", "--log-file", "run.log"])
    assert args.log_file == "run.log"


def test_parse_args_accepts_ac08_regression_set_flag() -> None:
    args = conv.parse_args(["in_folder", "--ac08-regression-set"])

    assert args.ac08_regression_set is True


def test_parse_args_uses_console_prompt_defaults_for_missing_range() -> None:
    args = conv.parse_args(["in_folder"])

    assert args.start is None
    assert args.end is None


def test_main_prompts_for_range_when_start_and_end_are_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    prompts: list[str] = []
    monkeypatch.setattr(conv, "_resolve_cli_csv_and_output", lambda _args: ("", "out_dir"))
    monkeypatch.setattr(conv, "convert_range", lambda *_args, **_kwargs: "out_dir")
    monkeypatch.setattr(conv, "_optional_log_capture", lambda _path: contextlib.nullcontext())

    answers = iter(["AC0001", "AC0003"])

    def fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr("builtins.input", fake_input)

    rc = conv.main(["images"])

    assert rc == 0
    assert prompts == ["Namen von: ", "Namen bis: "]


def test_main_skips_range_prompt_when_start_and_end_are_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(conv, "_resolve_cli_csv_and_output", lambda _args: ("", "out_dir"))
    monkeypatch.setattr(conv, "convert_range", lambda *_args, **_kwargs: "out_dir")
    monkeypatch.setattr(conv, "_optional_log_capture", lambda _path: contextlib.nullcontext())

    def fail_input(_prompt: str) -> str:
        raise AssertionError("input should not be called")

    monkeypatch.setattr("builtins.input", fail_input)

    rc = conv.main(["images", "--start", "AC0001", "--end", "AC0003"])

    assert rc == 0


def test_main_uses_fixed_ac08_regression_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(conv, "_resolve_cli_csv_and_output", lambda _args: ("table.csv", "out_dir"))
    monkeypatch.setattr(conv, "_optional_log_capture", lambda _path: contextlib.nullcontext())
    captured: dict[str, object] = {}

    def fake_convert_range(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return "out_dir"

    monkeypatch.setattr(conv, "convert_range", fake_convert_range)

    rc = conv.main(["images", "--ac08-regression-set"])

    assert rc == 0
    assert captured["args"][3] == "AC0000"
    assert captured["args"][4] == "ZZ9999"
    assert captured["args"][7] == "out_dir"
    assert captured["args"][8] == set(conv.AC08_REGRESSION_VARIANTS)


def test_optional_log_capture_writes_output_to_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    log_path = tmp_path / "run.log"

    with conv._optional_log_capture(str(log_path)):
        print("hello-capture")

    console = capsys.readouterr()
    assert "hello-capture" in console.out
    written = log_path.read_text(encoding="utf-8")
    assert "[INFO] Schreibe Konsolen-Output nach:" in written
    assert "hello-capture" in written


def test_resolve_cli_csv_and_output_autodetects_csv_when_second_arg_is_output(tmp_path: Path) -> None:
    """When called as `folder output`, CSV should be auto-detected from input folder."""
    in_dir = tmp_path / "images"
    in_dir.mkdir()
    out_dir = tmp_path / "converted"
    csv_file = in_dir / "reference_roundtrip.csv"
    csv_file.write_text("Wurzelform;Beschreibung\n", encoding="utf-8")

    args = conv.parse_args([str(in_dir), str(out_dir)])
    csv_path, output_dir = conv._resolve_cli_csv_and_output(args)

    assert csv_path == str(csv_file)
    assert output_dir == str(out_dir)


def test_resolve_cli_csv_and_output_keeps_explicit_csv_over_autodetect(tmp_path: Path) -> None:
    in_dir = tmp_path / "images"
    in_dir.mkdir()
    (in_dir / "reference_roundtrip.csv").write_text("Wurzelform;Beschreibung\n", encoding="utf-8")
    explicit = tmp_path / "explicit.csv"
    explicit.write_text("Wurzelform;Beschreibung\n", encoding="utf-8")

    args = conv.parse_args([str(in_dir), "out_dir", "32", "--csv-path", str(explicit)])
    csv_path, output_dir = conv._resolve_cli_csv_and_output(args)

    assert csv_path == str(explicit)
    assert output_dir == "out_dir"


def test_default_converted_symbols_root_points_to_converted_images() -> None:
    root = Path(conv._default_converted_symbols_root())

    assert root.name == "converted_images"
    assert root.parent.name == "artifacts"


def test_conversion_output_subdirectories_live_below_root() -> None:
    root = Path("/tmp/example-output")

    assert Path(conv._converted_svg_output_dir(str(root))) == root / "converted_svgs"
    assert Path(conv._diff_output_dir(str(root))) == root / "diff_pngs"
    assert Path(conv._reports_output_dir(str(root))) == root / "reports"


def test_render_embedded_raster_svg_wraps_gif_without_optional_deps(tmp_path: Path) -> None:
    gif_path = tmp_path / "sample.gif"
    gif_path.write_bytes(
        b"GIF89a"
        + bytes([2, 0, 3, 0])
        + b"\x80\x00\x00"
        + b"\x00\x00\x00\xff\xff\xff"
        + b",\x00\x00\x00\x00\x02\x00\x03\x00\x00\x02\x02D\x01\x00;"
    )

    svg = conv._render_embedded_raster_svg(gif_path)

    assert 'width="2"' in svg
    assert 'height="3"' in svg
    assert "data:image/gif;base64," in svg


def test_convert_image_fallback_writes_embedded_svg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jpg_path = tmp_path / "sample.jpg"
    jpg_path.write_bytes(
        b"\xff\xd8"
        + b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        + b"\xff\xc0\x00\x11\x08\x00\x04\x00\x05\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01"
        + b"\xff\xd9"
    )
    out_path = tmp_path / "sample.svg"
    monkeypatch.setattr(image_composite_converter, "cv2", None)
    monkeypatch.setattr(image_composite_converter, "np", None)

    result = conv.convert_image(jpg_path, out_path)

    assert result == out_path
    text = out_path.read_text(encoding="utf-8")
    assert 'viewBox="0 0 5 4"' in text
    assert "data:image/jpeg;base64," in text


def test_load_description_mapping_from_xml_reads_wurzelform_key_and_images(tmp_path: Path) -> None:
    xml_path = tmp_path / "Finale_Wurzelformen_V3.xml"
    xml_path.write_text(
        """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<wurzelformen_export>
  <entries>
    <entry kind=\"symbol\" key=\"AC0812_L\">
      <wurzelform>AC0812</wurzelform>
      <beschreibung>Semantic badge sample</beschreibung>
      <bilder>
        <bild>AC0812_L.jpg</bild>
        <bild>AC0812_M.jpg</bild>
      </bilder>
    </entry>
  </entries>
</wurzelformen_export>
""",
        encoding="utf-8",
    )

    mapping = conv._load_description_mapping(str(xml_path))

    assert mapping["AC0812"] == "Semantic badge sample"
    assert mapping["AC0812_L"] == "Semantic badge sample"
    assert mapping["AC0812_M"] == "Semantic badge sample"


def test_load_existing_conversion_rows_reads_prior_iteration_log(tmp_path: Path) -> None:
    output_root = tmp_path / "converted"
    reports_dir = output_root / "reports"
    svg_dir = output_root / "converted_svgs"
    images_dir = tmp_path / "images"
    reports_dir.mkdir(parents=True)
    svg_dir.mkdir(parents=True)
    images_dir.mkdir()

    (reports_dir / "Iteration_Log.csv").write_text(
        "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel\n"
        "AC0820_L.jpg;SEMANTIC: Kreis + Buchstabe CO_2;3;20.61;0.02289506\n",
        encoding="utf-8",
    )
    (svg_dir / "AC0820_L.svg").write_text(
        '<svg width="30px" height="30px" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="15" cy="15" r="10" fill="#dcdcdc" stroke="#7f7f7f" stroke-width="1"/>'
        '<text x="15" y="17" fill="#5f5f5f">CO₂</text>'
        "</svg>",
        encoding="utf-8",
    )
    shutil.copyfile("artifacts/images_to_convert/AC0820_L.jpg", images_dir / "AC0820_L.jpg")

    rows = conv._load_existing_conversion_rows(str(output_root), str(images_dir))

    assert len(rows) == 1
    assert rows[0]["variant"] == "AC0820_L"
    assert rows[0]["base"] == "AC0820"
    assert rows[0]["best_iter"] == 3
    assert rows[0]["error_per_pixel"] == pytest.approx(0.02289506)
    assert rows[0]["params"]["mode"] == "semantic_badge"


def test_convert_range_uses_existing_conversion_rows_as_template_donors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    csv_path = tmp_path / "mapping.csv"
    output_root = tmp_path / "converted"
    target_name = "AC0833_L.jpg"
    shutil.copyfile("artifacts/images_to_convert/AC0833_L.jpg", images_dir / target_name)
    csv_path.write_text("Wurzelform;Beschreibung\nAC0833;semantic\n", encoding="utf-8")

    existing_donor = {
        "filename": "AC0820_L.jpg",
        "params": {"mode": "semantic_badge", "draw_text": True, "text_mode": "co2"},
        "best_iter": 1,
        "best_error": 10.0,
        "error_per_pixel": 0.01,
        "w": 30,
        "h": 30,
        "base": "AC0820",
        "variant": "AC0820_L",
    }

    monkeypatch.setattr(conv, "_load_existing_conversion_rows", lambda *_args, **_kwargs: [existing_donor])
    monkeypatch.setattr(conv, "_load_quality_config", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(conv, "_write_quality_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(conv, "_write_quality_pass_report", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(conv, "_harmonize_semantic_size_variants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(conv, "_write_pixel_delta2_ranking", lambda *_args, **_kwargs: None)

    calls: list[list[str]] = []

    def fake_run_iteration_pipeline(image_path: str, *_args, **_kwargs):
        return (
            Path(image_path).stem,
            "semantic",
            {"mode": "semantic_badge", "draw_text": True, "text_mode": "co2", "elements": ["SEMANTIC: test"]},
            1,
            100.0,
        )

    def fake_try_template_transfer(*, target_row, donor_rows, **_kwargs):
        calls.append([str(row.get("variant", "")) for row in donor_rows])
        return None, None

    monkeypatch.setattr(conv, "run_iteration_pipeline", fake_run_iteration_pipeline)
    monkeypatch.setattr(conv, "_try_template_transfer", fake_try_template_transfer)

    conv.convert_range(
        str(images_dir),
        str(csv_path),
        iterations=1,
        start_ref="AC0833",
        end_ref="AC0833",
        output_root=str(output_root),
    )

    assert calls
    assert "AC0820_L" in calls[0]


def test_validate_badge_by_elements_detects_stagnation_and_stops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    params = {
        "circle_enabled": True,
        "stem_enabled": False,
        "arm_enabled": False,
        "draw_text": False,
        "cx": 5.0,
        "cy": 5.0,
        "r": 3.0,
    }
    img = np.zeros((12, 12, 3), dtype=np.uint8)

    monkeypatch.setattr(conv.Action, "generate_badge_svg", staticmethod(lambda *_args, **_kwargs: "<svg />"))
    monkeypatch.setattr(conv.Action, "render_svg_to_numpy", staticmethod(lambda *_args, **_kwargs: img.copy()))
    monkeypatch.setattr(conv.Action, "_fit_to_original_size", staticmethod(lambda _orig, rendered: rendered))
    monkeypatch.setattr(conv.Action, "create_diff_image", staticmethod(lambda *_args, **_kwargs: img.copy()))
    monkeypatch.setattr(conv.Action, "extract_badge_element_mask", staticmethod(lambda *_args, **_kwargs: np.ones((12, 12), dtype=bool)))
    monkeypatch.setattr(conv.Action, "_element_match_error", staticmethod(lambda *_args, **_kwargs: 1.0))
    monkeypatch.setattr(conv.Action, "_optimize_element_width_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_optimize_element_extent_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_optimize_circle_center_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_optimize_circle_radius_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_optimize_element_color_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_apply_canonical_badge_colors", staticmethod(lambda current: current))
    monkeypatch.setattr(conv.Action, "calculate_error", staticmethod(lambda *_args, **_kwargs: 42.0))

    logs = conv.Action.validate_badge_by_elements(img, params, max_rounds=4)

    assert any("stagnation_detected" in line for line in logs)
    assert any("switch_to_fallback_search" in line for line in logs)
    assert any("stopped_due_to_stagnation" in line for line in logs)


def test_resolve_cli_csv_and_output_accepts_xml_as_table_path(tmp_path: Path) -> None:
    in_dir = tmp_path / "images"
    in_dir.mkdir()
    xml_path = tmp_path / "Finale_Wurzelformen_V3.xml"
    xml_path.write_text("<wurzelformen_export/>\n", encoding="utf-8")

    args = conv.parse_args([str(in_dir), str(xml_path), "32"])
    csv_path, output_dir = conv._resolve_cli_csv_and_output(args)

    assert csv_path == str(xml_path)
    assert output_dir is None


def test_load_description_mapping_from_xml_prefers_image_specific_detail(tmp_path: Path) -> None:
    xml_path = tmp_path / "Finale_Wurzelformen_V3.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<wurzelformen_export>
  <entries>
    <entry kind="rohrgruppe" key="z_rohre">
      <beschreibung>Gruppenbeschreibung Rohrformen</beschreibung>
      <bilder>
        <bild>z_202.jpg</bild>
      </bilder>
      <bildbeschreibungen>
        <bildbeschreibung bild="z_202.jpg">Langgezogenes Rechteck mit Verlauf</bildbeschreibung>
      </bildbeschreibungen>
    </entry>
  </entries>
</wurzelformen_export>
""",
        encoding="utf-8",
    )

    mapping = conv._load_description_mapping(str(xml_path))

    assert "z_202" in mapping
    assert "Gruppenbeschreibung Rohrformen" in mapping["z_202"]
    assert "Langgezogenes Rechteck mit Verlauf" in mapping["z_202"]


def test_load_description_mapping_from_xml_reads_bild_attribute_description(tmp_path: Path) -> None:
    xml_path = tmp_path / "Finale_Wurzelformen_V3.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<wurzelformen_export>
  <entries>
    <entry kind="rohrgruppe" key="z_rohre">
      <beschreibung>Rohrgruppe</beschreibung>
      <bilder>
        <bild beschreibung="Halb offene Hand, Kontur + Innenfläche">z_111.jpg</bild>
      </bilder>
    </entry>
  </entries>
</wurzelformen_export>
""",
        encoding="utf-8",
    )

    mapping = conv._load_description_mapping(str(xml_path))

    assert mapping["z_111"] == "Rohrgruppe Halb offene Hand, Kontur + Innenfläche"


def test_load_description_mapping_from_xml_registers_case_and_extension_variants() -> None:
    """XML loader should expose descriptions for key/image variants used by runtime lookup."""
    mapping = conv._load_description_mapping_from_xml(
        "artifacts/images_to_convert/Finale_Wurzelformen_V3.xml"
    )

    assert mapping.get("AC0241")
    assert mapping.get("AC0241_L")
    assert mapping.get("ac0241_l")
    assert mapping.get("z_202")
    assert mapping.get("Z_202")
    assert mapping.get("z_202.jpg")
    assert mapping.get("Z_202.JPG")


def test_parse_description_uses_xml_loaded_variant_descriptions() -> None:
    """Descriptions from merged XML entries should be discoverable for concrete image variants."""
    mapping = conv._load_description_mapping_from_xml(
        "artifacts/images_to_convert/Finale_Wurzelformen_V3.xml"
    )
    ref = conv.Reflection(mapping)

    desc, _params = ref.parse_description("z_202", "z_202.jpg")

    assert "rohr" in desc


def test_load_description_mapping_from_xml_falls_back_to_descriptions_directory() -> None:
    mapping = conv._load_description_mapping_from_xml(
        "artifacts/images_to_convert/Finale_Wurzelformen_V3.xml"
    )

    assert mapping.get("AC0241")


def test_build_linux_vendor_install_command_uses_vendor_defaults() -> None:
    cmd = conv.build_linux_vendor_install_command(vendor_dir="vendor", platform_tag="manylinux2014_x86_64", python_version="311")

    assert cmd[:4] == [image_composite_converter.sys.executable, "-m", "pip", "install"]
    assert "--target" in cmd
    assert "vendor" in cmd
    assert "--platform" in cmd
    assert "manylinux2014_x86_64" in cmd
    assert "--python-version" in cmd
    assert "311" in cmd
    assert "numpy" in cmd
    assert "opencv-python-headless" in cmd
    assert "Pillow" in cmd
    assert "PyMuPDF" in cmd


def test_main_print_linux_vendor_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = conv.main(
        [
            "artifacts/images_to_convert",
            "--print-linux-vendor-command",
            "--vendor-dir",
            "vendor",
            "--vendor-platform",
            "manylinux2014_x86_64",
            "--vendor-python-version",
            "311",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "--target vendor" in captured.out
    assert "--platform manylinux2014_x86_64" in captured.out
    assert "--python-version 311" in captured.out


def test_trace_image_segment_uses_raw_contour_chain_for_epsilon_sweep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contour extraction should keep all points so epsilon iterations can have an effect."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2
    if np is None or cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    original_find_contours = cv2.findContours
    called_methods: list[int] = []

    def _wrapped_find_contours(*args, **kwargs):
        if len(args) >= 3:
            called_methods.append(int(args[2]))
        return original_find_contours(*args, **kwargs)

    monkeypatch.setattr(cv2, "findContours", _wrapped_find_contours)

    # white background + dark square foreground => at least one contour
    img = np.full((24, 24, 3), 255, dtype=np.uint8)
    cv2.rectangle(img, (5, 5), (18, 18), (90, 90, 90), thickness=-1)

    paths = Action.trace_image_segment(img, epsilon_factor=0.01)

    assert paths
    assert called_methods
    assert all(method == cv2.CHAIN_APPROX_NONE for method in called_methods)


def test_bbox_to_dict_records_expected_coordinates() -> None:
    region = image_composite_converter._bbox_to_dict("circle", (1, 2, 6, 8), (0, 0, 255))

    assert region["label"] == "circle"
    assert region["bbox"] == {"x0": 1, "y0": 2, "x1": 6, "y1": 8, "width": 6, "height": 7}
    assert region["color_bgr"] == [0, 0, 255]


def test_parse_args_defaults_to_convert_mode() -> None:
    args = image_composite_converter.parse_args(["images"])

    assert args.mode == "convert"


def test_create_diff_image_without_cv2_writes_rgb_overlay(tmp_path: Path) -> None:
    src = tmp_path / "sample.jpg"
    shutil.copyfile("artifacts/images_to_convert/AC0010.jpg", src)

    svg = image_composite_converter._render_embedded_raster_svg(src)
    diff = image_composite_converter._create_diff_image_without_cv2(src, svg)

    assert diff.n == 3
    assert diff.width > 0
    assert diff.height > 0


def test_convert_range_fallback_writes_diff_pngs_when_cv2_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    shutil.copyfile("artifacts/images_to_convert/AC0010.jpg", images_dir / "AC0010.jpg")

    monkeypatch.setattr(image_composite_converter, "cv2", None)
    monkeypatch.setattr(image_composite_converter, "np", None)

    out_dir = image_composite_converter.convert_range(
        str(images_dir),
        csv_path="",
        iterations=1,
        start_ref="AC0010",
        end_ref="AC0010",
        output_root=str(tmp_path / "out"),
    )

    assert (Path(out_dir) / "converted_svgs" / "AC0010.svg").exists()
    assert (Path(out_dir) / "diff_pngs" / "AC0010_diff.png").exists()


def test_detect_relevant_regions_finds_circle_stem_and_text() -> None:
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2
    img = np.full((80, 80, 3), 255, dtype=np.uint8)
    cv2.circle(img, (28, 26), 14, (0, 0, 0), thickness=2)
    cv2.rectangle(img, (24, 39), (32, 67), (0, 0, 0), thickness=-1)
    cv2.putText(img, "M", (45, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)

    regions = image_composite_converter.detect_relevant_regions(img)
    labels = {region["label"] for region in regions}

    assert {"circle", "stem", "text"}.issubset(labels)


def test_render_svg_to_numpy_returns_none_after_retryable_renderer_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Renderer exceptions should be absorbed so batch processing can decide how to continue."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    attempts: list[tuple[str, bytes]] = []

    def fake_open(kind: str, payload: bytes):
        attempts.append((kind, payload))
        raise RuntimeError("renderer exploded")

    monkeypatch.setattr(image_composite_converter.fitz, "open", fake_open)

    result = Action.render_svg_to_numpy('<svg xmlns="http://www.w3.org/2000/svg">  <rect width="1" height="1"/> </svg>', 4, 4)

    assert result is None
    assert len(attempts) >= 1



def test_convert_range_continues_after_render_failure_and_writes_batch_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A render failure for one file should be logged without aborting the remaining batch."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2
    if np is None or cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    images_dir = tmp_path / "images"
    images_dir.mkdir()
    output_root = tmp_path / "out"
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0820;semantic\n", encoding="utf-8")
    for name in ("AC0820_L.jpg", "AC0820_M.jpg"):
        assert cv2.imwrite(str(images_dir / name), np.full((10, 10, 3), 220, dtype=np.uint8))

    monkeypatch.setattr(image_composite_converter, "_in_requested_range", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(image_composite_converter, "_load_quality_config", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(image_composite_converter, "_write_quality_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_harmonize_semantic_size_variants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_write_pixel_delta2_ranking", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_select_open_quality_cases", lambda rows, **_kwargs: [])
    monkeypatch.setattr(image_composite_converter, "_select_middle_lower_tercile", lambda _rows: [])
    monkeypatch.setattr(image_composite_converter, "_try_template_transfer", lambda **_kwargs: (None, None))

    def fake_pipeline(img_path: str, _csv_path: str, _iterations: int, svg_out: str, diff_out: str, reports_out: str, *_args, **_kwargs):
        stem = Path(img_path).stem
        Path(svg_out).mkdir(parents=True, exist_ok=True)
        Path(diff_out).mkdir(parents=True, exist_ok=True)
        Path(reports_out).mkdir(parents=True, exist_ok=True)
        if stem.endswith("_L"):
            log_path = Path(reports_out) / f"{stem}_element_validation.log"
            log_path.write_text(
                "status=render_failure\n"
                "failure_reason=composite_iteration_render_failed\n"
                f"filename={stem}.jpg\n"
                "params_snapshot={\"mode\":\"semantic_badge\"}\n",
                encoding="utf-8",
            )
            return None
        svg = '<svg width="10" height="10" xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10" fill="#d0d0d0"/></svg>'
        (Path(svg_out) / f"{stem}.svg").write_text(svg, encoding="utf-8")
        (Path(diff_out) / f"{stem}_diff.png").write_bytes(b"png")
        params = {"mode": "semantic_badge", "elements": ["circle"], "cx": 5.0, "cy": 5.0, "r": 3.0}
        return stem, "semantic", params, 1, 30.0

    monkeypatch.setattr(image_composite_converter, "run_iteration_pipeline", fake_pipeline)

    result = image_composite_converter.convert_range(
        str(images_dir),
        str(csv_path),
        iterations=1,
        start_ref="AC0820",
        end_ref="AC0820",
        output_root=str(output_root),
    )

    assert result == str(output_root)
    iteration_log = (output_root / "reports" / "Iteration_Log.csv").read_text(encoding="utf-8-sig")
    assert "AC0820_M.jpg" in iteration_log
    assert "AC0820_L.jpg" not in iteration_log

    batch_summary = (output_root / "reports" / "batch_failure_summary.csv").read_text(encoding="utf-8")
    assert "AC0820_L.jpg;render_failure;composite_iteration_render_failed" in batch_summary
    assert "AC0820_L_element_validation.log" in batch_summary
