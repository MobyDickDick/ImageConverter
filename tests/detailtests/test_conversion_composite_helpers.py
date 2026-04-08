from __future__ import annotations

from src.iCCModules import imageCompositeConverterConversionComposite as conversion_composite_helpers


class _NpStub:
    @staticmethod
    def linspace(_start: float, _end: float, num: int):
        return [0.1 for _ in range(num)]


def test_run_composite_iteration_impl_uses_plateau_and_logs() -> None:
    logs: list[str] = []
    validation_rows: list[list[str]] = []
    write_calls: list[tuple[str, object]] = []

    def _render(_svg: str, _w: int, _h: int) -> object:
        return object()

    def _calc(_target: object, _rendered: object) -> float:
        return 10.0

    best_iter, best_error = conversion_composite_helpers.runCompositeIterationImpl(
        max_iterations=12,
        width=8,
        height=8,
        params={"mode": "composite"},
        folder_path="/tmp",
        target_img=object(),
        np_module=_NpStub(),
        generate_composite_svg_fn=lambda _w, _h, _params, _folder, _eps: "<svg/>",
        render_svg_to_numpy_fn=_render,
        calculate_error_fn=_calc,
        create_diff_image_fn=lambda _target, _rendered: {"diff": True},
        write_attempt_artifacts_fn=lambda svg, **kwargs: write_calls.append((svg, kwargs.get("diff_img"))),
        write_validation_log_fn=validation_rows.append,
        record_render_failure_fn=lambda *_args, **_kwargs: logs.append("render_failure"),
        print_fn=logs.append,
    )

    assert best_iter == 1
    assert best_error == 10.0
    assert validation_rows and validation_rows[0][0] == "status=composite_ok"
    assert any("convergence=plateau" == row for row in validation_rows[0])
    assert write_calls and write_calls[0][0] == "<svg/>"
    assert any("Früher Abbruch" in msg for msg in logs)
