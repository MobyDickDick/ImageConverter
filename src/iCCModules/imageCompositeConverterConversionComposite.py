"""Extracted composite-iteration conversion helpers for imageCompositeConverter."""

from __future__ import annotations

from collections.abc import Callable


def runCompositeIterationImpl(
    *,
    max_iterations: int,
    width: int,
    height: int,
    params: dict[str, object],
    folder_path: str,
    target_img,
    np_module,
    generate_composite_svg_fn: Callable[[int, int, dict[str, object], str, float], str],
    render_svg_to_numpy_fn: Callable[[str, int, int], object | None],
    calculate_error_fn: Callable[[object, object], float],
    create_diff_image_fn: Callable[[object, object], object],
    write_attempt_artifacts_fn: Callable[..., None],
    write_validation_log_fn: Callable[[list[str]], None],
    record_render_failure_fn: Callable[..., None],
    print_fn: Callable[[str], None],
) -> tuple[int, float]:
    best_error = float("inf")
    best_svg = ""
    best_diff = None
    best_iter = 0

    epsilon_factors = np_module.linspace(0.05, 0.0005, max_iterations)
    plateau_tolerance = 1e-6
    min_plateau_iterations = min(max_iterations, 12)
    plateau_patience = min(max_iterations, max(8, max_iterations // 6))
    plateau_streak = 0
    previous_error: float | None = None
    stop_reason = "max_iterations"

    for i, eps in enumerate(epsilon_factors):
        svg_content = generate_composite_svg_fn(width, height, params, folder_path, float(eps))

        svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
        if svg_rendered is None:
            record_render_failure_fn(
                "composite_iteration_render_failed",
                svg_content=svg_content,
                params_snapshot=params,
            )
            return 0, float("inf")

        error = calculate_error_fn(target_img, svg_rendered)

        if previous_error is not None and abs(error - previous_error) <= plateau_tolerance:
            plateau_streak += 1
        else:
            plateau_streak = 0

        improved = error < best_error
        if improved or i == 0 or (i + 1) == max_iterations:
            print_fn(f"  [Iter {i+1}/{max_iterations}] Epsilon={eps:.4f} -> Diff-Fehler: {error:.2f}")

        if improved:
            best_error, best_svg, best_iter = error, svg_content, i + 1
            best_diff = create_diff_image_fn(target_img, svg_rendered)

        previous_error = error

        if (i + 1) >= min_plateau_iterations and plateau_streak >= plateau_patience:
            print_fn(
                "  -> Früher Abbruch: Diff-Fehler blieb "
                f"{plateau_streak + 1} Iterationen innerhalb ±{plateau_tolerance:.0e}"
            )
            stop_reason = "plateau"
            break

    print_fn(f"-> Bester Match in Iteration {best_iter} (Fehler auf {best_error:.2f} reduziert)")
    if stop_reason == "plateau":
        if best_iter <= 1:
            print_fn("-> Konvergenzdiagnose: Plateau ohne messbare Verbesserung (Parameterraum ggf. erweitern)")
        else:
            print_fn("-> Konvergenzdiagnose: Plateau nach Verbesserung erreicht (lokales Optimum wahrscheinlich)")
    else:
        print_fn("-> Konvergenzdiagnose: Iterationsbudget ausgeschöpft (Optimum unklar, ggf. Suchraum erweitern)")

    if best_svg:
        write_attempt_artifacts_fn(best_svg, diff_img=best_diff)

    write_validation_log_fn(
        [
            "status=composite_ok",
            f"convergence={stop_reason}",
            f"best_iter={int(best_iter)}",
            f"best_error={float(best_error):.6f}",
        ]
    )
    return best_iter, best_error
