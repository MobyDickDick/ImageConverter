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
    assert observed["stem"] is False
    assert observed["arm"] is False
    assert observed["text"] is False


def test_detect_semantic_primitives_detects_vertical_connector_without_arm() -> None:
    """AC0813 badges should report a vertical connector, not hallucinate a horizontal one."""
    if conv.cv2 is None or conv.np is None:
        pytest.skip("opencv/numpy not available in this environment")

    img = conv.cv2.imread("artifacts/images_to_convert/AC0813_L.jpg")
    assert img is not None

    observed = conv.Action._detect_semantic_primitives(img)

    assert observed["circle"] is True
    assert observed["stem"] is True
    assert observed["arm"] is False
    assert observed["connector_orientation"] == "vertical"


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


def test_semantic_validation_ignores_structural_false_positives_for_plain_circle_badge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Connector-free circle badges should not fail only because raw heuristics hallucinate arm/text noise."""
    if conv.np is None:
        pytest.skip("numpy not available in this environment")

    monkeypatch.setattr(
        conv.Action,
        "_detect_semantic_primitives",
        staticmethod(lambda _img: {"circle": True, "arm": True, "text": True}),
    )
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
        ["SEMANTIC: Kreis ohne Buchstabe"],
        {"cx": 4.5, "cy": 4.5, "r": 2.5, "draw_text": False},
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


def test_update_successful_conversions_manifest_keeps_existing_line_without_fresh_metrics(tmp_path: Path) -> None:
    """Existing manifest metrics must survive when a variant is not reconverted in the current run."""
    reports_dir = tmp_path / "reports"
    svg_dir = tmp_path / "svg"
    images_dir = tmp_path / "images"
    reports_dir.mkdir()
    svg_dir.mkdir()
    images_dir.mkdir()

    manifest_path = reports_dir / "successful_conversions.txt"
    existing_line = (
        "AC0800_L ; status=semantic_ok ; best_iteration=42 ; diff_score=0.123456 ; "
        "error_per_pixel=0.00001234 ; total_delta2=12.500000 ; mean_delta2=0.100000 ; "
        "std_delta2=0.010000 ; pixel_count=125  # bereits bestätigt"
    )
    manifest_path.write_text(existing_line + "\n", encoding="utf-8")

    updated_path, metrics = image_composite_converter.update_successful_conversions_manifest_with_metrics(
        folder_path=str(images_dir),
        svg_out_dir=str(svg_dir),
        reports_out_dir=str(reports_dir),
        manifest_path=manifest_path,
        successful_variants=["AC0800_L"],
    )

    assert updated_path == manifest_path
    assert len(metrics) == 1
    assert updated_path.read_text(encoding="utf-8").strip() == existing_line


def test_update_successful_conversions_manifest_appends_missing_variant_with_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing successful variants should be appended so metrics reach the manifest file."""
    reports_dir = tmp_path / "reports"
    svg_dir = tmp_path / "svg"
    image_dir = tmp_path / "images"
    reports_dir.mkdir()
    svg_dir.mkdir()
    image_dir.mkdir()

    manifest_path = reports_dir / "successful_conversions.txt"
    manifest_path.write_text("# erfolgreiche Varianten\n", encoding="utf-8")
    (reports_dir / "Iteration_Log.csv").write_text(
        "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel\n"
        "AC0002_L.jpg;SEMANTIC;7;9.50;0.12500000\n",
        encoding="utf-8-sig",
    )
    (reports_dir / "AC0002_L_element_validation.log").write_text("status=semantic_ok\n", encoding="utf-8")
    (image_dir / "AC0002_L.jpg").write_bytes(b"fake-jpg")
    (svg_dir / "AC0002_L.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>', encoding="utf-8")

    np = conv.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    source = np.array([[[10, 10, 10]]], dtype=np.uint8)
    rendered = np.array([[[12, 10, 10]]], dtype=np.uint8)

    monkeypatch.setattr(conv.cv2, "imread", lambda path: source.copy() if path.endswith("AC0002_L.jpg") else None)
    monkeypatch.setattr(conv.Action, "render_svg_to_numpy", staticmethod(lambda _svg, _w, _h: rendered.copy()))

    updated_path, metrics = image_composite_converter.update_successful_conversions_manifest_with_metrics(
        folder_path=str(image_dir),
        svg_out_dir=str(svg_dir),
        reports_out_dir=str(reports_dir),
        manifest_path=manifest_path,
        successful_variants=["AC0002_L"],
    )

    assert updated_path == manifest_path
    assert [row["variant"] for row in metrics] == ["AC0002_L"]
    manifest_text = updated_path.read_text(encoding="utf-8")
    assert "# erfolgreiche Varianten" in manifest_text
    assert "AC0002_L ; status=semantic_ok ; best_iteration=7 ; diff_score=9.500000 ; error_per_pixel=0.12500000 ; total_delta2=4.000000 ; mean_delta2=4.000000 ; std_delta2=0.000000 ; pixel_count=1" in manifest_text



def test_update_successful_conversions_manifest_rejects_worse_candidate_and_restores_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A worse reconversion must not overwrite the persisted best-list entry or artifact snapshot."""
    reports_dir = tmp_path / "reports"
    svg_dir = tmp_path / "svg"
    image_dir = tmp_path / "images"
    reports_dir.mkdir()
    svg_dir.mkdir()
    image_dir.mkdir()

    manifest_path = reports_dir / "successful_conversions.txt"
    existing_line = (
        "AC0003_L ; status=semantic_ok ; best_iteration=3 ; diff_score=4.000000 ; "
        "error_per_pixel=0.10000000 ; total_delta2=10.000000 ; mean_delta2=10.000000 ; "
        "std_delta2=0.000000 ; pixel_count=1"
    )
    manifest_path.write_text(existing_line + "\n", encoding="utf-8")
    (reports_dir / "Iteration_Log.csv").write_text(
        "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel\n"
        "AC0003_L.jpg;SEMANTIC;9;9.00;0.30000000\n",
        encoding="utf-8-sig",
    )
    (reports_dir / "AC0003_L_element_validation.log").write_text("status=semantic_ok\n", encoding="utf-8")
    (image_dir / "AC0003_L.jpg").write_bytes(b"fake-jpg")
    (svg_dir / "AC0003_L.svg").write_text("<svg>new-worse</svg>", encoding="utf-8")

    best_dir = reports_dir / "successful_conversions_bestlist"
    best_dir.mkdir()
    (best_dir / "AC0003_L.svg").write_text("<svg>old-best</svg>", encoding="utf-8")
    (best_dir / "AC0003_L_element_validation.log").write_text("status=semantic_ok\nsource=best\n", encoding="utf-8")

    np = conv.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    source = np.array([[[10, 10, 10]]], dtype=np.uint8)
    rendered = np.array([[[14, 10, 10]]], dtype=np.uint8)

    monkeypatch.setattr(conv.cv2, "imread", lambda path: source.copy() if path.endswith("AC0003_L.jpg") else None)
    monkeypatch.setattr(conv.Action, "render_svg_to_numpy", staticmethod(lambda _svg, _w, _h: rendered.copy()))

    updated_path, metrics = image_composite_converter.update_successful_conversions_manifest_with_metrics(
        folder_path=str(image_dir),
        svg_out_dir=str(svg_dir),
        reports_out_dir=str(reports_dir),
        manifest_path=manifest_path,
        successful_variants=["AC0003_L"],
    )

    assert updated_path == manifest_path
    assert [row["variant"] for row in metrics] == ["AC0003_L"]
    assert updated_path.read_text(encoding="utf-8").strip() == existing_line
    assert (svg_dir / "AC0003_L.svg").read_text(encoding="utf-8") == "<svg>old-best</svg>"
    assert "source=best" in (reports_dir / "AC0003_L_element_validation.log").read_text(encoding="utf-8")


def test_update_successful_conversions_manifest_rejects_worse_candidate_without_snapshot_keeps_current_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without a stored snapshot, rejected candidates must not delete freshly converted outputs."""
    reports_dir = tmp_path / "reports"
    svg_dir = tmp_path / "svg"
    image_dir = tmp_path / "images"
    reports_dir.mkdir()
    svg_dir.mkdir()
    image_dir.mkdir()

    manifest_path = reports_dir / "successful_conversions.txt"
    existing_line = (
        "AC0800_L ; status=semantic_ok ; best_iteration=3 ; diff_score=4.000000 ; "
        "error_per_pixel=0.10000000 ; total_delta2=10.000000 ; mean_delta2=10.000000 ; "
        "std_delta2=0.000000 ; pixel_count=1"
    )
    manifest_path.write_text(existing_line + "\n", encoding="utf-8")
    (reports_dir / "Iteration_Log.csv").write_text(
        "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel\n"
        "AC0800_L.jpg;SEMANTIC;9;9.00;0.30000000\n",
        encoding="utf-8-sig",
    )
    (reports_dir / "AC0800_L_element_validation.log").write_text("status=semantic_ok\nsource=current\n", encoding="utf-8")
    (image_dir / "AC0800_L.jpg").write_bytes(b"fake-jpg")
    (svg_dir / "AC0800_L.svg").write_text("<svg>current-run</svg>", encoding="utf-8")

    np = conv.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    source = np.array([[[10, 10, 10]]], dtype=np.uint8)
    rendered = np.array([[[14, 10, 10]]], dtype=np.uint8)

    monkeypatch.setattr(conv.cv2, "imread", lambda path: source.copy() if path.endswith("AC0800_L.jpg") else None)
    monkeypatch.setattr(conv.Action, "render_svg_to_numpy", staticmethod(lambda _svg, _w, _h: rendered.copy()))

    updated_path, metrics = image_composite_converter.update_successful_conversions_manifest_with_metrics(
        folder_path=str(image_dir),
        svg_out_dir=str(svg_dir),
        reports_out_dir=str(reports_dir),
        manifest_path=manifest_path,
        successful_variants=["AC0800_L"],
    )

    assert updated_path == manifest_path
    assert [row["variant"] for row in metrics] == ["AC0800_L"]
    assert updated_path.read_text(encoding="utf-8").strip() == existing_line
    assert (svg_dir / "AC0800_L.svg").read_text(encoding="utf-8") == "<svg>current-run</svg>"
    assert "source=current" in (reports_dir / "AC0800_L_element_validation.log").read_text(encoding="utf-8")


def test_update_successful_conversions_manifest_accepts_better_candidate_and_updates_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A better reconversion should replace the best-list metrics and stored snapshot."""
    reports_dir = tmp_path / "reports"
    svg_dir = tmp_path / "svg"
    image_dir = tmp_path / "images"
    reports_dir.mkdir()
    svg_dir.mkdir()
    image_dir.mkdir()

    manifest_path = reports_dir / "successful_conversions.txt"
    manifest_path.write_text(
        "AC0004_L ; status=semantic_ok ; best_iteration=2 ; diff_score=8.000000 ; error_per_pixel=0.20000000 ; total_delta2=12.000000 ; mean_delta2=12.000000 ; std_delta2=0.000000 ; pixel_count=1\n",
        encoding="utf-8",
    )
    (reports_dir / "Iteration_Log.csv").write_text(
        "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel\n"
        "AC0004_L.jpg;SEMANTIC;5;5.50;0.05000000\n",
        encoding="utf-8-sig",
    )
    (reports_dir / "AC0004_L_element_validation.log").write_text("status=semantic_ok\n", encoding="utf-8")
    (image_dir / "AC0004_L.jpg").write_bytes(b"fake-jpg")
    (svg_dir / "AC0004_L.svg").write_text("<svg>new-better</svg>", encoding="utf-8")

    np = conv.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    source = np.array([[[10, 10, 10]]], dtype=np.uint8)
    rendered = np.array([[[11, 10, 10]]], dtype=np.uint8)

    monkeypatch.setattr(conv.cv2, "imread", lambda path: source.copy() if path.endswith("AC0004_L.jpg") else None)
    monkeypatch.setattr(conv.Action, "render_svg_to_numpy", staticmethod(lambda _svg, _w, _h: rendered.copy()))

    updated_path, _metrics = image_composite_converter.update_successful_conversions_manifest_with_metrics(
        folder_path=str(image_dir),
        svg_out_dir=str(svg_dir),
        reports_out_dir=str(reports_dir),
        manifest_path=manifest_path,
        successful_variants=["AC0004_L"],
    )

    manifest_text = updated_path.read_text(encoding="utf-8")
    assert "best_iteration=5" in manifest_text
    assert "diff_score=5.500000" in manifest_text
    assert "error_per_pixel=0.05000000" in manifest_text
    assert "mean_delta2=1.000000" in manifest_text
    best_svg = (reports_dir / "successful_conversions_bestlist" / "AC0004_L.svg").read_text(encoding="utf-8")
    assert best_svg == "<svg>new-better</svg>"

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


def test_co2_superscript_has_global_minimum_gap_from_o() -> None:
    """Superscript 2 should keep a visible horizontal gap from the O glyph."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params["co2_index_mode"] = "superscript"
    params["co2_anchor_mode"] = "cluster"
    layout = Action._co2_layout(params)

    o_right = float(layout["co_x"]) + (float(layout["font_size"]) * 1.04 * float(layout["width_scale"]) / 2.0)
    min_gap = float(layout["font_size"]) * 0.13
    assert float(layout["subscript_x"]) - o_right >= (min_gap - 1e-6)


def test_finalize_ac0820_keeps_default_anchor_mode() -> None:
    """AC0820 should keep the default CO₂ anchor mode (no forced centering rule)."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820", params)

    assert params["co2_anchor_mode"] == "center_co"


def test_finalize_ac0820_variant_name_keeps_default_anchor_mode() -> None:
    """AC0820 variants should keep superscript CO² without forcing centered anchoring."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820_L", params)

    assert params["co2_anchor_mode"] == "center_co"
    assert params["co2_index_mode"] == "superscript"
    assert float(params["co2_optical_bias"]) >= 0.125


def test_finalize_ac0820_m_enforces_larger_superscript_gap() -> None:
    """AC0820_M should keep a stronger horizontal separation between O and superscript 2."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params = Action._finalize_ac08_style("AC0820_M", params)
    layout = Action._co2_layout(params)

    o_right = float(layout["co_x"]) + (float(layout["font_size"]) * 1.04 * float(layout["width_scale"]) / 2.0)
    min_gap = float(layout["font_size"]) * 0.16
    assert float(layout["subscript_x"]) - o_right >= (min_gap - 1e-6)


def test_finalize_ac0800_keeps_ring_darker_than_fill() -> None:
    """AC0800 should preserve generic ring semantics: darker stroke than fill."""
    params = Action.make_badge_params(30, 30, "AC0800")
    assert params is not None
    assert float(params["r"]) == pytest.approx(10.8)
    assert int(params["stroke_gray"]) < int(params["fill_gray"])
    assert float(params["stroke_circle"]) >= 1.0


def test_apply_redraw_variation_jitters_params_and_logs_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Final badge redraw should apply a slight stochastic variation and record it."""
    monkeypatch.setattr(conv.time, "time_ns", lambda: 123_456_789)
    conv.Action.STOCHASTIC_RUN_SEED = 11
    conv.Action.STOCHASTIC_SEED_OFFSET = 2
    params = {
        "circle_enabled": True,
        "cx": 10.0,
        "cy": 10.0,
        "r": 4.0,
        "stroke_circle": 1.0,
        "draw_text": False,
    }

    varied, logs = conv.Action.apply_redraw_variation(params, 20, 20)

    assert logs
    assert logs[0].startswith("redraw_variation: seed=")
    assert "cx:" in logs[0]
    assert "cy:" in logs[0]
    assert varied["cx"] != params["cx"] or varied["cy"] != params["cy"] or varied["r"] != params["r"]
    assert 0.0 <= float(varied["cx"]) <= 20.0
    assert 0.0 <= float(varied["cy"]) <= 20.0


def test_apply_redraw_variation_uses_new_time_nonce_per_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Separate redraw passes should produce different logged parameter jitters."""
    timestamps = iter([100, 200])
    monkeypatch.setattr(conv.time, "time_ns", lambda: next(timestamps))
    conv.Action.STOCHASTIC_RUN_SEED = 5
    conv.Action.STOCHASTIC_SEED_OFFSET = 0
    params = {
        "circle_enabled": True,
        "cx": 10.0,
        "cy": 10.0,
        "r": 4.0,
        "stroke_circle": 1.0,
        "draw_text": False,
    }

    _varied_a, logs_a = conv.Action.apply_redraw_variation(params, 20, 20)
    _varied_b, logs_b = conv.Action.apply_redraw_variation(params, 20, 20)

    assert logs_a[0] != logs_b[0]


def test_select_circle_radius_plateau_candidate_prefers_plateau_midpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Near-equal circle radii should resolve to the plateau center instead of a noisy edge minimum."""
    if conv.np is None:
        pytest.skip("numpy not available in this environment")

    img = conv.np.zeros((20, 20, 3), dtype=conv.np.uint8)
    params = {"circle_enabled": True, "min_circle_radius": 5.0, "max_circle_radius": 8.0}
    evaluations = {5.0: 10.03, 5.5: 10.0, 6.0: 10.01}
    full_errors = {5.5: 20.0, 6.0: 19.5}

    monkeypatch.setattr(
        conv.Action,
        "_full_badge_error_for_circle_radius",
        staticmethod(lambda _img, _params, radius: full_errors[float(radius)]),
    )

    best_r, best_err, best_full_err = conv.Action._select_circle_radius_plateau_candidate(
        img,
        params,
        evaluations,
        current_radius=5.0,
    )

    assert best_r == pytest.approx(6.0)
    assert best_err == pytest.approx(10.01)
    assert best_full_err == pytest.approx(19.5)


def test_optimize_circle_radius_bracket_uses_plateau_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Radius bracketing should not keep the smallest noisy minimum when the plateau center scores better overall."""
    if conv.np is None:
        pytest.skip("numpy not available in this environment")

    img = conv.np.zeros((20, 20, 3), dtype=conv.np.uint8)
    params = {"circle_enabled": True, "r": 5.0, "min_circle_radius": 5.0, "max_circle_radius": 8.0}
    element_errors = {5.0: 10.03, 5.5: 10.0, 6.0: 10.01}
    full_errors = {5.5: 20.0, 6.0: 19.5}

    monkeypatch.setattr(conv.Action, "_clip_scalar", staticmethod(lambda value, low, high: max(low, min(high, value))))
    monkeypatch.setattr(conv.Action, "_snap_half", staticmethod(lambda value: round(value * 2.0) / 2.0))
    monkeypatch.setattr(
        conv.Action,
        "_element_error_for_circle_radius",
        staticmethod(lambda _img, _params, radius: element_errors[float(radius)]),
    )
    monkeypatch.setattr(
        conv.Action,
        "_full_badge_error_for_circle_radius",
        staticmethod(lambda _img, _params, radius: full_errors[float(radius)]),
    )

    logs: list[str] = []
    changed = conv.Action._optimize_circle_radius_bracket(img, params, logs)

    assert changed is True
    assert params["r"] == pytest.approx(6.0)
    assert any("full_err=19.500" in entry for entry in logs)


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


def test_generate_badge_svg_keeps_border_touching_arm_caps_inside_viewbox() -> None:
    """Rounded arms may touch the border, but they must stay inside the original canvas."""
    params = {
        "arm_enabled": True,
        "arm_x1": 21.5,
        "arm_y1": 10.0,
        "arm_x2": 35.0,
        "arm_y2": 10.0,
        "arm_stroke": 1.0,
        "stroke_gray": 120,
        "circle_enabled": False,
        "draw_text": False,
    }

    svg = Action.generate_badge_svg(35, 20, params)

    assert 'x1="21.5000"' in svg
    assert 'x2="35.0000"' in svg
    assert '35.5000' not in svg


def test_generate_badge_svg_keeps_border_touching_stem_inside_viewbox() -> None:
    """Bottom-anchored stems must not be extended past the canvas height."""
    params = {
        "stem_enabled": True,
        "stem_x": 9.0,
        "stem_top": 4.0,
        "stem_bottom": 20.0,
        "stem_width": 2.0,
        "stroke_gray": 120,
        "circle_enabled": False,
        "draw_text": False,
    }

    svg = Action.generate_badge_svg(20, 20, params)

    assert 'y="4.0000"' in svg
    assert 'height="16.0000"' in svg
    assert '20.5000' not in svg


def test_fit_semantic_badge_uses_border_touch_fallback_for_tiny_plain_ring() -> None:
    """Tiny plain rings that touch every border should expand to the canvas-fitting circle."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    img = image_composite_converter.cv2.imread("artifacts/images_to_convert/AC0800_S.jpg")
    assert img is not None

    fitted = Action.make_badge_params(img.shape[1], img.shape[0], "AC0800", img)

    assert fitted is not None
    assert float(fitted["cx"]) == pytest.approx(7.5)
    assert float(fitted["cy"]) == pytest.approx(7.5)
    assert float(fitted["r"]) == pytest.approx(7.0)


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


def test_make_badge_params_ac0833_uses_superscript_index() -> None:
    """AC0833 variants should render CO² with a raised superscript 2."""
    params = image_composite_converter.Action.make_badge_params(24, 24, "AC0833")

    assert params is not None
    assert params.get("text_mode") == "co2"
    assert params.get("co2_index_mode") == "superscript"


def test_finalize_ac0833_keeps_superscript_after_fit() -> None:
    """Final AC0833 tuning should keep superscript settings even after fitting updates."""
    params = image_composite_converter.Action._apply_co2_label(image_composite_converter.Action._default_ac0813_params(24, 24))
    params["co2_index_mode"] = "subscript"

    tuned = image_composite_converter.Action._finalize_ac08_style("AC0833_M", params)

    assert tuned.get("co2_index_mode") == "superscript"


def test_parse_description_marks_ac0813_with_top_vertical_connector() -> None:
    """AC0813 belongs to the top-connector family and must encode that semantic element."""
    ref = image_composite_converter.Reflection({})

    _desc, params = ref.parse_description("AC0813", "AC0813_L.jpg")

    assert "SEMANTIC: senkrechter Strich oben vom Kreis" in list(params.get("elements", []))


def test_parse_description_marks_ac0838_with_right_horizontal_arm() -> None:
    """AC0838 belongs to the right-arm VOC family and must include that semantic element."""
    ref = image_composite_converter.Reflection({})

    _desc, params = ref.parse_description("AC0838", "AC0838_L.jpg")

    assert "SEMANTIC: waagrechter Strich rechts vom Kreis" in list(params.get("elements", []))


def test_parse_description_marks_ac0800_as_plain_ring_family() -> None:
    """AC0800 should remain a semantic plain ring even without text clues in the XML."""
    ref = image_composite_converter.Reflection({})

    _desc, params = ref.parse_description("AC0800", "AC0800_M.jpg")

    assert params["mode"] == "semantic_badge"
    assert params["label"] == ""
    assert "SEMANTIC: Kreis ohne Buchstabe" in list(params.get("elements", []))


def test_parse_description_does_not_misread_ac0130_text_as_top_source_ref() -> None:
    """AC0130 mentions 'oben mitte' and 'in beiden Diagonalen' but has no donor image reference."""
    raw = image_composite_converter._load_description_mapping(
        "artifacts/descriptions/Finale_Wurzelformen_V3.xml"
    )
    ref = image_composite_converter.Reflection(raw)

    _desc, params = ref.parse_description("AC0130", "AC0130.jpg")

    assert params["top_source_ref"] is None
    assert "OBEN: Geschnitten aus Originaldatei BEIDEN" not in list(params.get("elements", []))


def test_finalize_ac0820_leaves_plain_circle_unlocked() -> None:
    """AC0820 should no longer inject circle-center or radius guardrails."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params = Action._finalize_ac08_style("AC0820", params)

    assert "lock_circle_cx" not in params
    assert "lock_circle_cy" not in params
    assert "min_circle_radius" not in params


def test_finalize_ac0820_keeps_template_radius_optional() -> None:
    """Template radius metadata should softly stabilize AC0820 ring size."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params["template_circle_radius"] = float(params["r"])
    params["r"] = 3.0

    params = Action._finalize_ac08_style("AC0820", params)

    assert float(params["r"]) >= float(params["template_circle_radius"]) * 0.95
    assert "min_circle_radius" not in params


def test_finalize_non_ac0820_text_badge_keeps_radius_unbounded() -> None:
    """Non-AC0820 text badges should also skip injected radius floors."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params["template_circle_radius"] = float(params["r"])
    params["r"] = 3.0

    params = Action._finalize_ac08_style("AC0831", params)

    assert float(params["r"]) == 3.0
    assert "min_circle_radius" not in params


def test_finalize_elongated_connector_badge_does_not_add_radius_floor() -> None:
    """Elongated connector badges should not receive a hard radius floor anymore."""
    params = Action._default_ac0811_params(30, 45)
    params["template_circle_radius"] = float(params["r"])
    params["r"] = float(params["r"]) * 0.84

    params = Action._finalize_ac08_style("AC0811_L", params)

    assert "min_circle_radius" not in params


def test_scale_badge_params_reanchors_vertical_stem_after_circle_canvas_fit() -> None:
    """Scaled AC0811-family stems must stay attached when the circle gets clipped to a smaller canvas."""
    anchor = Action._default_ac0811_params(25, 45)
    anchor["template_circle_cx"] = float(anchor["cx"])
    anchor["template_circle_cy"] = float(anchor["cy"])
    anchor["template_circle_radius"] = float(anchor["r"])
    anchor["template_stem_top"] = float(anchor["stem_top"])
    anchor["template_stem_bottom"] = float(anchor["stem_bottom"])

    scaled = image_composite_converter._scale_badge_params(anchor, 25, 45, 20, 35)

    assert float(scaled["cx"]) == pytest.approx(10.0)
    assert float(scaled["cy"]) == pytest.approx(9.9167, abs=0.02)
    assert float(scaled["r"]) == pytest.approx(8.6, abs=0.02)
    assert float(scaled["stem_top"]) == pytest.approx(float(scaled["cy"]) + float(scaled["r"]) - (float(scaled["stem_width"]) * 0.55), abs=0.02)
    assert float(scaled["stem_bottom"]) == pytest.approx(35.0)
    assert float(scaled["template_circle_cx"]) == pytest.approx(10.0)
    assert float(scaled["template_circle_cy"]) == pytest.approx(9.9167, abs=0.02)
    assert float(scaled["template_circle_radius"]) == pytest.approx(8.6)
    assert float(scaled["template_stem_bottom"]) == pytest.approx(35.0)


def test_default_edge_anchored_circle_geometry_keeps_symmetric_clearance() -> None:
    """Edge-anchored connector badges should use the same clearance rule at either edge."""
    top = Action._default_edge_anchored_circle_geometry(25, 45, anchor="top")
    bottom = Action._default_edge_anchored_circle_geometry(25, 45, anchor="bottom")

    assert float(top["r"]) == pytest.approx(10.75)
    assert float(top["cy"]) == pytest.approx(12.75)
    assert float(bottom["r"]) == pytest.approx(float(top["r"]))
    assert float(bottom["cy"]) == pytest.approx(45.0 - float(top["cy"]))


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


def test_finalize_ac0800_preserves_plain_ring_geometry_bounds() -> None:
    """AC0800 should keep center locks and a tight radius cap for later validation rounds."""
    params = Action.make_badge_params(30, 30, "AC0800")

    assert params["lock_circle_cx"] is True
    assert params["lock_circle_cy"] is True
    assert float(params["min_circle_radius"]) >= (10.8 * 0.96) - 0.01
    assert float(params["max_circle_radius"]) <= (10.8 * 1.15) + 0.01


def test_finalize_ac0800_small_variant_keeps_template_radius_floor() -> None:
    """AC0800_S should not shrink below the template radius during later optimization passes."""
    params = Action.make_badge_params(15, 15, "AC0800")
    params["template_circle_radius"] = float(params["r"])
    params = Action._finalize_ac08_style("AC0800_S", params)

    assert params["ac08_small_variant_mode"] is True
    assert float(params["min_circle_radius"]) >= float(params["template_circle_radius"]) - 0.01



def test_validate_badge_by_elements_keeps_ac0800_l_centered_and_bounded() -> None:
    """AC0800_L should not drift left/right or overgrow during circle-only validation."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None or image_composite_converter.fitz is None:
        pytest.skip("numpy/cv2/fitz not available in this environment")

    img = image_composite_converter.cv2.imread("artifacts/images_to_convert/AC0800_L.jpg")
    assert img is not None

    params = Action.make_badge_params(img.shape[1], img.shape[0], "AC0800", img)
    template_cx = float(params["template_circle_cx"])
    template_cy = float(params["template_circle_cy"])
    template_r = float(params["template_circle_radius"])

    logs = Action.validate_badge_by_elements(img, params, max_rounds=4)

    assert logs
    assert float(params["cx"]) == pytest.approx(template_cx)
    assert float(params["cy"]) == pytest.approx(template_cy)
    assert float(params["r"]) <= (template_r * 1.15) + 0.01


def test_validate_badge_by_elements_keeps_ac0800_s_at_template_radius_floor() -> None:
    """AC0800_S should stay concentric without shrinking below the original template radius."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None or image_composite_converter.fitz is None:
        pytest.skip("numpy/cv2/fitz not available in this environment")

    img = image_composite_converter.cv2.imread("artifacts/images_to_convert/AC0800_S.jpg")
    assert img is not None

    params = Action.make_badge_params(img.shape[1], img.shape[0], "AC0800", img)
    template_cx = float(params["template_circle_cx"])
    template_cy = float(params["template_circle_cy"])
    template_r = float(params["template_circle_radius"])

    logs = Action.validate_badge_by_elements(img, params, max_rounds=4)

    assert logs
    assert float(params["cx"]) == pytest.approx(template_cx)
    assert float(params["cy"]) == pytest.approx(template_cy)
    assert float(params["r"]) >= template_r - 0.01


def test_make_badge_params_reanchors_ac0811_l_stem_after_template_center_lock() -> None:
    """AC0811_L should keep its stem attached to the circle after template recentering."""
    if image_composite_converter.cv2 is None:
        pytest.skip("cv2 not available in this environment")

    img = image_composite_converter.cv2.imread("artifacts/images_to_convert/AC0811_L.jpg")
    assert img is not None

    defaults = Action._default_ac0811_params(img.shape[1], img.shape[0])
    params = Action.make_badge_params(img.shape[1], img.shape[0], "AC0811", img)

    expected_top = float(params["cy"]) + float(params["r"]) - (float(params["stem_width"]) * 0.55)
    default_stem_len = float(defaults["stem_bottom"]) - float(defaults["stem_top"])
    fitted_stem_len = float(params["stem_bottom"]) - float(params["stem_top"])

    assert float(params["stem_top"]) == pytest.approx(expected_top)
    assert fitted_stem_len >= (default_stem_len * 0.90) - 0.01



def test_finalize_ac08_small_variant_keeps_only_small_variant_metadata() -> None:
    """Small AC08 `_S` variants should still flag compact mode without forcing connector bounds."""
    params = Action.make_badge_params(15, 15, "AC0832")

    assert params["ac08_small_variant_mode"] is True
    assert params["ac08_small_variant_reason"] in {"variant_suffix+min_dim", "variant_suffix", "min_dim"}
    assert int(params["validation_mask_dilate_px"]) >= 1
    assert "arm_len_min_ratio" not in params or float(params["arm_len_min_ratio"]) <= 0.75




def test_finalize_left_connector_family_leaves_geometry_unlocked() -> None:
    """Left-connector families should preserve detected geometry without shared guardrails."""
    params = Action._apply_co2_label(Action._default_ac0812_params(20, 12))
    params["template_circle_radius"] = float(params["r"])
    params["template_circle_cx"] = float(params["cx"])
    params["template_circle_cy"] = float(params["cy"])
    params["cx"] = float(params["cx"]) - 1.5
    params["cy"] = float(params["cy"]) + 1.0
    params["r"] = float(params["r"]) * 0.85

    tuned = Action._finalize_ac08_style("AC0832_S", params)

    assert "connector_family_group" not in tuned
    assert float(tuned["cx"]) == float(params["template_circle_cx"])
    assert float(tuned["cy"]) == float(params["template_circle_cy"])
    assert "arm_len_min_ratio" not in tuned
    assert "min_circle_radius" not in tuned


def test_finalize_left_connector_path_text_preserves_existing_settings() -> None:
    """Left-arm text badges should no longer synthesize connector guardrails."""
    params = Action._default_ac0882_params(45, 25)
    params["template_circle_radius"] = float(params["r"])
    params["template_circle_cx"] = float(params["cx"])
    params["template_circle_cy"] = float(params["cy"])
    params["arm_enabled"] = False

    tuned = Action._finalize_ac08_style("AC0882_L", params)

    assert tuned["arm_enabled"] is False
    assert "connector_family_group" not in tuned


def test_finalize_right_connector_family_leaves_geometry_unlocked() -> None:
    """Right-connector families should preserve detected geometry without mirrored guardrails."""
    params = Action._apply_co2_label(Action._default_ac0814_params(20, 12))
    params["template_circle_radius"] = float(params["r"])
    params["template_circle_cx"] = float(params["cx"])
    params["template_circle_cy"] = float(params["cy"])
    params["cx"] = float(params["cx"]) + 1.5
    params["cy"] = float(params["cy"]) - 1.0
    params["r"] = float(params["r"]) * 0.85
    params["arm_enabled"] = False

    tuned = Action._finalize_ac08_style("AC0834_S", params)

    assert "connector_family_group" not in tuned
    assert float(tuned["cx"]) == float(params["template_circle_cx"])
    assert float(tuned["cy"]) == float(params["template_circle_cy"])
    assert tuned["arm_enabled"] is False
    assert "arm_len_min_ratio" not in tuned
    assert "min_circle_radius" not in tuned


def test_finalize_right_connector_voc_family_preserves_existing_arm_state() -> None:
    """VOC right-arm badges should keep the existing arm state without extra bounds."""
    params = Action._apply_voc_label(Action._default_ac0814_params(45, 25))
    params["template_circle_radius"] = float(params["r"])
    params["template_circle_cx"] = float(params["cx"])
    params["template_circle_cy"] = float(params["cy"])
    params["arm_enabled"] = False

    tuned = Action._finalize_ac08_style("AC0839_L", params)

    assert "connector_family_group" not in tuned
    assert tuned["arm_enabled"] is False
    assert "voc_font_scale_min" not in tuned


def test_fit_ac0814_medium_plain_badge_allows_bounded_left_center_correction(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC0814_M should keep the traced circle from drifting right versus the source raster."""
    if image_composite_converter.np is None:
        pytest.skip("numpy not available in this environment")

    defaults = Action._default_ac0814_params(35, 20)

    def fake_fit(_img, _defaults):
        fitted = dict(defaults)
        fitted["cx"] = 11.5
        fitted["cy"] = 9.5
        fitted["r"] = 9.05
        return fitted

    monkeypatch.setattr(Action, "_fit_semantic_badge_from_image", staticmethod(fake_fit))

    np = image_composite_converter.np
    img = np.full((20, 35, 3), 220, dtype=np.uint8)
    fitted = Action._fit_ac0814_params_from_image(img, defaults)
    finalized = Action._finalize_ac08_style("AC0814_M", dict(fitted))

    assert float(fitted["cx"]) == pytest.approx(11.5, abs=0.02)
    assert float(fitted["cx"]) < float(defaults["cx"])
    assert float(finalized["cx"]) == pytest.approx(float(fitted["cx"]), abs=0.001)


def test_finalize_vertical_connector_family_leaves_geometry_unlocked() -> None:
    """Vertical families should keep detected geometry without centered connector guardrails."""
    params = Action._apply_co2_label(Action._default_ac0881_params(20, 30))
    params["template_circle_radius"] = float(params["r"])
    params["template_circle_cx"] = float(params["cx"])
    params["template_circle_cy"] = float(params["cy"])
    params["cx"] = float(params["cx"]) + 1.0
    params["cy"] = float(params["cy"]) - 1.0
    params["r"] = float(params["r"]) * 0.86
    params["stem_enabled"] = False

    tuned = Action._finalize_ac08_style("AC0831_L", params)

    assert "connector_family_group" not in tuned
    assert float(tuned["cx"]) == float(params["template_circle_cx"])
    assert float(tuned["cy"]) == float(params["template_circle_cy"])
    assert tuned["stem_enabled"] is False
    assert "stem_len_min_ratio" not in tuned
    assert "min_circle_radius" not in tuned


def test_finalize_vertical_connector_voc_family_preserves_existing_stem_state() -> None:
    """VOC vertical badges should preserve the existing stem state without extra bounds."""
    params = Action._apply_voc_label(Action._default_ac0881_params(45, 25))
    params["template_circle_radius"] = float(params["r"])
    params["template_circle_cx"] = float(params["cx"])
    params["template_circle_cy"] = float(params["cy"])
    params["stem_enabled"] = False

    tuned = Action._finalize_ac08_style("AC0836_L", params)

    assert "connector_family_group" not in tuned
    assert tuned["stem_enabled"] is False
    assert "voc_font_scale_min" not in tuned

def test_validate_badge_logs_small_variant_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validation logs should explicitly state when the `_S` small-variant mode is active."""
    if image_composite_converter.np is None:
        pytest.skip("numpy not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    img = np.full((15, 15, 3), 255, dtype=np.uint8)
    params = Action.make_badge_params(15, 15, "AC0832")

    monkeypatch.setattr(Action, "generate_badge_svg", staticmethod(lambda *_args, **_kwargs: "<svg/>"))
    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda *_args, **_kwargs: img.copy()))
    monkeypatch.setattr(Action, "_fit_to_original_size", staticmethod(lambda *_args, **_kwargs: img.copy()))
    monkeypatch.setattr(Action, "extract_badge_element_mask", staticmethod(lambda *_args, **_kwargs: np.ones((15, 15), dtype=bool)))
    monkeypatch.setattr(Action, "_element_match_error", staticmethod(lambda *_args, **_kwargs: 0.0))
    monkeypatch.setattr(Action, "_optimize_element_width_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_element_extent_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_circle_center_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_circle_radius_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "calculate_error", staticmethod(lambda *_args, **_kwargs: 7.5))

    logs = Action.validate_badge_by_elements(img, params, max_rounds=1)

    assert any(log.startswith("small_variant_mode_active:") for log in logs)


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


def test_quantize_promotes_near_canvas_fitting_circle_radius() -> None:
    """Near-border circles should snap up to the true canvas fit instead of shrinking asymmetrically."""
    params = {
        "circle_enabled": True,
        "cx": 12.5,
        "cy": 12.5,
        "r": 11.666666666666666,
        "stroke_circle": 1.0,
    }

    quantized = Action._quantize_badge_params(params, w=25, h=45)

    assert float(quantized["r"]) == pytest.approx(12.0)


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
    """Semantic mismatches should still emit a best-effort SVG artifact."""
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
        "_detect_semantic_primitives",
        staticmethod(
            lambda *_args, **_kwargs: {
                "circle": True,
                "stem": True,
                "arm": False,
                "text": False,
                "connector_orientation": "vertical",
                "horizontal_line_candidates": 0,
                "vertical_line_candidates": 2,
            }
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
    assert not (diff_dir / "AC0814_L_failed_diff.png").exists()
    log_text = (reports_dir / "AC0814_L_element_validation.log").read_text(encoding="utf-8")
    assert "status=semantic_mismatch" in log_text
    assert "best_attempt_svg=AC0814_L_failed.svg" in log_text
    assert "best_attempt_diff=AC0814_L_failed_diff.png" not in log_text
    assert "semantic_audit_status=semantic_mismatch" in log_text
    assert "semantic_audit_derived_elements=SEMANTIC: Kreis ohne Buchstabe" in log_text
    assert "semantic_audit_mismatch_reason=circle missing" in log_text
    assert "semantic_connector_classification=vertical;circle_source=unknown;horizontal_candidates=0;vertical_candidates=2" in log_text


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
    assert observed["stem"] is False
    assert observed["arm"] is False


def test_validate_semantic_description_alignment_accepts_ac0813_vertical_connector() -> None:
    """Vertical connector families should not fail semantic validation due to arm hallucinations."""
    if image_composite_converter.cv2 is None:
        pytest.skip("cv2 not available in this environment")

    img = image_composite_converter.cv2.imread("artifacts/images_to_convert/AC0813_L.jpg")
    assert img is not None

    badge_params = Action.make_badge_params(img.shape[1], img.shape[0], "AC0813", img)
    issues = Action.validate_semantic_description_alignment(
        img,
        ["SEMANTIC: Kreis ohne Buchstabe", "SEMANTIC: senkrechter Strich oben vom Kreis"],
        badge_params,
    )

    assert issues == []


def test_validate_semantic_description_alignment_ignores_structural_stem_for_left_arm_badges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Left-arm families should not fail when structural detection hallucinates a vertical stem."""
    if image_composite_converter.np is None:
        pytest.skip("numpy not available in this environment")

    np = image_composite_converter.np
    img = np.full((16, 24, 3), 240, dtype=np.uint8)
    badge_params = Action._default_ac0812_params(24, 16)

    monkeypatch.setattr(
        Action,
        "_detect_semantic_primitives",
        staticmethod(lambda _img: {"circle": True, "stem": True, "arm": False, "text": False}),
    )

    def fake_extract(_img, _params, element):
        mask = np.zeros((16, 24), dtype=np.uint8)
        if element == "circle":
            mask[4:12, 12:20] = 1
        if element == "arm":
            mask[7:9, 0:12] = 1
        return mask

    monkeypatch.setattr(Action, "extract_badge_element_mask", staticmethod(fake_extract))

    issues = Action.validate_semantic_description_alignment(
        img,
        ["SEMANTIC: Kreis ohne Buchstabe", "SEMANTIC: waagrechter Strich links vom Kreis"],
        badge_params,
    )

    assert issues == []




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


def test_in_requested_range_partial_filter_ignores_size_suffix_in_bounds() -> None:
    """Partial fallback filters should still find AC0800_* when users enter AC080_L..AC080_L."""
    assert image_composite_converter._in_requested_range("AC0800_L.jpg", "AC080_L", "AC080_L") is True


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


def test_adaptive_iteration_budget_reduces_for_early_plateau() -> None:
    assert conv._adaptive_iteration_budget_for_quality_row(
        {
            "convergence": "plateau",
            "best_iter": 24,
        },
        128,
    ) == 77


def test_adaptive_iteration_budget_increases_for_budget_edge_minimum() -> None:
    assert conv._adaptive_iteration_budget_for_quality_row(
        {
            "convergence": "max_iterations",
            "best_iter": 128,
        },
        128,
    ) == 173


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
    assert "AC0800_L;stable_good;Previously marked good plain-ring large variant" in manifest
    assert "AC0811_L;stable_good;Known regression-safe good conversion anchor" in manifest
    assert "expected_reports=Iteration_Log.csv,quality_tercile_passes.csv,pixel_delta2_ranking.csv,pixel_delta2_summary.txt,ac08_weak_family_status.csv,ac08_weak_family_status.txt,ac08_success_metrics.csv,ac08_success_criteria.txt" in summary


def test_load_successful_conversions_uses_manifest_and_allows_non_ac08_entries(tmp_path: Path) -> None:
    manifest = tmp_path / "successful_conversions.txt"
    manifest.write_text("AC0800_L ; total_delta2=22.000000\nge0015_s\nac0811_l ; mean_delta2=11.000000\n# comment\nAC0800_L\n", encoding="utf-8")

    variants = image_composite_converter._load_successful_conversions(manifest, tmp_path / "missing")
    ac08_variants = tuple(variant for variant in variants if variant.startswith("AC08"))

    assert variants == ("AC0800_L", "GE0015_S", "AC0811_L")
    assert ac08_variants == ("AC0800_L", "AC0811_L")


def test_load_successful_conversions_expands_manifest_ranges_against_available_variants(tmp_path: Path) -> None:
    manifest = tmp_path / "successful_conversions.txt"
    source_dir = tmp_path / "images"
    source_dir.mkdir()
    for name in (
        "AC0800_L.jpg",
        "AC0800_M.jpg",
        "AC0800_S.jpg",
        "AC0811_L.jpg",
        "AC0811_M.jpg",
        "AC0811_S.jpg",
        "AC0812_L.jpg",
        "AC0812_M.jpg",
        "AC0812_S.jpg",
        "GE0015_S.jpg",
    ):
        (source_dir / name).write_bytes(b"jpg")
    manifest.write_text("AC0800_L bis AC0812_S\nGE0015_S\n", encoding="utf-8")

    variants = image_composite_converter._load_successful_conversions(manifest, source_dir)

    assert variants == (
        "AC0800_L",
        "AC0800_M",
        "AC0800_S",
        "AC0811_L",
        "AC0811_M",
        "AC0811_S",
        "AC0812_L",
        "AC0812_M",
        "AC0812_S",
        "GE0015_S",
    )


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
    (reports_dir / "AC0800_L_element_validation.log").write_text(
        "run-meta: seed=1\nstatus=semantic_ok\nRunde 1: elementweise Validierung gestartet\n",
        encoding="utf-8",
    )
    (reports_dir / "AC0800_M_element_validation.log").write_text(
        "run-meta: seed=1\nstatus=semantic_ok\nRunde 1: elementweise Validierung gestartet\n",
        encoding="utf-8",
    )
    (reports_dir / "AC0800_S_element_validation.log").write_text(
        "run-meta: seed=1\nstatus=semantic_ok\nRunde 1: elementweise Validierung gestartet\n",
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
    metric_rows = {}
    for line in metrics.strip().splitlines()[1:]:
        key, value = line.split(";", 1)
        metric_rows[key] = value

    known_logs = {
        "AC0800_L": "semantic_ok",
        "AC0800_M": "semantic_ok",
        "AC0800_S": "semantic_ok",
        "AC0811_L": "semantic_mismatch",
        "AC0820_L": "other",
    }
    expected_previous_good = set(image_composite_converter.AC08_PREVIOUSLY_GOOD_VARIANTS)
    expected_preserved = sum(1 for v, status in known_logs.items() if v in expected_previous_good and status == "semantic_ok")
    expected_regressed = sum(1 for v, status in known_logs.items() if v in expected_previous_good and status != "semantic_ok")
    expected_missing = len(expected_previous_good) - expected_preserved - expected_regressed

    assert metric_rows["previous_good_expected"] == str(len(expected_previous_good))
    assert metric_rows["previous_good_preserved_count"] == str(expected_preserved)
    assert metric_rows["previous_good_regressed_count"] == str(expected_regressed)
    assert metric_rows["previous_good_missing_count"] == str(expected_missing)
    assert float(metric_rows["mean_validation_rounds_per_file"]) > 0.0
    assert "criterion_validation_rounds_recorded;1" in metrics
    assert "criterion_no_new_batch_aborts=0" in summary
    assert "previous_good_regressed=AC0811_L" in summary
    assert "criterion_no_accepted_regressions=1" in summary
    assert "criterion_validation_rounds_recorded=1" in summary
    assert "criterion_regression_set_improved=1" in summary
    assert "overall_success=0" in summary


def test_summarize_previous_good_ac08_variants_detects_regressions(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "AC0800_L_element_validation.log").write_text("status=semantic_ok\n", encoding="utf-8")
    (reports_dir / "AC0800_M_element_validation.log").write_text("status=semantic_ok\n", encoding="utf-8")
    (reports_dir / "AC0800_S_element_validation.log").write_text("status=semantic_mismatch\n", encoding="utf-8")

    summary = image_composite_converter._summarize_previous_good_ac08_variants(str(reports_dir))

    assert summary["expected"] == list(image_composite_converter.AC08_PREVIOUSLY_GOOD_VARIANTS)
    assert summary["preserved"] == ["AC0800_L", "AC0800_M"]
    assert summary["regressed"] == ["AC0800_S"]
    assert summary["missing"] == ["AC0811_L"]


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


def test_global_parameter_vector_roundtrip_preserves_core_fields() -> None:
    params = {
        "cx": 11.5,
        "cy": 12.0,
        "r": 6.5,
        "arm_x1": 0.0,
        "arm_y1": 12.0,
        "arm_stroke": 1.0,
        "stem_x": 11.0,
        "stem_width": 1.2,
        "text_x": 11.5,
        "text_y": 13.0,
        "text_scale": 0.9,
    }

    vector = image_composite_converter.GlobalParameterVector.from_params(params)
    restored = vector.apply_to_params({})

    assert float(restored["cx"]) == 11.5
    assert float(restored["cy"]) == 12.0
    assert float(restored["r"]) == 6.5
    assert float(restored["arm_stroke"]) == 1.0
    assert float(restored["stem_width"]) == 1.2
    assert float(restored["text_scale"]) == 0.9


def test_optimize_circle_pose_adaptive_domain_logs_global_vector_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((20, 20, 3), 220, dtype=np.uint8)
    params = {"circle_enabled": True, "cx": 5.0, "cy": 6.0, "r": 3.0, "min_circle_radius": 1.0}

    monkeypatch.setattr(
        Action,
        "_element_error_for_circle_pose",
        staticmethod(lambda *_args, **_kwargs: 1.0),
    )
    logs: list[str] = []

    Action._optimize_circle_pose_adaptive_domain(img, params, logs, rounds=1, samples_per_round=8)

    assert any("adaptive-start: global_vector" in line for line in logs)
    assert any("src=canvas" in line for line in logs)
    assert any("src=semantic" in line for line in logs)


def test_optimize_global_parameter_vector_sampling_improves_multiple_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((24, 24, 3), 220, dtype=np.uint8)
    params = {
        "enable_global_search_mode": True,
        "circle_enabled": True,
        "cx": 5.0,
        "cy": 5.0,
        "r": 2.0,
        "stem_enabled": True,
        "stem_x": 3.0,
        "stem_top": 7.0,
        "stem_bottom": 15.0,
        "stem_width": 1.0,
        "draw_text": True,
        "text_x": 4.0,
        "text_y": 4.0,
        "text_scale": 0.5,
        "min_circle_radius": 1.0,
    }
    target = {"cx": 12.0, "cy": 11.0, "r": 6.0, "text_x": 12.0, "text_y": 12.0, "text_scale": 1.0}

    def fake_full_error(_img, candidate_params):
        err = 0.0
        for key, center in target.items():
            err += abs(float(candidate_params.get(key, 0.0)) - center)
        return float(err)

    monkeypatch.setattr(Action, "_full_badge_error_for_params", staticmethod(fake_full_error))
    logs: list[str] = []
    start = {k: float(params[k]) for k in target}

    changed = Action._optimize_global_parameter_vector_sampling(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=14,
    )

    assert changed is True
    end = {k: float(params[k]) for k in target}
    assert sum(abs(end[k] - target[k]) for k in target) < sum(abs(start[k] - target[k]) for k in target)
    assert any("aktive_parameter=" in line for line in logs)
    assert any("akzeptierte_kandidaten=" in line for line in logs)


def test_optimize_global_parameter_vector_sampling_logs_global_near_optimum_plateau(monkeypatch: pytest.MonkeyPatch) -> None:
    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((24, 24, 3), 220, dtype=np.uint8)
    params = {
        "enable_global_search_mode": True,
        "circle_enabled": True,
        "cx": 6.0,
        "cy": 6.0,
        "r": 3.0,
        "stem_enabled": True,
        "stem_x": 4.0,
        "stem_top": 9.0,
        "stem_bottom": 15.0,
        "stem_width": 1.0,
        "draw_text": True,
        "text_x": 5.0,
        "text_y": 5.0,
        "text_scale": 0.8,
        "min_circle_radius": 1.0,
    }

    def fake_full_error(_img, candidate_params):
        cx = float(candidate_params.get("cx", 0.0))
        cy = float(candidate_params.get("cy", 0.0))
        text_x = float(candidate_params.get("text_x", 0.0))
        return abs(cx - 10.0) + abs(cy - 10.0) + abs(text_x - 10.0)

    monkeypatch.setattr(Action, "_full_badge_error_for_params", staticmethod(fake_full_error))
    logs: list[str] = []

    changed = Action._optimize_global_parameter_vector_sampling(
        img,
        params,
        logs,
        rounds=2,
        samples_per_round=12,
    )

    assert changed is True
    assert any("near-optimum-definition" in line for line in logs)
    plateau_lines = [line for line in logs if "near-optimum-plateau" in line]
    assert len(plateau_lines) == 2
    assert all("punkte=" in line and "spannweite=" in line for line in plateau_lines)
    representative_lines = [line for line in logs if "plateau-repräsentant" in line]
    assert len(representative_lines) == 2
    assert all("kandidat=" in line and "begründung=" in line for line in representative_lines)


def test_optimize_global_parameter_vector_sampling_uses_run_seed_offset(monkeypatch: pytest.MonkeyPatch) -> None:
    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((24, 24, 3), 220, dtype=np.uint8)
    params = {
        "enable_global_search_mode": True,
        "circle_enabled": True,
        "cx": 6.0,
        "cy": 6.0,
        "r": 3.0,
        "stem_enabled": True,
        "stem_x": 4.0,
        "stem_top": 9.0,
        "stem_bottom": 15.0,
        "stem_width": 1.0,
        "draw_text": True,
        "text_x": 5.0,
        "text_y": 5.0,
        "text_scale": 0.8,
        "min_circle_radius": 1.0,
    }

    monkeypatch.setattr(Action, "_full_badge_error_for_params", staticmethod(lambda *_args, **_kwargs: 1.0))

    captured: list[int] = []

    def fake_make_rng(seed: int):
        captured.append(int(seed))
        return Action._ScalarRng(int(seed))

    monkeypatch.setattr(Action, "_make_rng", staticmethod(fake_make_rng))
    monkeypatch.setattr(Action, "STOCHASTIC_RUN_SEED", 123, raising=False)
    monkeypatch.setattr(Action, "STOCHASTIC_SEED_OFFSET", 7, raising=False)

    logs: list[str] = []
    Action._optimize_global_parameter_vector_sampling(img, params, logs, rounds=1, samples_per_round=8)

    assert captured == [4229]


def test_optimize_global_parameter_vector_sampling_respects_locks_and_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((20, 20, 3), 220, dtype=np.uint8)
    params = {
        "enable_global_search_mode": True,
        "circle_enabled": True,
        "cx": 8.0,
        "cy": 7.0,
        "r": 3.0,
        "min_circle_radius": 2.0,
        "lock_circle_cx": True,
        "stem_enabled": True,
        "stem_x": 1.0,
        "stem_top": 10.0,
        "stem_bottom": 17.0,
        "stem_width": 1.0,
        "draw_text": True,
        "text_x": 8.0,
        "text_y": 9.0,
        "text_scale": 0.8,
        "lock_text_position": True,
    }

    start_cx = float(params["cx"])
    start_text_x = float(params["text_x"])
    start_text_y = float(params["text_y"])
    initial_bounds = Action._global_parameter_vector_bounds(params, img.shape[1], img.shape[0])

    def fake_full_error(_img, candidate_params):
        # Pulls the optimizer toward extreme values, so clamping/locks are exercised.
        return float(
            abs(float(candidate_params.get("cy", 0.0)) - 999.0)
            + abs(float(candidate_params.get("r", 0.0)) - 999.0)
            + abs(float(candidate_params.get("stem_x", 0.0)) - 999.0)
            + abs(float(candidate_params.get("stem_width", 0.0)) - 999.0)
            + abs(float(candidate_params.get("text_scale", 0.0)) - 99.0)
        )

    monkeypatch.setattr(Action, "_full_badge_error_for_params", staticmethod(fake_full_error))
    logs: list[str] = []

    Action._optimize_global_parameter_vector_sampling(img, params, logs, rounds=2, samples_per_round=12)

    assert float(params["cx"]) == start_cx
    assert float(params["text_x"]) == start_text_x
    assert float(params["text_y"]) == start_text_y

    for key in ("cy", "r", "stem_x", "stem_width", "text_scale"):
        low, high, _locked, _source = initial_bounds[key]
        value = float(params[key])
        assert low <= value <= high


def test_optimize_global_parameter_vector_sampling_disabled_by_default() -> None:
    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")
    img = np.full((16, 16, 3), 220, dtype=np.uint8)
    params = {"circle_enabled": True, "cx": 8.0, "cy": 8.0, "r": 4.0, "text_x": 8.0, "text_y": 8.0, "text_scale": 1.0}
    logs: list[str] = []

    changed = Action._optimize_global_parameter_vector_sampling(img, params, logs)

    assert changed is False
    assert logs == []


def test_validate_badge_by_elements_runs_global_search_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Element validation should execute one global-search pass when the mode flag is enabled."""
    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    img = np.full((16, 16, 3), 220, dtype=np.uint8)
    params = {
        "enable_global_search_mode": True,
        "circle_enabled": True,
        "cx": 8.0,
        "cy": 8.0,
        "r": 4.0,
        "draw_text": False,
    }

    monkeypatch.setattr(Action, "generate_badge_svg", staticmethod(lambda *_args, **_kwargs: "<svg/>"))
    monkeypatch.setattr(Action, "render_svg_to_numpy", staticmethod(lambda *_args, **_kwargs: img))
    monkeypatch.setattr(Action, "_fit_to_original_size", staticmethod(lambda *_args, **_kwargs: img))
    monkeypatch.setattr(Action, "extract_badge_element_mask", staticmethod(lambda *_args, **_kwargs: np.ones((16, 16), dtype=bool)))
    monkeypatch.setattr(Action, "_element_match_error", staticmethod(lambda *_args, **_kwargs: 0.0))
    monkeypatch.setattr(Action, "_optimize_element_width_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_element_extent_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_circle_center_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_circle_radius_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_optimize_element_color_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(Action, "_apply_canonical_badge_colors", staticmethod(lambda current: current))
    monkeypatch.setattr(Action, "calculate_error", staticmethod(lambda *_args, **_kwargs: 0.0))

    calls: list[bool] = []

    def fake_global_search(_img_orig, _params, _logs, *, rounds=3, samples_per_round=16):
        calls.append(True)
        return False

    monkeypatch.setattr(Action, "_optimize_global_parameter_vector_sampling", staticmethod(fake_global_search))

    logs = Action.validate_badge_by_elements(img, params, max_rounds=1)

    assert calls == [True]
    assert any("Runde 1: elementweise Validierung gestartet" in entry for entry in logs)


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


def test_finalize_ac0820_keeps_text_scale_unbounded() -> None:
    """AC0820 should no longer inject bounded CO₂ scale tuning metadata."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params = Action._finalize_ac08_style("AC0820", params)

    assert "lock_text_scale" not in params
    assert "co2_font_scale_min" not in params
    assert "co2_font_scale_max" not in params


def test_finalize_vertical_non_ac0820_co2_keeps_text_scale_unbounded() -> None:
    """Vertical non-AC0820 CO₂ badges should no longer inject bounded text tuning."""
    params = Action._apply_co2_label(Action._default_ac0881_params(20, 20))
    params = Action._finalize_ac08_style("AC0831", params)

    assert "lock_text_scale" not in params
    assert "co2_font_scale_min" not in params
    assert "co2_font_scale_max" not in params


def test_make_badge_params_applies_ac0831_vertical_co2_tuning() -> None:
    """AC0831 should use cluster-centered CO² placement with compact sizing."""
    params = Action.make_badge_params(25, 45, "AC0831", None)

    assert params["co2_anchor_mode"] == "cluster"
    assert params["co2_index_mode"] == "superscript"
    assert float(params["co2_optical_bias"]) >= 0.08
    assert float(params["co2_font_scale"]) <= 0.74
    assert float(params["co2_sub_font_scale"]) <= 48.0
    assert float(params["co2_dy"]) >= 0.35
    assert float(params["co2_superscript_min_gap_scale"]) >= 0.19


def test_make_badge_params_applies_compact_ac0831_small_variant_text_tuning() -> None:
    """Tiny AC0831 variants should keep the CO² cluster tight and readable."""
    params = Action.make_badge_params(15, 25, "AC0831", None)

    assert params["co2_anchor_mode"] == "cluster"
    assert params["co2_index_mode"] == "superscript"
    assert float(params["co2_font_scale"]) <= 0.74
    assert float(params["co2_sub_font_scale"]) <= 48.0
    assert float(params["co2_dy"]) >= 0.35
    assert float(params["co2_superscript_min_gap_scale"]) >= 0.19


def test_make_badge_params_ac0832_l_uses_superscript_two() -> None:
    """AC0832_L should render CO² with a raised 2 instead of subscript CO₂."""
    params = Action._apply_co2_label(Action._default_ac0812_params(25, 25))
    params = Action._tune_ac0832_co2_badge(params)
    params = Action._finalize_ac08_style("AC0832_L", params)

    assert params["co2_index_mode"] == "superscript"
    assert float(params["co2_superscript_offset_scale"]) <= 0.11


def test_co2_layout_superscript_keeps_clear_gap_from_o_glyph() -> None:
    """Superscript CO² rendering should keep a visible horizontal gap before the raised 2."""
    params = Action._apply_co2_label(Action._default_ac0812_params(25, 25))
    params = Action._tune_ac0832_co2_badge(params)
    layout = Action._co2_layout(params)

    co_width = float(layout["font_size"]) * 1.04 * float(layout["width_scale"])
    o_right = float(layout["co_x"]) + (co_width / 2.0)
    superscript_gap = float(layout["subscript_x"]) - o_right

    assert superscript_gap >= float(layout["font_size"]) * 0.06


def test_normalize_centered_co2_label_reduces_oversized_co_cluster() -> None:
    """Centered CO₂ labels should stay clearly smaller than the enclosing ring."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params["co2_font_scale"] = 1.25

    tuned = Action._normalize_centered_co2_label(params)

    assert float(tuned["co2_font_scale"]) <= 0.96


def test_make_badge_params_ac0820_l_uses_compact_co2_scale() -> None:
    """AC0820_L should avoid an oversized 'C' relative to the circle diameter."""
    params = Action.make_badge_params(30, 30, "AC0820", None)

    assert params["co2_anchor_mode"] == "center_co"
    assert float(params["co2_font_scale"]) <= 0.82


def test_finalize_tiny_non_ac0820_co2_keeps_text_scale_unbounded() -> None:
    """Tiny CO₂ variants should also skip bounded text tuning metadata."""
    params = Action._apply_co2_label(Action._default_ac0813_params(15, 25))
    params = Action._finalize_ac08_style("AC0833_S", params)

    assert "lock_text_scale" not in params
    assert "co2_font_scale_min" not in params
    assert "co2_font_scale_max" not in params


def test_release_ac08_adaptive_locks_is_disabled_without_guardrails() -> None:
    """Adaptive lock release should be a no-op once guardrails are removed."""
    params = Action._apply_co2_label(Action._default_ac0881_params(20, 20))
    params = Action._finalize_ac08_style("AC0831", params)
    params["template_circle_radius"] = float(params["r"])
    params["stem_enabled"] = True
    params["stem_top"] = 12.0
    params["stem_bottom"] = 20.0
    params["stem_len_min_ratio"] = 0.65
    params["stem_len_min"] = 5.2
    logs: list[str] = []

    changed = Action._release_ac08_adaptive_locks(
        params,
        logs,
        reason="stagnation_same_fingerprint",
        current_error=12.5,
    )

    assert changed is False
    assert "adaptive_lock_release_active" not in params
    assert logs == []


def test_optimize_element_color_bracket_respects_adaptive_color_corridor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adaptive palette release must stay within the configured grayscale corridor."""
    if image_composite_converter.np is None:
        pytest.skip("numpy not available in this environment")

    img = image_composite_converter.np.full((4, 4, 3), 220, dtype=image_composite_converter.np.uint8)
    mask = image_composite_converter.np.ones((4, 4), dtype=image_composite_converter.np.uint8)
    params = {
        "circle_enabled": True,
        "fill_gray": 220,
        "fill_gray_min": 214,
        "fill_gray_max": 226,
        "lock_colors": False,
    }
    logs: list[str] = []

    monkeypatch.setattr(Action, "_mean_gray_for_mask", staticmethod(lambda *_args, **_kwargs: 245.0))
    monkeypatch.setattr(
        Action,
        "_element_error_for_color",
        staticmethod(lambda _img, _params, _element, _color_key, color_value, _mask: abs(color_value - 226)),
    )

    changed = Action._optimize_element_color_bracket(img, params, "circle", mask, logs)

    assert changed is True
    assert int(params["fill_gray"]) == 226
    assert int(params["fill_gray"]) <= int(params["fill_gray_max"])
    assert int(params["fill_gray"]) >= int(params["fill_gray_min"])

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
    assert abs(float(fixed["arm_x2"]) - 22.0) < 1e-6
    assert abs(float(fixed["arm_y2"]) - 12.5) < 1e-6
    assert float(fixed["arm_len_min"]) >= 22.0 * 0.75


def test_tune_ac08_left_connector_family_keeps_template_right_extent() -> None:
    """Left-connector families should keep most of the template right edge circle extent."""
    defaults = Action._default_ac0812_params(25, 15)
    params = {
        **defaults,
        "width": 25,
        "height": 15,
        "template_circle_cx": float(defaults["cx"]),
        "template_circle_radius": float(defaults["r"]),
        "cx": float(defaults["cx"]),
        # Simulate a run where the fitted circle got too small on the right edge.
        "r": float(defaults["r"]) * 0.78,
        "draw_text": False,
        "arm_enabled": True,
    }

    tuned = Action._tune_ac08_left_connector_family("AC0812_M", params)
    min_r = float(tuned.get("min_circle_radius", 1.0))
    required_r = (float(params["template_circle_cx"]) + float(params["template_circle_radius"])) * 0.97 - float(params["cx"])

    assert min_r >= required_r - 1e-6


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


def test_finalize_ac08_style_leaves_ac0835_s_voc_unbounded() -> None:
    """AC0835_S should not inject centered-family VOC bounds anymore."""
    params = Action._apply_voc_label(Action._default_ac0870_params(15, 15))
    params["template_circle_radius"] = float(params["r"])
    params["template_circle_cx"] = 7.5
    params["template_circle_cy"] = 7.5
    params["cx"] = 6.0
    params["cy"] = 9.0
    params["r"] = float(params["r"]) * 0.82

    tuned = Action._finalize_ac08_style("AC0835_S", params)

    assert "connector_family_group" not in tuned
    assert float(tuned["cx"]) == float(params["template_circle_cx"])
    assert float(tuned["cy"]) == float(params["template_circle_cy"])
    assert "min_circle_radius" not in tuned
    assert "voc_font_scale_min" not in tuned
    assert "voc_font_scale_max" not in tuned


def test_tune_ac0835_voc_badge_lowers_tiny_variant_text() -> None:
    """AC0835_S should start with a lower VOC baseline to match the source raster."""
    params = Action._apply_voc_label(Action._default_ac0870_params(15, 15))

    tuned = Action._tune_ac0835_voc_badge(params, 15, 15)

    assert float(tuned["voc_dy"]) >= float(tuned["r"]) * 0.13
    assert int(tuned["text_gray"]) == Action.LIGHT_CIRCLE_STROKE_GRAY


def test_finalize_ac08_circle_text_family_leaves_ac0820_unlocked() -> None:
    """AC0820 should no longer inject centered-family circle/text guardrails."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params["template_circle_radius"] = float(params["r"])
    params["template_circle_cx"] = 15.0
    params["template_circle_cy"] = 15.0
    params["cx"] = 13.0
    params["cy"] = 12.0
    params["r"] = float(params["r"]) * 0.84

    tuned = Action._finalize_ac08_style("AC0820_L", params)

    assert "connector_family_group" not in tuned
    assert float(tuned["cx"]) == float(params["template_circle_cx"])
    assert float(tuned["cy"]) == float(params["template_circle_cy"])
    assert tuned["co2_anchor_mode"] == "center_co"
    assert float(tuned["co2_width_scale"]) <= 0.89
    assert float(tuned["co2_dy"]) >= float(params["template_circle_radius"]) * 0.03
    assert float(tuned["co2_center_co_bias"]) <= -0.05
    assert "min_circle_radius" not in tuned
    assert "max_circle_radius" not in tuned


def test_finalize_ac0820_l_keeps_circle_radius_at_template_scale() -> None:
    """AC0820_L should not collapse into a tiny ring during unconstrained fitting rounds."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params["template_circle_radius"] = float(params["r"])
    params["r"] = float(params["template_circle_radius"]) * 0.60

    tuned = Action._finalize_ac08_style("AC0820_L", params)

    assert float(tuned["r"]) >= float(params["template_circle_radius"])
    assert "min_circle_radius" not in tuned



def test_finalize_ac0820_l_enforces_minimum_diameter_over_half_image_width() -> None:
    """AC0820_L should keep 2r strictly larger than half of the image width."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params["width"] = 30
    params["r"] = 7.0

    tuned = Action._finalize_ac08_style("AC0820_L", params)

    assert (2.0 * float(tuned["r"])) > (float(params["width"]) / 2.0)
    assert float(tuned["circle_radius_lower_bound_px"]) > (float(params["width"]) / 4.0)
    assert "allow_circle_overflow" not in tuned


def test_clamp_circle_with_text_enforces_strict_diameter_less_than_width() -> None:
    params = {
        "circle_enabled": True,
        "draw_text": True,
        "cx": 10.0,
        "cy": 10.0,
        "r": 10.0,
        "stroke_circle": 0.0,
    }
    clamped = Action._clamp_circle_inside_canvas(params, 20, 20)
    assert (2.0 * float(clamped["r"])) < 20.0


def test_clamp_circle_with_text_keeps_radius_above_half_text_width() -> None:
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params["draw_text"] = True
    params["cx"] = 15.0
    params["cy"] = 15.0
    params["r"] = 3.0
    params["stroke_circle"] = 0.0
    x1, _y1, x2, _y2 = Action._text_bbox(params)

    clamped = Action._clamp_circle_inside_canvas(params, 30, 30)

    assert float(clamped["r"]) > ((float(x2) - float(x1)) / 2.0)
    assert (2.0 * float(clamped["r"])) < 30.0


def test_clamp_plain_circle_without_text_keeps_canvas_limited_half_width_radius() -> None:
    params = {
        "circle_enabled": True,
        "draw_text": False,
        "cx": 10.0,
        "cy": 10.0,
        "r": 10.0,
        "stroke_circle": 0.0,
    }
    clamped = Action._clamp_circle_inside_canvas(params, 20, 20)
    assert float(clamped["r"]) == pytest.approx(10.0)


def test_finalize_ac0820_large_canvas_does_not_force_large_circle_radius_constraint() -> None:
    """Base AC0820 names should not inherit an AC0820_L overflow radius rule."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params["width"] = 30
    params["r"] = 8.0

    tuned = Action._finalize_ac08_style("AC0820", params)

    assert float(tuned["r"]) <= (float(params["width"]) / 2.0)
    assert "allow_circle_overflow" not in tuned


def test_finalize_ac0820_variant_name_does_not_force_large_circle_radius_constraint() -> None:
    """AC0820 with variant_name AC0820_L should still avoid overflow radius floors."""
    params = Action._apply_co2_label(Action._default_ac0870_params(20, 20))
    params["variant_name"] = "AC0820_L"
    params["width"] = 30
    params["r"] = 8.0

    tuned = Action._finalize_ac08_style("AC0820", params)

    assert float(tuned["r"]) <= 15.0
    assert "allow_circle_overflow" not in tuned



def test_finalize_ac08_circle_text_family_leaves_ac0870_geometry_as_detected() -> None:
    """AC0870 should no longer be recentered by shared circle/text guardrails."""
    params = Action._default_ac0870_params(30, 30)
    params["template_circle_radius"] = float(params["r"])
    params["template_circle_cx"] = 15.0
    params["template_circle_cy"] = 15.0
    params["cx"] = 12.5
    params["cy"] = 17.0
    params["r"] = float(params["r"]) * 0.88
    params["s"] = 0.008

    tuned = Action._finalize_ac08_style("AC0870_S", params)

    assert "connector_family_group" not in tuned
    assert float(tuned["cx"]) == float(params["template_circle_cx"])
    assert float(tuned["cy"]) == float(params["template_circle_cy"])
    assert float(tuned["s"]) == 0.008

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


def test_co2_text_width_bracketing_uses_default_domain_for_ac0820() -> None:
    """AC0820 text width bracketing should fall back to the default domain without explicit bounds."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820", params)

    key, low, high = Action._element_width_key_and_bounds("text", params, 30, 30)
    assert key == "co2_font_scale"
    assert float(low) <= float(params["co2_font_scale"]) <= float(high)
    assert "co2_font_scale_min" not in params
    assert "co2_font_scale_max" not in params


def test_finalize_ac0820_leaves_palette_unlocked() -> None:
    """AC08xx semantic badges should no longer lock the grayscale palette."""
    params = Action._apply_co2_label(Action._default_ac0870_params(30, 30))
    params = Action._finalize_ac08_style("AC0820", params)

    assert "lock_colors" not in params


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


def test_activate_ac08_adaptive_locks_is_disabled_without_guardrails() -> None:
    """Adaptive AC08 unlocks should be a no-op once guardrails are removed."""
    params = Action._finalize_ac08_style(
        "AC0839",
        {
            "width": 14,
            "height": 14,
            "circle_enabled": True,
            "arm_enabled": True,
            "draw_text": True,
            "text_mode": "voc",
            "cx": 7.0,
            "cy": 7.0,
            "r": 4.0,
            "min_circle_radius": 3.8,
            "arm_x1": 7.0,
            "arm_y1": 7.0,
            "arm_x2": 13.0,
            "arm_y2": 7.0,
            "arm_len_min_ratio": 0.75,
            "fill_gray": 220,
            "stroke_gray": 152,
            "text_gray": 152,
            "voc_font_scale": 0.52,
        },
    )
    logs: list[str] = []

    changed = Action._activate_ac08_adaptive_locks(
        params,
        logs,
        full_err=19.5,
        reason="unit_test",
    )

    assert changed is False
    assert "adaptive_unlock_active" not in params
    assert logs == []


def test_optimize_element_color_bracket_respects_adaptive_color_corridor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adaptive unlock color tuning must stay inside the configured narrow palette corridor."""
    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    img = np.zeros((8, 8, 3), dtype=np.uint8)
    mask = np.ones((8, 8), dtype=np.uint8)
    params = {
        "circle_enabled": True,
        "fill_gray": 220,
        "stroke_gray": 152,
        "lock_colors": False,
        "fill_gray_min": 214,
        "fill_gray_max": 226,
    }
    logs: list[str] = []
    seen_values: list[int] = []

    def fake_error(_img, _params, _element, color_key, color_value, _mask):
        if color_key == "fill_gray":
            seen_values.append(int(color_value))
        return float(abs(int(color_value) - 226))

    monkeypatch.setattr(Action, "_element_error_for_color", staticmethod(fake_error))

    changed = Action._optimize_element_color_bracket(img, params, "circle", mask, logs)

    assert changed is True
    assert params["fill_gray"] == 226
    assert seen_values
    assert min(seen_values) >= 214
    assert max(seen_values) <= 226

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
    assert params["semantic_conflicts"] == []


def test_expected_semantic_presence_does_not_treat_circle_ohne_buchstabe_as_text() -> None:
    expected = image_composite_converter.Action._expected_semantic_presence([
        "SEMANTIC: Kreis ohne Buchstabe",
        "SEMANTIC: senkrechter Strich hinter dem Kreis",
    ])

    assert expected["circle"] is True
    assert expected["stem"] is True
    assert expected["arm"] is False
    assert expected["text"] is False


def test_validate_semantic_alignment_accepts_vertical_circle_when_raw_hough_misses() -> None:
    """Vertical connector families should accept a robust local circle mask when raw circle detection misses the ring."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    cv2 = image_composite_converter.cv2
    img = cv2.imread("artifacts/images_to_convert/AC0811_M.jpg")
    assert img is not None

    params = Action.make_badge_params(img.shape[1], img.shape[0], "AC0811", img)
    issues = Action.validate_semantic_description_alignment(
        img,
        ["SEMANTIC: Kreis ohne Buchstabe", "SEMANTIC: senkrechter Strich hinter dem Kreis"],
        params,
    )

    assert "Beschreibung erwartet Kreis, im Bild aber nicht robust erkennbar" not in issues
    assert "Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt" not in issues
    assert "Im Bild ist waagrechter Strich erkennbar, aber nicht in der Beschreibung enthalten" not in issues


def test_validate_semantic_alignment_accepts_ac0814_small_horizontal_connector() -> None:
    """Tiny AC0814_S crops should keep circle+right-arm semantics despite anti-aliasing blur."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    cv2 = image_composite_converter.cv2
    img = cv2.imread("artifacts/images_to_convert/AC0814_S.jpg")
    assert img is not None

    params = Action.make_badge_params(img.shape[1], img.shape[0], "AC0814", img)
    issues = Action.validate_semantic_description_alignment(
        img,
        ["SEMANTIC: Kreis ohne Buchstabe", "SEMANTIC: waagrechter Strich rechts vom Kreis"],
        params,
    )

    assert "Beschreibung erwartet Kreis, im Bild aber nicht robust erkennbar" not in issues
    assert "Beschreibung erwartet waagrechter Strich, im Bild aber nicht robust erkennbar" not in issues
    assert "Im Bild ist senkrechter Strich erkennbar, aber nicht in der Beschreibung enthalten" not in issues
    assert "Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt" not in issues
    assert "Strukturprüfung: Kein belastbarer waagrechter Linien-Kandidat im Rohbild erkannt" not in issues


def test_validate_semantic_alignment_accepts_ac0870_small_circle_text_variant() -> None:
    """Tiny AC0870_S crops should retain circle+text semantics despite soft raster edges."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    cv2 = image_composite_converter.cv2
    img = cv2.imread("artifacts/images_to_convert/AC0870_S.jpg")
    assert img is not None

    params = Action.make_badge_params(img.shape[1], img.shape[0], "AC0870", img)
    issues = Action.validate_semantic_description_alignment(
        img,
        ["SEMANTIC: Kreis + Buchstabe VOC"],
        params,
    )

    assert "Beschreibung erwartet Kreis, im Bild aber nicht robust erkennbar" not in issues
    assert "Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt" not in issues


def test_detect_semantic_primitives_reports_family_circle_fallback_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """Semantic primitive detection should expose when AC08 small-family fallback provided circle evidence."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    cv2 = image_composite_converter.cv2
    img = cv2.imread("artifacts/images_to_convert/AC0814_S.jpg")
    assert img is not None

    params = Action.make_badge_params(img.shape[1], img.shape[0], "AC0814", img)
    assert params is not None

    monkeypatch.setattr(cv2, "HoughCircles", lambda *args, **kwargs: None)
    monkeypatch.setattr(Action, "_circle_from_foreground_mask", staticmethod(lambda _mask: None))

    structural = Action._detect_semantic_primitives(img, params)

    assert structural["circle"] is True
    assert structural["circle_detection_source"] == "family_fallback"


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
    expected_attach = float(restored["cx"]) - float(restored["r"]) - (float(restored["arm_stroke"]) / 2.0)
    assert abs(float(restored["arm_x2"]) - expected_attach) < 1e-6


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
    expected_attach = float(restored["cx"]) - float(restored["r"]) - (float(restored["arm_stroke"]) / 2.0)
    assert abs(float(restored["arm_x2"]) - expected_attach) < 1e-6


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

    assert changed is False


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


def test_parse_args_uses_default_folder_path_when_only_helper_flags_are_used() -> None:
    args = conv.parse_args(["--print-linux-vendor-command"])

    assert args.folder_path == "artifacts/images_to_convert"


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


def test_parse_args_accepts_descriptions_path_alias_and_named_iterations() -> None:
    args = conv.parse_args(
        [
            "in_folder",
            "out_dir",
            "--descriptions-path",
            "mapping.xml",
            "--iterations",
            "12",
        ]
    )

    assert args.csv_path == "mapping.xml"
    assert args.iterations == 12


def test_readme_links_local_workflow_doc() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "docs/image_converter_workflow.md" in readme


def test_local_workflow_doc_tracks_current_commands() -> None:
    workflow_doc = Path("docs/image_converter_workflow.md").read_text(encoding="utf-8")

    assert "python -m compileall src tests" in workflow_doc
    assert "python -m pytest" in workflow_doc
    assert "python -m src.image_composite_converter --help" in workflow_doc
    assert "--descriptions-path" in workflow_doc
    assert "--ac08-regression-set" in workflow_doc
    assert "--print-linux-vendor-command" in workflow_doc


def test_parse_args_help_mentions_canonical_image_converter_flags(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        conv.parse_args(["--help"])

    captured = capsys.readouterr()

    assert excinfo.value.code == 0
    assert "--descriptions-path" in captured.out
    assert "--iterations" in captured.out
    assert "python -m src.image_composite_converter --print-linux-vendor-command" in captured.out


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


def test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC08 problem families should widen bounded search space before giving up on stagnation."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    params = Action._finalize_ac08_style(
        "AC0831",
        {
            "width": 18,
            "height": 18,
            "circle_enabled": True,
            "stem_enabled": True,
            "arm_enabled": False,
            "draw_text": True,
            "text_mode": "co2",
            "cx": 9.0,
            "cy": 7.0,
            "r": 4.0,
            "stem_x": 8.5,
            "stem_top": 11.0,
            "stem_bottom": 17.0,
            "stem_width": 1.0,
            "fill_gray": 220,
            "stroke_gray": 152,
            "text_gray": 152,
            "co2_font_scale": 0.82,
        },
    )
    img = np.zeros((18, 18, 3), dtype=np.uint8)

    monkeypatch.setattr(conv.Action, "generate_badge_svg", staticmethod(lambda *_args, **_kwargs: "<svg />"))
    monkeypatch.setattr(conv.Action, "render_svg_to_numpy", staticmethod(lambda *_args, **_kwargs: img.copy()))
    monkeypatch.setattr(conv.Action, "_fit_to_original_size", staticmethod(lambda _orig, rendered: rendered))
    monkeypatch.setattr(conv.Action, "create_diff_image", staticmethod(lambda *_args, **_kwargs: img.copy()))
    monkeypatch.setattr(conv.Action, "extract_badge_element_mask", staticmethod(lambda *_args, **_kwargs: np.ones((18, 18), dtype=bool)))
    monkeypatch.setattr(conv.Action, "_element_match_error", staticmethod(lambda *_args, **_kwargs: 1.0))
    monkeypatch.setattr(conv.Action, "_optimize_element_width_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_optimize_element_extent_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_optimize_circle_center_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_optimize_circle_radius_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_optimize_element_color_bracket", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(conv.Action, "_apply_canonical_badge_colors", staticmethod(lambda current: current))
    monkeypatch.setattr(conv.Action, "calculate_error", staticmethod(lambda *_args, **_kwargs: 22.0))

    logs = conv.Action.validate_badge_by_elements(img, params, max_rounds=4)

    assert not any("adaptive_unlock_applied" in line for line in logs)


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


def test_load_description_mapping_from_xml_reports_line_and_column_for_parse_errors(tmp_path: Path) -> None:
    xml_path = tmp_path / "broken.xml"
    xml_path.write_text(
        "<wurzelformen_export>\n"
        "  <entries>\n"
        "    <entry>\n"
        "  </entries>\n"
        "</wurzelformen_export>\n",
        encoding="utf-8",
    )

    with pytest.raises(conv.DescriptionMappingError) as exc_info:
        conv._load_description_mapping_from_xml(str(xml_path))

    exc = exc_info.value
    assert exc.span is not None
    assert exc.span.path == str(xml_path)
    assert exc.span.line == 4
    assert exc.span.column == 5
    assert "Description XML could not be parsed." in str(exc)


def test_load_description_mapping_from_csv_reports_source_span_for_short_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "broken.csv"
    csv_path.write_text(
        "Wurzelform;Beschreibung\n"
        "AC0812\n",
        encoding="utf-8",
    )

    with pytest.raises(conv.DescriptionMappingError) as exc_info:
        conv._load_description_mapping_from_csv(str(csv_path))

    exc = exc_info.value
    assert exc.span is not None
    assert exc.span.path == str(csv_path)
    assert exc.span.line == 2
    assert exc.span.column == 1
    assert "missing expected columns" in exc.message


def test_main_returns_error_for_invalid_description_xml_with_source_location(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    broken_xml = tmp_path / "broken.xml"
    broken_xml.write_text("<wurzelformen_export>\n  <entries>\n", encoding="utf-8")

    exit_code = conv.main(
        [
            str(images_dir),
            "--descriptions-path",
            str(broken_xml),
            "--start",
            "AC0001",
            "--end",
            "AC0001",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "[ERROR] Description XML could not be parsed." in captured.out
    assert f"Ort: {broken_xml}:3:1." in captured.out


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


def test_create_diff_image_uses_signed_normalized_rgb_delta() -> None:
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np

    orig = np.array(
        [
            [[10, 10, 10], [200, 200, 200]],
        ],
        dtype=np.uint8,
    )
    svg = np.array(
        [
            [[40, 40, 40], [170, 170, 170]],
        ],
        dtype=np.uint8,
    )

    diff = Action.create_diff_image(orig, svg)
    # First pixel brighter in generated image => cyan tint from dark base tone.
    assert tuple(int(v) for v in diff[0, 0]) == (52, 52, 22)
    # Second pixel darker in generated image => red tint from bright base tone.
    assert tuple(int(v) for v in diff[0, 1]) == (163, 163, 193)


def test_create_diff_image_respects_focus_mask_for_signed_delta() -> None:
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np

    orig = np.array([[[0, 0, 0], [0, 0, 0]]], dtype=np.uint8)
    svg = np.array([[[30, 30, 30], [30, 30, 30]]], dtype=np.uint8)
    focus_mask = np.array([[1, 0]], dtype=np.uint8)

    diff = Action.create_diff_image(orig, svg, focus_mask)
    assert tuple(int(v) for v in diff[0, 0]) == (43, 43, 13)
    assert tuple(int(v) for v in diff[0, 1]) == (0, 0, 0)


def test_create_diff_image_uses_mean_tone_for_zero_difference() -> None:
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np

    orig = np.array([[[255, 255, 255], [20, 20, 20]]], dtype=np.uint8)
    svg = orig.copy()

    diff = Action.create_diff_image(orig, svg)
    assert tuple(int(v) for v in diff[0, 0]) == (255, 255, 255)
    assert tuple(int(v) for v in diff[0, 1]) == (20, 20, 20)


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



def test_convert_range_stops_after_render_failure_and_writes_batch_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A render failure should be logged and stop further conversions in that run."""
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
    for name in ("AC0820_L.jpg", "AC0820_M.jpg", "AC0820_S.jpg"):
        assert cv2.imwrite(str(images_dir / name), np.full((10, 10, 3), 220, dtype=np.uint8))
    class _FixedRandom:
        def randrange(self, _limit: int) -> int:
            return 7

        def shuffle(self, _seq) -> None:
            return None
    monkeypatch.setattr(image_composite_converter, "_conversion_random", lambda: _FixedRandom())

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
    assert "AC0820_M.jpg" not in iteration_log
    assert "AC0820_S.jpg" not in iteration_log
    assert "AC0820_L.jpg" not in iteration_log

    batch_summary = (output_root / "reports" / "batch_failure_summary.csv").read_text(encoding="utf-8")
    assert "AC0820_L.jpg;render_failure;composite_iteration_render_failed" in batch_summary
    assert "AC0820_L_element_validation.log" in batch_summary


def test_update_successful_conversions_manifest_keeps_single_failed_entry(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    svg_dir = tmp_path / "svg"
    image_dir = tmp_path / "images"
    reports_dir.mkdir()
    svg_dir.mkdir()
    image_dir.mkdir()

    manifest_path = reports_dir / "successful_conversions.txt"
    manifest_path.write_text(
        "AC0001_L ; status=semantic_ok\n"
        "AC0999_L ; status=failed ; reason=old\n"
        "AC0998_L ; status=failed ; reason=older\n",
        encoding="utf-8",
    )
    (reports_dir / "batch_failure_summary.csv").write_text(
        "filename;status;reason;details;log_file\n"
        "AC0123_M.jpg;render_failure;composite_iteration_render_failed;;AC0123_M_element_validation.log\n",
        encoding="utf-8",
    )
    (reports_dir / "Iteration_Log.csv").write_text(
        "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel\n",
        encoding="utf-8-sig",
    )

    updated_path, _ = image_composite_converter.update_successful_conversions_manifest_with_metrics(
        folder_path=str(image_dir),
        svg_out_dir=str(svg_dir),
        reports_out_dir=str(reports_dir),
        manifest_path=manifest_path,
        successful_variants=["AC0001_L"],
    )

    manifest_lines = [line.strip() for line in updated_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    failed_lines = [line for line in manifest_lines if "status=failed" in line.lower()]
    assert len(failed_lines) == 1
    assert failed_lines[0].startswith("AC0123_M ; status=failed")


@pytest.mark.parametrize(
    ("variant", "expected_status"),
    [
        ("AC0800_L", "semantic_ok"),
        ("AC0800_M", "semantic_ok"),
        ("AC0820_L", "semantic_ok"),
        ("AC0835_S", "semantic_ok"),
        ("AC0837_L", "semantic_ok"),
    ],
)
def test_ac08_regression_suite_preserves_previously_good_variants(
    tmp_path: Path,
    variant: str,
    expected_status: str,
) -> None:
    """Regression-safe semantic changes must keep the already-good AC08 fixtures convertible."""
    if (
        image_composite_converter.np is None
        or image_composite_converter.cv2 is None
        or image_composite_converter.fitz is None
    ):
        pytest.skip("numpy/cv2/fitz not available in this environment")

    images_dir = Path("artifacts/images_to_convert")
    csv_path = images_dir / "Finale_Wurzelformen_V3.xml"
    if not images_dir.exists() or not csv_path.exists():
        pytest.skip("AC08 fixture inputs not available")

    img_path = images_dir / f"{variant}.jpg"
    assert img_path.exists(), f"missing regression fixture: {img_path}"

    svg_dir = tmp_path / "svgs"
    diff_dir = tmp_path / "diffs"
    reports_dir = tmp_path / "reports"

    result = image_composite_converter.run_iteration_pipeline(
        str(img_path),
        str(csv_path),
        4,
        str(svg_dir),
        str(diff_dir),
        str(reports_dir),
    )

    assert result is not None
    assert (svg_dir / f"{variant}.svg").exists()
    assert not (svg_dir / f"{variant}_failed.svg").exists()
    log_text = (reports_dir / f"{variant}_element_validation.log").read_text(encoding="utf-8")
    assert f"status={expected_status}" in log_text


def test_ac0811_l_conversion_preserves_long_bottom_stem(tmp_path: Path) -> None:
    """AC0811_L should keep a visibly long stem instead of collapsing during validation."""
    if (
        image_composite_converter.np is None
        or image_composite_converter.cv2 is None
        or image_composite_converter.fitz is None
    ):
        pytest.skip("numpy/cv2/fitz not available in this environment")

    images_dir = Path("artifacts/images_to_convert")
    csv_path = images_dir / "Finale_Wurzelformen_V3.xml"
    if not images_dir.exists() or not csv_path.exists():
        pytest.skip("AC0811 fixture inputs not available")

    output_root = tmp_path / "ac0811_l_out"
    result = image_composite_converter.convert_range(
        str(images_dir),
        str(csv_path),
        iterations=4,
        start_ref="AC0811",
        end_ref="AC0811",
        output_root=str(output_root),
    )

    assert result == str(output_root)
    svg_text = (output_root / "converted_svgs" / "AC0811_L.svg").read_text(encoding="utf-8")

    import re

    match_y = re.search(r'<rect x="[0-9.]+" y="([0-9.]+)" width="[0-9.]+" height="([0-9.]+)"', svg_text)
    assert match_y is not None
    stem_y = float(match_y.group(1))
    stem_h = float(match_y.group(2))

    assert stem_y <= 27.5
    assert stem_h >= 16.0


def test_ac0820_l_conversion_keeps_circle_diameter_above_half_image_width(tmp_path: Path) -> None:
    """AC0820_L must keep the final circle diameter strictly above half the source width."""
    if (
        image_composite_converter.np is None
        or image_composite_converter.cv2 is None
        or image_composite_converter.fitz is None
    ):
        pytest.skip("numpy/cv2/fitz not available in this environment")

    images_dir = Path("artifacts/images_to_convert")
    csv_path = images_dir / "Finale_Wurzelformen_V3.xml"
    if not images_dir.exists() or not csv_path.exists():
        pytest.skip("AC0820 fixture inputs not available")

    img_path = images_dir / "AC0820_L.jpg"
    assert img_path.exists(), f"missing regression fixture: {img_path}"

    src = image_composite_converter.cv2.imread(str(img_path))
    assert src is not None
    src_h, src_w = src.shape[:2]

    svg_dir = tmp_path / "svgs"
    diff_dir = tmp_path / "diffs"
    reports_dir = tmp_path / "reports"

    result = image_composite_converter.run_iteration_pipeline(
        str(img_path),
        str(csv_path),
        4,
        str(svg_dir),
        str(diff_dir),
        str(reports_dir),
    )

    assert result is not None
    svg_text = (svg_dir / "AC0820_L.svg").read_text(encoding="utf-8")

    import re

    circle_match = re.search(r'<circle[^>]*\sr="([0-9.]+)"', svg_text)
    assert circle_match is not None
    radius = float(circle_match.group(1))

    assert src_w == 30
    assert src_h == 30
    assert (2.0 * radius) > (float(src_w) / 2.0)


def test_ac08_semantic_anchor_variants_convert_without_failed_svg(tmp_path: Path) -> None:
    """The historical anchor failures AC0811_L and AC0812_M should now render as real SVG outputs."""
    if (
        image_composite_converter.np is None
        or image_composite_converter.cv2 is None
        or image_composite_converter.fitz is None
    ):
        pytest.skip("numpy/cv2/fitz not available in this environment")

    images_dir = Path("artifacts/images_to_convert")
    csv_path = images_dir / "Finale_Wurzelformen_V3.xml"
    if not images_dir.exists() or not csv_path.exists():
        pytest.skip("AC08 fixture inputs not available")

    output_ac0811 = tmp_path / "ac0811_out"
    result_ac0811 = image_composite_converter.convert_range(
        str(images_dir),
        str(csv_path),
        iterations=4,
        start_ref="AC0811",
        end_ref="AC0811",
        output_root=str(output_ac0811),
    )

    assert result_ac0811 == str(output_ac0811)
    assert (output_ac0811 / "converted_svgs" / "AC0811_L.svg").exists()
    assert not (output_ac0811 / "converted_svgs" / "AC0811_L_failed.svg").exists()
    log_ac0811_l = (output_ac0811 / "reports" / "AC0811_L_element_validation.log").read_text(encoding="utf-8")
    assert "status=semantic_ok" in log_ac0811_l

    output_ac0812 = tmp_path / "ac0812_out"
    result_ac0812 = image_composite_converter.convert_range(
        str(images_dir),
        str(csv_path),
        iterations=4,
        start_ref="AC0812",
        end_ref="AC0812",
        output_root=str(output_ac0812),
    )

    assert result_ac0812 == str(output_ac0812)
    assert (output_ac0812 / "converted_svgs" / "AC0812_M.svg").exists()
    assert not (output_ac0812 / "converted_svgs" / "AC0812_M_failed.svg").exists()
    log_ac0812_m = (output_ac0812 / "reports" / "AC0812_M_element_validation.log").read_text(encoding="utf-8")
    assert "status=semantic_ok" in log_ac0812_m


def test_persist_connector_length_floor_uses_template_stem_geometry() -> None:
    """Connector floors should remain anchored to the semantic template, not only to the current short fit."""
    params = {
        "stem_top": 9.0,
        "stem_bottom": 15.0,
        "template_stem_top": 7.0,
        "template_stem_bottom": 18.0,
        "stem_len_min_ratio": 0.70,
    }

    conv.Action._persist_connector_length_floor(params, "stem", default_ratio=0.65)

    assert params["stem_len_min_ratio"] == pytest.approx(0.70)
    assert params["stem_len_min"] >= ((18.0 - 7.0) * 0.70) - 1e-6


def test_write_successful_conversion_quality_report_records_delta2_totals(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reports_dir = tmp_path / "reports"
    svg_dir = tmp_path / "svg"
    image_dir = tmp_path / "images"
    reports_dir.mkdir()
    svg_dir.mkdir()
    image_dir.mkdir()

    (reports_dir / "successful_conversions.txt").write_text("AC0001_L\nAC9999_M\n", encoding="utf-8")
    (reports_dir / "Iteration_Log.csv").write_text(
        "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel\n"
        "AC0001_L.jpg;SEMANTIC;4;12.50;0.25000000\n",
        encoding="utf-8-sig",
    )
    (reports_dir / "AC0001_L_element_validation.log").write_text("status=semantic_ok\n", encoding="utf-8")
    (image_dir / "AC0001_L.jpg").write_bytes(b"fake-jpg")
    (svg_dir / "AC0001_L.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="2" height="1"/>', encoding="utf-8")

    np = conv.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    source = np.array([[[10, 10, 10], [20, 20, 20]]], dtype=np.uint8)
    rendered = np.array([[[13, 10, 10], [17, 20, 18]]], dtype=np.uint8)

    monkeypatch.setattr(conv.cv2, "imread", lambda path: source.copy() if path.endswith("AC0001_L.jpg") else None)
    monkeypatch.setattr(conv.Action, "render_svg_to_numpy", staticmethod(lambda _svg, _w, _h: rendered.copy()))

    csv_path, txt_path, rows = conv.write_successful_conversion_quality_report(
        folder_path=str(image_dir),
        svg_out_dir=str(svg_dir),
        reports_out_dir=str(reports_dir),
        successful_variants=["AC0001_L", "AC9999_M"],
    )

    assert Path(csv_path).exists()
    assert Path(txt_path).exists()
    leaderboard_csv_path = reports_dir / "successful_conversions.csv"
    assert leaderboard_csv_path.exists()
    assert [row["variant"] for row in rows] == ["AC0001_L", "AC9999_M"]
    assert rows[0]["status"] == "semantic_ok"
    assert rows[0]["best_iteration"] == "4"
    assert rows[0]["pixel_count"] == 2
    assert rows[0]["total_delta2"] == pytest.approx(22.0)
    assert rows[0]["mean_delta2"] == pytest.approx(11.0)
    assert rows[0]["std_delta2"] == pytest.approx(2.0)
    assert rows[1]["svg_found"] is False

    csv_text = Path(csv_path).read_text(encoding="utf-8")
    assert "AC0001_L;semantic_ok;1;1;1;4;12.500000;0.25000000;2;22.000000;11.000000;2.000000" in csv_text
    assert csv_text == leaderboard_csv_path.read_text(encoding="utf-8")

    manifest_text = (reports_dir / "successful_conversions.txt").read_text(encoding="utf-8")
    assert "AC0001_L ; status=semantic_ok ; best_iteration=4 ; diff_score=12.500000 ; error_per_pixel=0.25000000 ; total_delta2=22.000000 ; mean_delta2=11.000000 ; std_delta2=2.000000 ; pixel_count=2" in manifest_text
    assert "AC9999_M" in manifest_text
    summary_text = Path(txt_path).read_text(encoding="utf-8")
    assert "variants_updated=2" in summary_text


def test_write_successful_conversion_quality_report_sorts_csv_by_variant(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reports_dir = tmp_path / "reports"
    svg_dir = tmp_path / "svg"
    image_dir = tmp_path / "images"
    reports_dir.mkdir()
    svg_dir.mkdir()
    image_dir.mkdir()

    (reports_dir / "successful_conversions.txt").write_text("AC0002_L\nAC0001_L\n", encoding="utf-8")
    (reports_dir / "Iteration_Log.csv").write_text(
        "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel\n"
        "AC0002_L.jpg;SEMANTIC;7;9.50;0.12500000\n"
        "AC0001_L.jpg;SEMANTIC;4;1.50;0.02500000\n",
        encoding="utf-8-sig",
    )
    (reports_dir / "AC0002_L_element_validation.log").write_text("status=semantic_ok\n", encoding="utf-8")
    (reports_dir / "AC0001_L_element_validation.log").write_text("status=semantic_ok\n", encoding="utf-8")
    (image_dir / "AC0002_L.jpg").write_bytes(b"fake-jpg")
    (image_dir / "AC0001_L.jpg").write_bytes(b"fake-jpg")
    (svg_dir / "AC0002_L.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>', encoding="utf-8")
    (svg_dir / "AC0001_L.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>', encoding="utf-8")

    np = conv.np
    if np is None:
        pytest.skip("numpy not available in this environment")

    source = np.array([[[10, 10, 10]]], dtype=np.uint8)
    rendered = np.array([[[11, 10, 10]]], dtype=np.uint8)

    monkeypatch.setattr(conv.cv2, "imread", lambda path: source.copy() if path.endswith(("AC0001_L.jpg", "AC0002_L.jpg")) else None)
    monkeypatch.setattr(conv.Action, "render_svg_to_numpy", staticmethod(lambda _svg, _w, _h: rendered.copy()))

    csv_path, txt_path, rows = conv.write_successful_conversion_quality_report(
        folder_path=str(image_dir),
        svg_out_dir=str(svg_dir),
        reports_out_dir=str(reports_dir),
        successful_variants=["AC0002_L", "AC0001_L"],
    )

    assert [row["variant"] for row in rows] == ["AC0001_L", "AC0002_L"]
    csv_lines = Path(csv_path).read_text(encoding="utf-8").splitlines()
    assert csv_lines[1].startswith("AC0001_L;")
    assert csv_lines[2].startswith("AC0002_L;")
    summary_text = Path(txt_path).read_text(encoding="utf-8")
    assert "leaderboard_csv_path=" in summary_text


def test_kelle_constraints_require_handle_start_at_circle_center() -> None:
    with pytest.raises(ValueError, match="Griff.Anfang"):
        conv.Kelle(
            griff=conv.Griff(anfang=conv.Punkt(11, 10), ende=conv.Punkt(11, 25)),
            kreis=conv.Kreis(
                mittelpunkt=conv.Punkt(10, 10),
                radius=6,
                randbreite=2,
                rand_farbe=conv.RGBWert(90, 90, 90),
                hintergrundfarbe=conv.RGBWert(220, 220, 220),
            ),
        )


def test_kelle_to_svg_draws_handle_before_circle_and_clips() -> None:
    kelle = conv.build_oriented_kelle(
        "left",
        mittelpunkt=conv.Punkt(12, 12),
        radius=8,
        griff_laenge=16,
        randbreite=2,
        rand_farbe=conv.RGBWert(120, 120, 120),
        hintergrundfarbe=conv.RGBWert(230, 230, 230),
    )

    svg = kelle.to_svg(20, 20)

    assert 'clipPath id="canvasClip"' in svg
    assert svg.index("<line ") < svg.index("<circle ")


def test_build_oriented_kelle_supports_left_top_right_and_down() -> None:
    center = conv.Punkt(30, 30)
    common = {
        "mittelpunkt": center,
        "radius": 9,
        "griff_laenge": 14,
        "randbreite": 2,
        "rand_farbe": conv.RGBWert(130, 130, 130),
        "hintergrundfarbe": conv.RGBWert(240, 240, 240),
    }

    left = conv.build_oriented_kelle("left", **common)
    top = conv.build_oriented_kelle("top", **common)
    right = conv.build_oriented_kelle("right", **common)
    down = conv.build_oriented_kelle("down", **common)

    assert left.griff.ende.x < left.griff.anfang.x
    assert top.griff.ende.y < top.griff.anfang.y
    assert right.griff.ende.x > right.griff.anfang.x
    assert down.griff.ende.y > down.griff.anfang.y


def test_generate_conversion_overviews_creates_diff_and_svg_tiles(tmp_path: Path) -> None:
    """The overview generator should render one tile sheet for diff PNGs and one for SVG previews."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    from src.overview_tiles import generate_conversion_overviews

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2
    if np is None or cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    diff_dir = tmp_path / "diff_pngs"
    svg_dir = tmp_path / "converted_svgs"
    reports_dir = tmp_path / "reports"
    diff_dir.mkdir()
    svg_dir.mkdir()
    reports_dir.mkdir()

    assert cv2.imwrite(str(diff_dir / "AC0812_L_diff.png"), np.full((20, 20, 3), 180, dtype=np.uint8))
    (svg_dir / "AC0812_L.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">'
        '<circle cx="10" cy="10" r="8" fill="#dddddd" stroke="#777777"/></svg>',
        encoding="utf-8",
    )

    generated = generate_conversion_overviews(diff_dir, svg_dir, reports_dir)

    assert "diff" in generated
    assert "svg" in generated
    assert (reports_dir / "overview_diff_tiles.png").exists()
    assert (reports_dir / "overview_svg_tiles.png").exists()


def test_convert_range_invokes_overview_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """convert_range should call overview-tile generation after conversion output is written."""
    if image_composite_converter.np is None or image_composite_converter.cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    np = image_composite_converter.np
    cv2 = image_composite_converter.cv2
    if np is None or cv2 is None:
        pytest.skip("numpy/cv2 not available in this environment")

    images_dir = tmp_path / "images"
    output_root = tmp_path / "out"
    images_dir.mkdir()
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Wurzelform;Beschreibung\nAC0812;semantic\n", encoding="utf-8")
    assert cv2.imwrite(str(images_dir / "AC0812_L.jpg"), np.full((10, 10, 3), 220, dtype=np.uint8))

    monkeypatch.setattr(image_composite_converter, "_in_requested_range", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(image_composite_converter, "_load_quality_config", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(image_composite_converter, "_write_quality_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_harmonize_semantic_size_variants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_write_pixel_delta2_ranking", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(image_composite_converter, "_select_open_quality_cases", lambda rows, **_kwargs: [])
    monkeypatch.setattr(image_composite_converter, "_select_middle_lower_tercile", lambda _rows: [])
    monkeypatch.setattr(image_composite_converter, "_try_template_transfer", lambda **_kwargs: (None, None))

    called: dict[str, str] = {}

    def fake_overviews(diff_dir: str, svg_dir: str, reports_dir: str):
        called["diff"] = diff_dir
        called["svg"] = svg_dir
        called["reports"] = reports_dir
        return {"diff": str(Path(reports_dir) / "overview_diff_tiles.png")}

    monkeypatch.setattr(image_composite_converter, "generate_conversion_overviews", fake_overviews)

    def fake_pipeline(img_path: str, _csv_path: str, _iterations: int, svg_out: str, diff_out: str, reports_out: str, *_args, **_kwargs):
        stem = Path(img_path).stem
        Path(svg_out).mkdir(parents=True, exist_ok=True)
        Path(diff_out).mkdir(parents=True, exist_ok=True)
        Path(reports_out).mkdir(parents=True, exist_ok=True)
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
        start_ref="AC0812",
        end_ref="AC0812",
        output_root=str(output_root),
    )

    assert result == str(output_root)
    assert called["diff"] == str(output_root / "diff_pngs")
    assert called["svg"] == str(output_root / "converted_svgs")
    assert called["reports"] == str(output_root / "reports")
