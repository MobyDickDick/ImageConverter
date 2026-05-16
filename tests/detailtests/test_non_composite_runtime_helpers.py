from __future__ import annotations

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
        perc_img="target",
        img_path=str(image_dir / "AC0VR2_M.jpg"),
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg />",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg />",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: "rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda target, rendered: 0.5 if (target, rendered) == ("target", "rendered") else 99.0,
    )

    assert result == ("AC0VR2_M", "desc", {"mode": "manual_review", "review_reason": "Bitte prüfen"}, 1, 0.5)
    assert logs[0][0] == "status=manual_review_plan_b_sample_svg"
    assert prints and "Plan B aktiv" in prints[0]
    assert artifacts == [("<svg><circle r='1'/></svg>", "rendered")]


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
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: object(),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda *_args, **_kwargs: None,
        calculate_error_fn=lambda *_args, **_kwargs: 0.0,
    )

    assert result is None
    assert logs == [["status=skipped_manual_review", "manual_review_reason=Bitte prüfen"]]
    assert prints == ["  -> Überspringe Bild: Bitte prüfen"]


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
