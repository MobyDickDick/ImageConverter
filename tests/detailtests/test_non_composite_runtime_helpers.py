from __future__ import annotations

import numpy as np

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as non_composite_runtime_helpers

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

def test_run_non_composite_iteration_impl_forces_ac0011_sample_svg_even_when_sample_error_is_worse(tmp_path) -> None:
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

    assert result == ("AC0011", "desc", {"mode": "non_composite"}, 1, 1.7)
    assert logs[0][0] == "status=non_composite_pure_svg_placeholder_vector"
    assert logs[-1][0] == "status=non_composite_plan_b_sample_svg_selected"
    assert any(line.endswith("AC0011.svg") for line in logs[-1] if line.startswith("sample_svg_path="))
    assert "force_sample_svg=1" in logs[-1]
    assert prints and "forcierte Sample-Auswahl" in prints[-1]
    assert artifacts == [("<svg sample/>", "sample_rendered")]

def test_run_non_composite_iteration_impl_forced_ac0011_prefers_exact_sample_over_reference(tmp_path) -> None:
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

    assert result == ("AC0011", "Wie AC0010: geometrische Variante", {"mode": "non_composite"}, 1, 1.7)
    assert logs[-1][0] == "status=non_composite_plan_b_sample_svg_selected"
    assert any(line.endswith("AC0011.svg") for line in logs[-1] if line.startswith("sample_svg_path="))
    assert "force_sample_svg=1" in logs[-1]
    assert artifacts == [("<svg exact-sample/>", "exact_rendered")]

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
