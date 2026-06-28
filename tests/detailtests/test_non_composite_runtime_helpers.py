from __future__ import annotations

import numpy as np

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as non_composite_runtime_helpers


def test_structured_symbol_svg_can_fit_single_diagonal_top_left_plus() -> None:
    svg = non_composite_runtime_helpers._build_structured_symbol_svg(
        40,
        80,
        border_thickness=1.0,
        gradient_center=50.0,
        gradient_edge="#8f8f8f",
        gradient_mid="#dedede",
        diag1_width=1.4,
        diag2_width=0.0,
        plus_width=1.2,
        minus_width=0.0,
        plus_x_ratio=0.16,
        glyph_y_ratio=0.12,
        plus_half_ratio=0.08,
        minus_gap_ratio=1.8,
    )

    assert 'x1="39.5" y1="0.5" x2="0.5" y2="79.5"' in svg
    assert 'x1="0.5" y1="0.5" x2="39" y2="79"' not in svg
    assert 'x1="3.20" y1="9.60" x2="9.60" y2="9.60"' in svg
    assert svg.count('stroke="#f1f1f1"') == 2


def test_symbol_params_detect_glyph_geometry_from_raster() -> None:
    raster = np.ones((80, 40, 3), dtype=np.uint8) * 150
    raster[:, 18:22] = 210
    raster[14, 8:16] = 245
    raster[10:19, 12] = 245

    params = non_composite_runtime_helpers._derive_symbol_params_from_raster(
        width=40,
        height=80,
        perc_img=raster,
    )

    assert 0.24 <= params["plus_x_ratio"] <= 0.34
    assert 0.14 <= params["glyph_y_ratio"] <= 0.22
    assert 0.07 <= params["plus_half_ratio"] <= 0.13


def test_symbol_params_estimate_dark_glyph_color_from_top_left_raster() -> None:
    raster = np.ones((60, 30, 3), dtype=np.uint8) * 225
    raster[:, 0:2] = 185
    raster[7:9, 6:14] = 96
    raster[4:12, 9:11] = 96

    params = non_composite_runtime_helpers._derive_symbol_params_from_raster(
        width=30,
        height=60,
        perc_img=raster,
    )

    assert params["glyph_gray"] < 150.0


def test_candidate_window_can_avoid_boundary_escape_for_glyph_pose() -> None:
    candidates = non_composite_runtime_helpers._candidate_window(
        0.31,
        (-0.08, -0.04, 0.0, 0.04, 0.08),
        minimum=0.05,
        maximum=0.55,
        include_limits=False,
    )

    assert 0.05 not in candidates
    assert 0.55 not in candidates
    assert candidates == (0.23, 0.27, 0.31, 0.35, 0.39)


def test_run_non_composite_iteration_impl_manual_review_plan_b_uses_sample_svg(tmp_path) -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0VR2_M.svg").write_text("<svg><circle r='1'/></svg>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="manual_review",
        params={"mode": "manual_review", "review_reason": "Bitte prüfen"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0VR2_M",
        description="desc",
        perc_img=np.ones((64, 64, 3), dtype=np.uint8) * 180,
        img_path=str(image_dir / "AC0VR2_M.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg />",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg />",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "<circle" in content else "generated_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.5 if rendered == "sample_rendered" else 0.9,
    )

    assert result == ("AC0VR2_M", "desc", {"mode": "manual_review", "review_reason": "Bitte prüfen"}, 1, 0.5)
    assert logs[0][0] == "status=manual_review_plan_b_sample_svg"
    assert prints and "Plan B aktiv" in prints[0]
    assert artifacts == [("<svg><circle r='1'/></svg>", "sample_rendered")]

def test_run_non_composite_iteration_impl_manual_review_uses_iterative_symbol_fit() -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="manual_review",
        params={"mode": "manual_review", "review_reason": "Bitte prüfen"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0120_L",
        description="desc",
        perc_img=np.ones((64, 64, 3), dtype=np.uint8) * 180,
        img_path="input.jpg",
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg />",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg />",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: "rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, _rendered: 0.4,
    )

    assert result == ("AC0120_L", "desc", {"mode": "manual_review", "review_reason": "Bitte prüfen"}, 1, 0.4)
    assert logs and logs[0][0] == "status=manual_review_elementwise_symbol_fit"
    assert any("elementweise iterative Annäherung" in msg for msg in prints)
    assert any(line.startswith("step_border_thickness=") for line in logs[0])
    assert artifacts and "<svg" in artifacts[0][0]
def test_run_non_composite_iteration_impl_manual_review_writes_skip_log() -> None:
    logs: list[list[str]] = []
    prints: list[str] = []

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="manual_review",
        params={"mode": "manual_review", "review_reason": "Bitte prüfen"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="SE0082",
        description="desc",
        perc_img=object(),
        img_path="input.jpg",
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg />",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg />",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: None,
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda *_args, **_kwargs: None,
        calculate_error_fn=lambda *_args, **_kwargs: 0.0,
    )

    assert result is None
    assert logs == [["status=skipped_manual_review", "manual_review_reason=Bitte prüfen"]]
    assert prints and prints[-1] == "  -> Überspringe Bild: Bitte prüfen"

def test_run_non_composite_iteration_impl_manual_review_uses_gradient_stripe_plan_b() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    prints: list[str] = []

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="manual_review",
        params={"mode": "manual_review", "review_reason": "Bitte prüfen"},
        stripe_strategy={"stops": [0, 1, 2]},
        semantic_mode_visual_override=False,
        width=64,
        height=16,
        base_name="Z_203",
        description="desc",
        perc_img="target",
        img_path="input.jpg",
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg />",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: "rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, _rendered: 0.9,
    )

    assert result == ("Z_203", "desc", {"mode": "manual_review", "review_reason": "Bitte prüfen"}, 1, 0.9)
    assert logs == [["status=non_composite_gradient_stripe"]]
    assert artifacts == [("<svg gradient/>", "rendered")]
    assert prints and "Plan B aktiv" in prints[0]

def test_run_non_composite_iteration_impl_gradient_stripe_returns_iteration_tuple() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy={"stops": [0, 1, 2]},
        semantic_mode_visual_override=True,
        width=32,
        height=12,
        base_name="Z_203",
        description="desc",
        perc_img="target",
        img_path="input.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **kwargs: [
            f"status=non_composite_gradient_stripe_visual_override",
            f"stops={kwargs['strategy_stop_count']}",
        ],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: "rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda target, rendered: 1.25 if (target, rendered) == ("target", "rendered") else 99.0,
    )

    assert result == ("Z_203", "desc", {"mode": "non_composite"}, 1, 1.25)
    assert logs == [["status=non_composite_gradient_stripe_visual_override", "stops=3"]]
    assert artifacts == [("<svg gradient/>", "rendered")]

def test_run_non_composite_iteration_impl_prefers_sample_svg_when_better(tmp_path) -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0040_L.svg").write_text("<svg sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0040_L",
        description="desc",
        perc_img="target",
        img_path=str(image_dir / "AC0040_L.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.4 if rendered == "sample_rendered" else 1.1,
    )

    assert result == ("AC0040_L", "desc", {"mode": "non_composite"}, 1, 0.4)
    assert logs[-1][0] == "status=non_composite_plan_b_sample_svg_selected"
    assert prints and "Plan B Vergleich aktiv" in prints[-1]
    assert artifacts == [("<svg sample/>", "sample_rendered")]

def test_run_non_composite_iteration_impl_keeps_algorithmic_svg_when_sample_error_is_worse(tmp_path) -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0011.svg").write_text("<svg sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0011",
        description="desc",
        perc_img="target",
        img_path=str(image_dir / "AC0011.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg><image href=\"data:image/png;base64,abc\"/></svg>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 1.7 if rendered == "sample_rendered" else 1.1,
    )

    assert result == ("AC0011", "desc", {"mode": "non_composite"}, 1, 1.1)
    assert logs[0][0] == "status=non_composite_pure_svg_placeholder_vector"
    assert not any("status=non_composite_plan_b_sample_svg_selected" in line for row in logs for line in row)
    assert artifacts and artifacts[0][0].startswith("<svg")
    assert artifacts[0][1] == "baseline_rendered"

def test_run_non_composite_iteration_impl_prefers_documented_reference_sample_over_exact_alias(tmp_path) -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0010.svg").write_text("<svg reference-sample/>", encoding="utf-8")
    (samples_dir / "AC0011.svg").write_text("<svg exact-sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0011",
        description="Wie AC0010: geometrische Variante",
        perc_img="target",
        img_path=str(image_dir / "AC0011.jpg"),
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "exact_rendered" if "exact-sample" in content else "other_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 1.7 if rendered == "exact_rendered" else 1.1,
    )

    assert result == ("AC0011", "Wie AC0010: geometrische Variante", {"mode": "non_composite"}, 1, 1.1)
    assert not any("status=non_composite_plan_b_sample_svg_selected" in line for row in logs for line in row)
    assert artifacts and artifacts[0][1] == "other_rendered"

def test_run_non_composite_iteration_impl_keeps_vector_placeholder_when_non_forced_sample_render_fails(tmp_path) -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0012.svg").write_text("<svg sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0012",
        description="desc",
        perc_img="target",
        img_path=str(image_dir / "AC0012.jpg"),
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg><image href=\"data:image/png;base64,abc\"/></svg>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: None if "sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, _rendered: 1.1,
    )

    assert result == ("AC0012", "desc", {"mode": "non_composite"}, 1, 1.1)
    assert logs[0][0] == "status=non_composite_pure_svg_placeholder_vector"
    assert not any("sample_render_failed=1" in line for row in logs for line in row)
    assert artifacts and artifacts[0][1] == "baseline_rendered"


def test_run_non_composite_iteration_impl_prefers_perception_seeded_geometry_ir(monkeypatch) -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []

    def fake_seeded_ir(image, *, description: str | None = None, source: str = ""):
        assert image.shape == (20, 40, 3)
        assert description == "unbekannte Beschreibung"
        assert source == "non_composite_perception_seed"
        return [
            {
                "kind": "HorizontalRule",
                "id": "seeded_rule",
                "bbox": [0.25, 0.45, 0.5, 0.1],
                "perception_seed": {"kind": "horizontal_rule", "confidence": 0.91},
            }
        ]

    monkeypatch.setattr(
        non_composite_runtime_helpers,
        "build_perception_seeded_geometry_ir",
        fake_seeded_ir,
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=40,
        height=20,
        base_name="ACPF4",
        description="unbekannte Beschreibung",
        perc_img=np.ones((20, 40, 3), dtype=np.uint8) * 255,
        img_path="input.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg />",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: "rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, _rendered: 0.25,
    )

    assert result == ("ACPF4", "unbekannte Beschreibung", {"mode": "non_composite"}, 1, 0.25)
    assert logs[0][:3] == [
        "status=non_composite_perception_seeded_geometry_ir",
        "perception_seeded_geometry_ir=1",
        "perception_seed_count=1",
    ]
    assert 'id="seeded_rule"' in artifacts[0][0]

def test_run_non_composite_iteration_impl_vector_placeholder_has_no_embedded_image() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=40,
        height=80,
        base_name="AC0030",
        description="desc <unsafe> & marker",
        perc_img="target",
        img_path="input.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: '<svg><image href="data:image/png;base64,abc"/></svg>',
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: "rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, _rendered: 1.0,
    )

    assert result == ("AC0030", "desc <unsafe> & marker", {"mode": "non_composite"}, 1, 1.0)
    assert logs == [["status=non_composite_pure_svg_placeholder_vector"]]
    assert artifacts and artifacts[0][1] == "rendered"
    svg_content = artifacts[0][0].lower()
    assert "<image" not in svg_content
    assert "data:image/" not in svg_content
    assert "&lt;unsafe&gt;" in svg_content
    assert "&amp; marker" in svg_content

def test_run_non_composite_iteration_impl_uses_same_root_sample_svg_when_exact_missing(tmp_path) -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0212_L.svg").write_text("<svg same-root-sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0212_S",
        description="desc",
        perc_img="target",
        img_path=str(image_dir / "AC0212_S.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "same-root-sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.3 if rendered == "sample_rendered" else 1.2,
    )

    assert result == ("AC0212_S", "desc", {"mode": "non_composite"}, 1, 0.3)
    assert logs[-1][0] == "status=non_composite_plan_b_sample_svg_selected"
    assert "sample_svg_path=" in logs[-1][1] and "AC0212_L.svg" in logs[-1][1]
    assert prints and "Plan B Vergleich aktiv" in prints[-1]
    assert artifacts == [("<svg same-root-sample/>", "sample_rendered")]

def test_run_non_composite_iteration_impl_uses_root_sample_svg_without_size_suffix(tmp_path) -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0010_L.svg").write_text("<svg own-nosize-sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0010",
        description="desc",
        perc_img="target",
        img_path=str(image_dir / "AC0010.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "own-nosize-sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.35 if rendered == "sample_rendered" else 1.4,
    )

    assert result == ("AC0010", "desc", {"mode": "non_composite"}, 1, 0.35)
    assert logs[-1][0] == "status=non_composite_plan_b_sample_svg_selected"
    assert "sample_svg_path=" in logs[-1][1] and "AC0010_L.svg" in logs[-1][1]
    assert prints and "Plan B Vergleich aktiv" in prints[-1]
    assert artifacts == [("<svg own-nosize-sample/>", "sample_rendered")]

def test_run_non_composite_iteration_impl_uses_plain_root_sample_when_size_variant_missing(tmp_path) -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0010.svg").write_text("<svg plain-root-sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0010_S",
        description="desc",
        perc_img="target",
        img_path=str(image_dir / "AC0010_S.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "plain-root-sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.25 if rendered == "sample_rendered" else 1.5,
    )

    assert result == ("AC0010_S", "desc", {"mode": "non_composite"}, 1, 0.25)
    assert logs[-1][0] == "status=non_composite_plan_b_sample_svg_selected"
    assert "sample_svg_path=" in logs[-1][1] and "AC0010.svg" in logs[-1][1]
    assert prints and "Plan B Vergleich aktiv" in prints[-1]
    assert artifacts == [("<svg plain-root-sample/>", "sample_rendered")]

def test_run_non_composite_iteration_impl_uses_own_size_sample_for_base_without_size_suffix(tmp_path) -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0100_L.svg").write_text("<svg own-nosize-sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0100",
        description="desc",
        perc_img="target",
        img_path=str(image_dir / "AC0100.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "own-nosize-sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.31 if rendered == "sample_rendered" else 1.5,
    )

    assert result == ("AC0100", "desc", {"mode": "non_composite"}, 1, 0.31)
    assert logs[-1][0] == "status=non_composite_plan_b_sample_svg_selected"
    assert "sample_svg_path=" in logs[-1][1] and "AC0100_L.svg" in logs[-1][1]
    assert prints and "Plan B Vergleich aktiv" in prints[-1]
    assert artifacts == [("<svg own-nosize-sample/>", "sample_rendered")]

def test_try_load_sample_svg_does_not_fallback_to_standalone_size_suffix_file(tmp_path) -> None:
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "S.svg").write_text("<svg unrelated-size-only-sample/>", encoding="utf-8")

    sample = non_composite_runtime_helpers._try_load_sample_svg(
        img_path=str(image_dir / "AC7777_S.jpg"),
        base_name="AC7777_S",
    )

    assert sample is None

def test_try_load_sample_svg_ignores_repo_samples_for_bare_img_path(monkeypatch) -> None:
    monkeypatch.delenv("IMAGE_CONVERTER_SAMPLE_SVG_DIRS", raising=False)

    sample = non_composite_runtime_helpers._try_load_sample_svg(
        img_path="input.jpg",
        base_name="AC0120_L",
    )

    assert sample is None

def test_run_non_composite_iteration_impl_rejects_sample_without_sufficient_gain(tmp_path) -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0130_L.svg").write_text("<svg sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0130_L",
        description="desc",
        perc_img="target",
        img_path=str(image_dir / "AC0130_L.jpg"),
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 160.0 if rendered == "sample_rendered" else 188.0,
    )

    assert result == ("AC0130_L", "desc", {"mode": "non_composite"}, 1, 188.0)
    assert not any("status=non_composite_plan_b_sample_svg_selected" in line for row in logs for line in row)
    assert artifacts and artifacts[0][1] == "baseline_rendered"

def test_extract_reference_family_from_description() -> None:
    ref = non_composite_runtime_helpers._extract_reference_family_from_description(
        "Wie AC0030, jedoch mit einem zusätzlichen Zeichen."
    )
    assert ref == "AC0030"

def test_run_non_composite_iteration_impl_does_not_force_sample_for_known_problem_variant(tmp_path) -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0120_L.svg").write_text("<svg sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0120_L",
        description="desc",
        perc_img="target",
        img_path=str(image_dir / "AC0120_L.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 200.0 if rendered == "sample_rendered" else 188.0,
    )

    assert result == ("AC0120_L", "desc", {"mode": "non_composite"}, 1, 188.0)
    assert not any("status=non_composite_plan_b_sample_svg_selected" in line for row in logs for line in row)
    assert artifacts and artifacts[0][1] == "baseline_rendered"

def test_try_load_sample_svg_prefers_reference_family_from_description(tmp_path) -> None:
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0030.svg").write_text("<svg ref/>", encoding="utf-8")
    (samples_dir / "AC0120_L.svg").write_text("<svg direct/>", encoding="utf-8")

    sample = non_composite_runtime_helpers._try_load_sample_svg(
        img_path=str(image_dir / "AC0120_L.jpg"),
        base_name="AC0120_L",
        description="Wie AC0030, jedoch mit extra Plus-Minus-Zeichen.",
    )

    assert sample is not None
    sample_path, sample_content = sample
    assert sample_path.endswith("AC0030.svg")
    assert sample_content == "<svg ref/>"


def test_try_load_sample_svg_prefers_ac0100_documented_reference_over_exact_family(tmp_path) -> None:
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0010.svg").write_text("<svg reference/>", encoding="utf-8")
    (samples_dir / "AC0100_L.svg").write_text("<svg exact-family/>", encoding="utf-8")

    sample = non_composite_runtime_helpers._try_load_sample_svg(
        img_path=str(image_dir / "AC0100_M.jpg"),
        base_name="AC0100_M",
        description="Wie AC0010: Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, horizontaler Farbverlauf dunkel–hell–dunkel sowie graue Diagonale von oben rechts nach unten links.",
    )

    assert sample is not None
    sample_path, sample_content = sample
    assert sample_path.endswith("AC0010.svg")
    assert sample_content == "<svg reference/>"


def test_run_non_composite_iteration_impl_ac0100_size_variant_keeps_algorithmic_result_when_sample_error_is_higher(tmp_path) -> None:
    logs: list[list[str]] = []
    prints: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0100_L.svg").write_text("<svg sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0100_M",
        description="Wie AC0010: Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, horizontaler Farbverlauf dunkel–hell–dunkel sowie graue Diagonale von oben rechts nach unten links.",
        perc_img="target",
        img_path=str(image_dir / "AC0100_M.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: "sample_rendered" if "sample" in content else "baseline_rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 200.0 if rendered == "sample_rendered" else 100.0,
    )

    assert result == ("AC0100_M", "Wie AC0010: Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, horizontaler Farbverlauf dunkel–hell–dunkel sowie graue Diagonale von oben rechts nach unten links.", {"mode": "non_composite"}, 1, 100.0)
    assert logs[0][0] == "status=non_composite_description_geometry_ir"
    assert any("geometry_ir_element_1=HorizontalGradient" in line for line in logs[0])
    assert any("geometry_ir_element_3=DiagonalBand" in line for line in logs[0])
    assert not any("status=non_composite_plan_b_sample_svg_selected" in line for row in logs for line in row)
    assert artifacts and artifacts[0][0].startswith("<svg")
    assert artifacts[0][1] == "baseline_rendered"


def test_run_non_composite_iteration_impl_ac0100_keeps_description_algorithm_even_when_sample_error_is_lower(tmp_path) -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0100_L.svg").write_text("<svg sample/>", encoding="utf-8")

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0100_S",
        description=(
            "Wie AC0010: Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, "
            "horizontaler Farbverlauf dunkel–hell–dunkel sowie graue Diagonale von oben rechts nach unten links."
        ),
        perc_img="target",
        img_path=str(image_dir / "AC0100_S.jpg"),
        print_fn=lambda _message: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: (
            "sample_rendered" if "sample" in content else "algorithm_rendered"
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 10.0 if rendered == "sample_rendered" else 100.0,
    )

    assert result == (
        "AC0100_S",
        "Wie AC0010: Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, "
        "horizontaler Farbverlauf dunkel–hell–dunkel sowie graue Diagonale von oben rechts nach unten links.",
        {"mode": "non_composite"},
        1,
        100.0,
    )
    assert logs[0][0] in {"status=non_composite_description_geometry_ir", "status=non_composite_elementwise_symbol_fit"}
    assert not any("status=non_composite_plan_b_sample_svg_selected" in line for row in logs for line in row)
    assert artifacts and artifacts[0][1] == "algorithm_rendered"


def test_description_driven_symbol_algorithm_skips_sample_svg_lookup_for_ac0100_like_variants(tmp_path) -> None:
    logs: list[list[str]] = []
    rendered_inputs: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "AC0010.svg").write_text("<svg sample/>", encoding="utf-8")

    description = (
        "Wie AC0010: Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, "
        "horizontaler Farbverlauf dunkel–hell–dunkel sowie graue Diagonale von oben rechts nach unten links."
    )

    def _render(content, *_args, **_kwargs):
        rendered_inputs.append(content)
        return "sample_rendered" if "sample" in content else "algorithm_rendered"

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="AC0100_S",
        description=description,
        perc_img="target",
        img_path=str(image_dir / "AC0100_S.jpg"),
        print_fn=lambda _message: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=_render,
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 1.0 if rendered == "sample_rendered" else 100.0,
    )

    assert result == ("AC0100_S", description, {"mode": "non_composite"}, 1, 100.0)
    assert non_composite_runtime_helpers._has_description_driven_symbol_algorithm(description)
    assert any("description_driven_algorithm_available=1" in line for row in logs for line in row)
    assert any("sample_svg_lookup=skipped_description_driven_algorithm" in line for row in logs for line in row)
    assert all("sample" not in content for content in rendered_inputs)
    assert not any("status=non_composite_plan_b_sample_svg_selected" in line for row in logs for line in row)
    assert artifacts and artifacts[0][1] == "algorithm_rendered"


def test_description_driven_symbol_algorithm_skips_samples_for_all_ac0100_sizes(tmp_path) -> None:
    logs: list[list[str]] = []
    rendered_inputs: list[str] = []
    artifacts: list[tuple[str, object]] = []
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    for sample_name in ("AC0010", "AC0100_L", "AC0100_M", "AC0100_S"):
        (samples_dir / f"{sample_name}.svg").write_text("<svg sample/>", encoding="utf-8")

    description = (
        "Wie AC0010: Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, "
        "horizontaler Farbverlauf dunkel–hell–dunkel sowie graue Diagonale von oben rechts nach unten links."
    )

    def _render(content, *_args, **_kwargs):
        rendered_inputs.append(content)
        return "sample_rendered" if "sample" in content else "algorithm_rendered"

    for base_name in ("AC0100", "AC0100_L", "AC0100_M", "AC0100_S", "NEUTRAL_4711"):
        result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
            mode="non_composite",
            params={"mode": "non_composite", "variant_name": base_name},
            stripe_strategy=None,
            semantic_mode_visual_override=False,
            width=64,
            height=64,
            base_name=base_name,
            description=description,
            perc_img="target",
            img_path=str(image_dir / f"{base_name}.jpg"),
            print_fn=lambda _message: None,
            render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
            build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
            build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
            write_validation_log_fn=logs.append,
            render_svg_to_numpy_fn=_render,
            record_render_failure_fn=lambda *args, **kwargs: None,
            write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
            calculate_error_fn=lambda _target, rendered: 1.0 if rendered == "sample_rendered" else 100.0,
        )

        assert result == (base_name, description, {"mode": "non_composite", "variant_name": base_name}, 1, 100.0)

    assert non_composite_runtime_helpers._has_description_driven_symbol_algorithm(description)
    assert any("description_driven_algorithm_available=1" in line for row in logs for line in row)
    assert any("sample_svg_lookup=skipped_description_driven_algorithm" in line for row in logs for line in row)
    assert all("sample" not in content for content in rendered_inputs)
    assert not any("status=non_composite_plan_b_sample_svg_selected" in line for row in logs for line in row)
    assert artifacts and all(rendered == "algorithm_rendered" for _svg, rendered in artifacts)


def test_reference_derived_heat_exchanger_geometry_ir_does_not_override_better_elementwise_fit() -> None:
    geometry_ir = [
        {"kind": "HorizontalGradient"},
        {"kind": "RectBorder"},
        {"kind": "DiagonalBand"},
        {"kind": "PlusGlyph"},
        {"kind": "MinusGlyph"},
    ]

    assert non_composite_runtime_helpers._is_description_heat_exchanger_geometry(geometry_ir)
    assert not non_composite_runtime_helpers._prefer_description_geometry_candidate(
        geometry_ir,
        description="Wie AC0010: Heizelement mit horizontalem Farbverlauf und Diagonale.",
    )


def test_canonical_heat_exchanger_geometry_ir_prefers_description_contract() -> None:
    geometry_ir = [
        {"kind": "HorizontalGradient"},
        {"kind": "RectBorder"},
        {"kind": "DiagonalBand"},
        {"kind": "PlusGlyph"},
        {"kind": "MinusGlyph"},
    ]

    assert non_composite_runtime_helpers._prefer_description_geometry_candidate(
        geometry_ir,
        description="Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, Farbverlauf horizontal dunkel-hell-dunkel graue Diagonale oben rechts nach unten links",
    )


def test_semantic_geometry_ir_still_prefers_description_shape() -> None:
    geometry_ir = [{"kind": "TopKelleThreeWayValveGlyph"}]

    assert non_composite_runtime_helpers._prefer_description_geometry_candidate(geometry_ir, description="Wie AC0224")

def test_try_load_sample_svg_auto_converts_inkscape_file(tmp_path) -> None:
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    sample_path = samples_dir / "AC0120_L.svg"
    sample_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" inkscape:version="1.3"><inkscape:label/>\n<rect width="5" height="5"/></svg>',
        encoding="utf-8",
    )

    sample = non_composite_runtime_helpers._try_load_sample_svg(
        img_path=str(image_dir / "AC0120_L.jpg"),
        base_name="AC0120_L",
    )

    assert sample is not None
    _sample_path, sample_content = sample
    assert "inkscape:" not in sample_content
    persisted = sample_path.read_text(encoding="utf-8")
    assert "inkscape:" not in persisted

def test_try_load_sample_svg_does_not_rewrite_non_inkscape_svg(tmp_path) -> None:
    image_dir = tmp_path / "images"
    samples_dir = image_dir / "samples"
    samples_dir.mkdir(parents=True)
    sample_path = samples_dir / "AC0120_L.svg"
    original = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="5" height="5"/></svg>'
    sample_path.write_text(original, encoding="utf-8")

    sample = non_composite_runtime_helpers._try_load_sample_svg(
        img_path=str(image_dir / "AC0120_L.jpg"),
        base_name="AC0120_L",
    )

    assert sample is not None
    assert sample_path.read_text(encoding="utf-8") == original

def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0150_like_shape() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        "Graues Rechteck hochkant, graue Umrandung, drei graue horizontale Linien, "
        "Farbverlauf dunkel-hell-dunkel, Graue Linien Oben-Mitte nach Rechts-Mitte nach Unten-Mitte"
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=60,
        height=100,
        base_name="AC0150_L",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0150_L.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: "geometry_rendered" if "horizontal_rule_set" in content else None
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.42 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0150_L", description, {"mode": "non_composite"}, 1, 0.42)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=4"]
    assert "horizontal_rule_set" in artifacts[0][0]
    assert "right_side_orthogonal_line" in artifacts[0][0]

def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0160_like_shape() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        'Differenzdruckmessung oben kleines graues Rechteck mit "dp" geschrieben, '
        'vor halbem Rechteck mit doppelten grauen Rand'
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=400,
        height=400,
        base_name="AC0160_L",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0160_L.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: "geometry_rendered" if "dp_label_text" in content else None
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.16 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0160_L", description, {"mode": "non_composite"}, 1, 0.16)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=3"]
    assert "half_double_rect_outer" in artifacts[0][0]
    assert "dp_label_text" in artifacts[0][0]

def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0201_compressor() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = "Kompressor grau nach oben"

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=50,
        height=50,
        base_name="AC0201_2",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0201_2.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: "geometry_rendered" if "upward_compressor_left_line" in content else None
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.11 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0201_2", description, {"mode": "non_composite"}, 1, 0.11)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=2"]
    assert "compressor_circle" in artifacts[0][0]
    assert "upward_compressor_right_line" in artifacts[0][0]

def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0202_compressor() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = "Kompressor grau nach rechts"

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=50,
        height=50,
        base_name="AC0202_2",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0202_2.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "rightward_compressor_upper_line" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.12 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0202_2", description, {"mode": "non_composite"}, 1, 0.12)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=2"]
    assert "compressor_circle" in artifacts[0][0]
    assert "rightward_compressor_lower_line" in artifacts[0][0]

def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0203_mirrored_compressor() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = "Wie AC0202: Kompressor grau nach rechts. Geometrische Variante: Hauptdiagonal gespiegelt."

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=50,
        height=50,
        base_name="AC0203_1",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0203_1.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "mirrored_compressor_left_line" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.13 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0203_1", description, {"mode": "non_composite"}, 1, 0.13)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=2"]
    assert "compressor_circle" in artifacts[0][0]
    assert "mirrored_compressor_right_line" in artifacts[0][0]


def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0204_identical_reference() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = "Wie AC0201: Kompressor grau nach oben. Geometrische Variante: identisch zur Referenz."

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=25,
        height=20,
        base_name="AC0204_S_sia",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0204_S_sia.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "upward_compressor_left_line" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.14 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0204_S_sia", description, {"mode": "non_composite"}, 1, 0.14)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=2"]
    assert "compressor_circle" in artifacts[0][0]
    assert "upward_compressor_right_line" in artifacts[0][0]


def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0211_typo_upward_compressor() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = "Kopressor grau nach oben"

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=20,
        height=25,
        base_name="AC0211_S",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0211_S.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "upward_compressor_right_line" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.15 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0211_S", description, {"mode": "non_composite"}, 1, 0.15)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=2"]
    assert "compressor_circle" in artifacts[0][0]
    assert "upward_compressor_left_line" in artifacts[0][0]


def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0222_grey_background_upward_compressor() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = "Kompressor grauer Hintergrund nach oben."

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=30,
        height=20,
        base_name="AC0222_S",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0222_S.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered"
                if "upward_compressor_left_line" in content and "#d8d8d8" in content and "#666666" in content
                else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.16 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0222_S", description, {"mode": "non_composite"}, 1, 0.16)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=2"]
    assert "compressor_circle" in artifacts[0][0]
    assert "upward_compressor_right_line" in artifacts[0][0]


def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0221_top_kelle_three_way_valve() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        'Wie AC0231, jedoch ohne "M" in der Kelle oben. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=20,
        height=30,
        base_name="AC0221_S",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0221_S.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "top_kelle_three_way_valve_circle" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.19 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0221_S", description, {"mode": "non_composite"}, 1, 0.19)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=1"]
    assert "top_kelle_three_way_valve_body_1" in artifacts[0][0]
    assert "top_kelle_three_way_valve_label" not in artifacts[0][0]


def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0232_left_rotated_m_top_kelle_three_way_valve() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        'Wie AC0231: 3-Weg Ventil ähnlich AC0211, um 90° im Uhrzeigersinn gedreht, '
        '"M" wird immer noch senkrecht geschrieben. Noch ein 3. spitzes Dreieck unten. '
        'Wieder Farbwechsel von Dunkelgrau nach hellgrau (von links unten nach rechts oben). '
        'Geometrische Variante: 90° nach links gedreht. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=30,
        height=20,
        base_name="AC0232_S",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0232_S.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "left_rotated_top_kelle_three_way_valve_label" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.21 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0232_S", description, {"mode": "non_composite"}, 1, 0.21)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=1"]
    assert "left_rotated_top_kelle_three_way_valve_body_1" in artifacts[0][0]
    assert "left_rotated_top_kelle_three_way_valve_label" in artifacts[0][0]


def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0233_180_rotated_m_top_kelle_three_way_valve() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        'Wie AC0231: 3-Weg Ventil ähnlich AC0211, um 90° im Uhrzeigersinn gedreht, '
        '"M" wird immer noch senkrecht geschrieben. Noch ein 3. spitzes Dreieck unten. '
        'Wieder Farbwechsel von Dunkelgrau nach hellgrau (von links unten nach rechts oben). '
        'Geometrische Variante: 180° gedreht.'
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=60,
        height=40,
        base_name="AC0233_S",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0233_S.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "rotated_180_top_kelle_three_way_valve_label" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.21 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0233_S", description, {"mode": "non_composite"}, 1, 0.21)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=1"]
    assert "rotated_180_top_kelle_three_way_valve_body_1" in artifacts[0][0]
    assert "rotated_180_top_kelle_three_way_valve_label" in artifacts[0][0]

def test_ac0224_sia_variant_restores_compact_crossed_square_handle_profile() -> None:
    geometry_ir = [
        {
            "kind": "RightRotatedTopKelleThreeWayValveGlyph",
            "circle": [0.215, 0.500, 0.295],
            "connector": [[0.412, 0.500], [0.610, 0.500]],
        }
    ]

    regular = non_composite_runtime_helpers._apply_image_variant_geometry(
        [dict(element) for element in geometry_ir], base_name="AC0224_L"
    )
    sia = non_composite_runtime_helpers._apply_image_variant_geometry(
        [
            {
                **element,
                "circle": list(element["circle"]),
                "connector": [list(point) for point in element["connector"]],
            }
            for element in geometry_ir
        ],
        base_name="AC0224_L_sia",
    )

    assert regular[0]["circle"] == [0.215, 0.500, 0.295]
    assert "handle_shape" not in regular[0]
    assert sia[0]["handle_shape"] == "crossed_square"
    assert sia[0]["circle"] == [0.235, 0.500, 0.225]
    assert sia[0]["connector"] == [[0.450, 0.500], [0.610, 0.500]]


def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0224_right_rotated_top_kelle_three_way_valve() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        'Wie AC0221: Wie AC0231, jedoch ohne "M" in der Kelle oben. '
        'Geometrische Variante: 90° nach rechts gedreht. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=30,
        height=20,
        base_name="AC0224_S",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0224_S.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "right_rotated_top_kelle_three_way_valve_circle" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.20 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0224_S", description, {"mode": "non_composite"}, 1, 0.20)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=1"]
    assert "right_rotated_top_kelle_three_way_valve_body_1" in artifacts[0][0]
    assert "right_rotated_top_kelle_three_way_valve_label" not in artifacts[0][0]

def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0212_vertical_two_way_valve_motor() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        '2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=65,
        height=50,
        base_name="AC0212_L",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0212_L.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "vertical_two_way_valve_motor_circle" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.16 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0212_L", description, {"mode": "non_composite"}, 1, 0.16)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=1"]
    assert "vertical_two_way_valve_motor_body" in artifacts[0][0]
    assert "vertical_two_way_valve_motor_label" in artifacts[0][0]


def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0213_left_rotated_two_way_valve_motor() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        'Wie AC0212: 2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Geometrische Variante: 90° nach links gedreht. Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=50,
        height=65,
        base_name="AC0213_L",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0213_L.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "left_rotated_two_way_valve_motor_circle" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.17 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0213_L", description, {"mode": "non_composite"}, 1, 0.17)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=1"]
    assert "left_rotated_two_way_valve_motor_body" in artifacts[0][0]
    assert "left_rotated_two_way_valve_motor_label" in artifacts[0][0]

def test_run_non_composite_iteration_impl_uses_description_geometry_ir_for_ac0214_180_rotated_two_way_valve_motor() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        'Wie AC0212: 2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Geometrische Variante: 180° gedreht. Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=65,
        height=50,
        base_name="AC0214_S",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0214_S.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=(
            lambda content, *_args, **_kwargs: (
                "geometry_rendered" if "rotated_180_two_way_valve_motor_circle" in content else None
            )
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 0.18 if rendered == "geometry_rendered" else 99.0,
    )

    assert result == ("AC0214_S", description, {"mode": "non_composite"}, 1, 0.18)
    assert logs[-1][:2] == ["status=non_composite_description_geometry_ir", "geometry_ir_element_count=1"]
    assert "rotated_180_two_way_valve_motor_body" in artifacts[0][0]
    assert "rotated_180_two_way_valve_motor_label" in artifacts[0][0]


def test_ac0224_sia_prefers_semantic_geometry_and_uses_crossed_square(monkeypatch) -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        'Wie AC0221: Wie AC0231, jedoch ohne "M" in der Kelle oben. '
        'Geometrische Variante: 90° nach rechts gedreht. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )
    monkeypatch.setattr(
        non_composite_runtime_helpers,
        "_fit_symbol_element_by_element",
        lambda **_kwargs: (
            1.0,
            "<svg id='generic-pixel-fit'/>",
            "generic_rendered",
            {},
            [],
        ),
    )

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=45,
        height=30,
        base_name="AC0224_M_sia",
        description=description,
        perc_img="target",
        img_path="/tmp/no-sample/AC0224_M_sia.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=gradient"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: (
            "geometry_rendered"
            if "right_rotated_top_kelle_three_way_valve_square_cross" in content
            else None
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 40.0 if rendered == "geometry_rendered" else 1.0,
    )

    assert result == ("AC0224_M_sia", description, {"mode": "non_composite"}, 1, 40.0)
    assert logs[-1][0] == "status=non_composite_description_geometry_ir"
    assert "non_composite_selection=semantic_description_geometry" in logs[-1]
    assert "geometry_ir_raster_registration=1" not in logs[-1]
    assert 'id="right_rotated_top_kelle_three_way_valve_square"' in artifacts[0][0]
    assert 'id="right_rotated_top_kelle_three_way_valve_circle"' not in artifacts[0][0]



def test_ac0010_allows_much_better_algorithmic_raster_fit_over_generic_description(monkeypatch) -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        "Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, "
        "Farbverlauf horizontal dunkel-hell-dunkel graue Diagonale oben rechts nach unten links"
    )
    monkeypatch.setattr(
        non_composite_runtime_helpers,
        "_fit_symbol_element_by_element",
        lambda **_kwargs: (
            1.0,
            "<svg id='generic-stripe-pixel-fit'><rect/><rect/></svg>",
            "generic_rendered",
            {},
            [],
        ),
    )

    target = type("RasterStub", (), {"shape": (80, 40, 3)})()

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=40,
        height=80,
        base_name="AC0010",
        description=description,
        perc_img=target,
        img_path="/tmp/no-sample/AC0010.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=gradient"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda content, *_args, **_kwargs: (
            "geometry_rendered"
            if 'fill="url(#geometry-ir-horizontal-gradient)"' in content
            else "generic_rendered"
        ),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 40.0 if rendered == "geometry_rendered" else 1.0,
        image_variant_name="AC0010",
    )

    assert result == ("AC0010", description, {"mode": "non_composite"}, 1, 1.0)
    assert logs[-1][0] == "status=non_composite_elementwise_symbol_fit"
    assert "non_composite_selection=raster_fit_overrides_poor_description_geometry" in logs[-1]
    assert artifacts and artifacts[0][1] == "generic_rendered"
    assert "generic-stripe-pixel-fit" in artifacts[0][0]

def test_symbol_fit_keeps_description_declared_top_left_glyph_in_top_region(monkeypatch) -> None:
    initial = {
        "border_thickness": 1.0,
        "gradient_center": 50.0,
        "gradient_edge": "#808080",
        "gradient_mid": "#e0e0e0",
        "diag1_width": 1.4,
        "diag2_width": 0.0,
        "plus_width": 1.2,
        "minus_width": 0.0,
        "plus_x_ratio": 0.30,
        "glyph_y_ratio": 0.45,
        "plus_half_ratio": 0.08,
        "minus_gap_ratio": 1.8,
        "glyph_gray": 100.0,
        "diag_gray": 130.0,
        "border_gray": 150.0,
    }
    monkeypatch.setattr(
        non_composite_runtime_helpers,
        "_derive_symbol_params_from_raster",
        lambda **_kwargs: dict(initial),
    )

    def render(svg: str, _width: int, height: int):
        import re

        matches = re.findall(r'<line x1="[^"]+" y1="([0-9.]+)" x2="[^"]+" y2="([0-9.]+)"', svg)
        horizontal_y = next(float(y1) for y1, y2 in matches if y1 == y2)
        return np.full((height, 20, 3), horizontal_y / height * 255.0, dtype=np.float32)

    target = np.full((60, 20, 3), 0.15 * 255.0, dtype=np.float32)
    result = non_composite_runtime_helpers._fit_symbol_element_by_element(
        width=20,
        height=60,
        description="Plus-Zeichen oben links auf einem grauen Rechteck",
        perc_img=target,
        render_svg_to_numpy_fn=render,
        calculate_error_fn=lambda expected, actual: float(np.mean(np.abs(expected - actual))),
    )

    assert result is not None
    assert 0.05 <= result[3]["glyph_y_ratio"] <= 0.30
    assert result[3]["glyph_y_ratio"] == 0.15

    unconstrained_target = np.full((60, 20, 3), 0.45 * 255.0, dtype=np.float32)
    unconstrained = non_composite_runtime_helpers._fit_symbol_element_by_element(
        width=20,
        height=60,
        description="Plus-Zeichen auf einem grauen Rechteck",
        perc_img=unconstrained_target,
        render_svg_to_numpy_fn=render,
        calculate_error_fn=lambda expected, actual: float(np.mean(np.abs(expected - actual))),
    )

    assert unconstrained is not None
    assert unconstrained[3]["glyph_y_ratio"] == 0.45


def test_symbol_fit_honors_declared_diagonal_and_center_dot_without_inventing_glyphs() -> None:
    target = np.zeros((40, 20, 3), dtype=np.uint8)

    result = non_composite_runtime_helpers._fit_symbol_element_by_element(
        width=20,
        height=40,
        description=(
            "Rechteck hochkant mit Diagonale von unten links nach oben rechts, "
            "in der Mitte ein dunkelgrauer Punkt und Farbverlauf."
        ),
        perc_img=target,
        render_svg_to_numpy_fn=lambda svg, *_args: np.zeros_like(target),
        calculate_error_fn=lambda *_args: 0.0,
    )

    assert result is not None
    svg = result[1]
    params = result[3]
    assert params["diag1_width"] > 0
    assert params["diag2_width"] == 0
    assert params["center_dot_radius"] > 0
    assert params["plus_width"] == 0
    assert params["minus_width"] == 0
    assert svg.count("<line") == 1
    assert svg.count("<circle") == 1


def test_symbol_fit_renders_description_declared_right_chevron_without_inventing_diagonals() -> None:
    target = np.zeros((60, 30, 3), dtype=np.uint8)

    result = non_composite_runtime_helpers._fit_symbol_element_by_element(
        width=30,
        height=60,
        description=(
            "Graues Rechteck hochkant, drei graue horizontale Linien, "
            "graue Linien Oben-Mitte nach Rechts-Mitte nach Unten-Mitte"
        ),
        perc_img=target,
        render_svg_to_numpy_fn=lambda svg, *_args: np.zeros_like(target),
        calculate_error_fn=lambda *_args: 0.0,
    )

    assert result is not None
    svg = result[1]
    params = result[3]
    assert params["chevron_width"] > 0
    assert params["diag1_width"] == 0
    assert params["diag2_width"] == 0
    assert params["chevron_peak_x_ratio"] >= 0.88
    assert svg.count("<path") == 1
    assert svg.count("<line") == 0


def test_symbol_fit_rotates_declared_diagonal_for_quarter_turn_variant() -> None:
    import re

    target = np.zeros((30, 60, 3), dtype=np.uint8)

    result = non_composite_runtime_helpers._fit_symbol_element_by_element(
        width=60,
        height=30,
        description=(
            "Rechteck hochkant mit Diagonale von unten links nach oben rechts, "
            "in der Mitte ein dunkelgrauer Punkt. Geometrische Variante: "
            "90° nach rechts gedreht."
        ),
        perc_img=target,
        render_svg_to_numpy_fn=lambda svg, *_args: np.zeros_like(target),
        calculate_error_fn=lambda *_args: 0.0,
    )

    assert result is not None
    svg = result[1]
    params = result[3]
    assert params["diag1_width"] == 0
    assert params["diag2_width"] > 0
    line_match = re.search(
        r'<line x1="([0-9.]+)" y1="([0-9.]+)" x2="([0-9.]+)" y2="([0-9.]+)"',
        svg,
    )
    assert line_match is not None
    x1, y1, x2, y2 = map(float, line_match.groups())
    assert x1 < x2
    assert y1 < y2
    assert svg.count("<line") == 1
    assert svg.count("<circle") == 1


def test_symbol_raster_estimation_ignores_bright_frame_for_gradient_midpoint() -> None:
    raster = np.zeros((80, 40, 3), dtype=np.uint8)
    raster[:, :] = (90, 190, 70)  # OpenCV BGR -> saturated green SVG background.
    raster[:, 14:26] = (90, 205, 75)
    raster[:, :2] = 255
    raster[:, -2:] = 255
    raster[:2, :] = 255
    raster[-2:, :] = 255

    params = non_composite_runtime_helpers._derive_symbol_params_from_raster(
        width=40,
        height=80,
        perc_img=raster,
    )

    assert params["gradient_mid"] == "#4bcd5a"
    assert params["gradient_mid"] != "#ffffff"


def test_symbol_raster_estimation_preserves_bgr_source_colors_for_svg() -> None:
    raster = np.zeros((12, 12, 3), dtype=np.uint8)
    raster[:, :] = (70, 40, 230)  # OpenCV BGR -> SVG RGB #e62846.
    raster[:, 5:7] = (65, 70, 242)

    params = non_composite_runtime_helpers._derive_symbol_params_from_raster(
        width=12,
        height=12,
        perc_img=raster,
    )

    assert params["gradient_edge"] == "#e62846"
    assert params["gradient_mid"] == "#f24641"


def test_description_geometry_candidate_yields_to_much_better_algorithmic_raster_fit() -> None:
    candidates = []
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []
    description = (
        "Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, "
        "Farbverlauf horizontal dunkel-hell-dunkel graue Diagonale oben rechts nach unten links"
    )

    def _render(content, *_args, **_kwargs):
        candidates.append(content)
        if "geometry-ir-horizontal-gradient" in content:
            return "description_rendered"
        return "structured_rendered"

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite", "variant_name": "AC0010"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=40,
        height=80,
        base_name="AC0010",
        description=description,
        perc_img=np.ones((80, 40, 3), dtype=np.uint8) * 210,
        img_path="/tmp/AC0010.jpg",
        print_fn=lambda _message: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg baseline/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=_render,
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda _target, rendered: 120.0 if rendered == "description_rendered" else 20.0,
    )

    assert result == ("AC0010", description, {"mode": "non_composite", "variant_name": "AC0010"}, 1, 20.0)
    assert logs[0][0] == "status=non_composite_elementwise_symbol_fit"
    assert "non_composite_selection=raster_fit_overrides_poor_description_geometry" in logs[0]
    assert artifacts and artifacts[0][1] == "structured_rendered"


def test_reference_heat_exchanger_variants_remain_pixel_selectable_but_optimizable() -> None:
    description = (
        "Wie AC0010: Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, "
        "horizontaler Farbverlauf dunkel-hell-dunkel sowie graue Diagonale von oben rechts nach unten links."
    )
    geometry_ir = non_composite_runtime_helpers.geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description)

    assert non_composite_runtime_helpers._is_description_heat_exchanger_geometry(geometry_ir) is True
    assert non_composite_runtime_helpers._description_reuses_reference_family(description) is True
    assert non_composite_runtime_helpers._prefer_description_geometry_candidate(geometry_ir, description=description) is False
