        if variant and variant in skips:
            continue
        if math.isfinite(allowed_error_per_pixel) and err <= allowed_error_per_pixel:
            continue
        open_rows.append(row)

    return sorted(open_rows, key=_quality_sort_key, reverse=True)


def _iteration_strategy_for_pass(pass_idx: int, base_iterations: int) -> tuple[int, int]:
    """Adaptive per-pass search budget for unresolved quality cases."""
    p = max(1, int(pass_idx))
    base = max(1, int(base_iterations))
    phase = (p - 1) % 3

    if phase == 0:
        return base + p, 6 + p
    if phase == 1:
        return base + 24 + (p * 2), 7 + p
    return base + 48 + (p * 3), 8 + p


def _adaptive_iteration_budget_for_quality_row(row: dict[str, object], planned_budget: int) -> int:
    """Tune per-row iteration budget using convergence/plateau quality signals.

    Heuristic goals:
    - plateau reached clearly before budget end -> reduce budget next pass
    - max-iterations hit or best-iter near budget end -> increase budget
    """
    budget = max(1, int(planned_budget))
    convergence = str(row.get("convergence", "") or "").strip().lower()
    best_iter_raw = row.get("best_iter", 0)
    try:
        best_iter = max(0, int(best_iter_raw))
    except (TypeError, ValueError):
        best_iter = 0

    usage_ratio = (best_iter / budget) if budget > 0 else 0.0

    if convergence == "plateau":
        if usage_ratio <= 0.35:
            return max(1, int(round(budget * 0.60)))
        if usage_ratio <= 0.55:
            return max(1, int(round(budget * 0.80)))
        return budget

    if convergence == "max_iterations" or usage_ratio >= 0.95:
        return max(1, int(round(budget * 1.35)))
    if usage_ratio >= 0.80:
        return max(1, int(round(budget * 1.15)))
    return budget


def _write_quality_pass_report(
    reports_out_dir: str,
    pass_rows: list[dict[str, object]],
) -> None:
    if not pass_rows:
        return

    out_path = os.path.join(reports_out_dir, "quality_tercile_passes.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "pass",
            "filename",
            "old_error_per_pixel",
            "new_error_per_pixel",
            "old_mean_delta2",
            "new_mean_delta2",
            "improved",
            "decision",
            "iteration_budget",
            "badge_validation_rounds",
        ])
        for row in pass_rows:
            writer.writerow([
                row["pass"],
                row["filename"],
                f"{float(row['old_error_per_pixel']):.8f}",
                f"{float(row['new_error_per_pixel']):.8f}",
                f"{float(row.get('old_mean_delta2', float('inf'))):.6f}",
                f"{float(row.get('new_mean_delta2', float('inf'))):.6f}",
                "1" if bool(row["improved"]) else "0",
                row.get("decision", "accepted_improvement" if bool(row["improved"]) else "rejected_regression"),
                row["iteration_budget"],
                row["badge_validation_rounds"],
            ])


def _evaluate_quality_pass_candidate(
    old_row: dict[str, object],
    new_row: dict[str, object],
) -> tuple[bool, str, float, float, float, float]:
    """Return whether a quality-pass candidate should replace the previous result.

    The acceptance rule mirrors AC08 task 1.1: keep the new candidate only when
    at least one core quality metric improves (`error_per_pixel` or
    `mean_delta2`). The caller also receives the normalized metrics so reporting
    can use one consistent decision path for stochastic re-runs and fallback
