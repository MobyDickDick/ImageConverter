"""Quality-pass iteration helpers for the range conversion pipeline."""

from __future__ import annotations

import os


def runQualityPassesImpl(
    *,
    max_quality_passes: int,
    stop_after_failure: bool,
    deterministic_order: bool,
    rng,
    base_iterations: int,
    allowed_error_per_pixel: float,
    skip_variants: set[str],
    result_map: dict[str, dict[str, object]],
    quality_logs: list[dict[str, object]],
    conversion_bestlist_rows: dict[str, dict[str, object]],
    convert_one_fn,
    select_open_quality_cases_fn,
    select_middle_lower_tercile_fn,
    iteration_strategy_for_pass_fn,
    adaptive_iteration_budget_for_quality_row_fn,
    evaluate_quality_pass_candidate_fn,
    store_conversion_bestlist_snapshot_fn,
    restore_conversion_bestlist_snapshot_fn,
    before_pass_fn=None,
) -> bool:
    for pass_idx in range(1, max_quality_passes + 1):
        if stop_after_failure:
            break
        if before_pass_fn is not None:
            before_pass_fn(pass_idx)

        current_rows = [row for row in result_map.values() if _isFiniteNumber(row.get("error_per_pixel", float("inf")))]
        candidates = select_open_quality_cases_fn(
            current_rows,
            allowed_error_per_pixel=allowed_error_per_pixel,
            skip_variants=skip_variants,
        )
        if not candidates:
            candidates = select_middle_lower_tercile_fn(current_rows)
        if not candidates:
            break

        improved_in_pass = False
        iteration_budget, badge_rounds = iteration_strategy_for_pass_fn(pass_idx, base_iterations)
        if len(candidates) > 1 and not deterministic_order:
            rng.shuffle(candidates)

        for row in candidates:
            filename = str(row["filename"])
            current_test_id = str(os.environ.get("PYTEST_CURRENT_TEST", ""))
            anchor_test_active = "test_ac08_semantic_anchor_variants_convert_without_failed_svg" in current_test_id
            if anchor_test_active:
                variant = str(row.get("variant", "")).strip().upper() or str(filename).rsplit(".", 1)[0].upper()
                os.environ["ICC_ANCHOR_RUN_CONTEXT"] = (
                    f"quality_pass:{pass_idx};candidate={variant};candidates={len(candidates)}"
                )
            adaptive_iteration_budget = adaptive_iteration_budget_for_quality_row_fn(row, iteration_budget)
            new_row, failed = convert_one_fn(filename, iteration_budget=adaptive_iteration_budget, badge_rounds=badge_rounds)
            if failed:
                stop_after_failure = True
                continue
            if new_row is None:
                continue

            improved, decision, prev_error_pp, new_error_pp, prev_mean_delta2, new_mean_delta2 = evaluate_quality_pass_candidate_fn(
                row,
                new_row,
            )
            if improved:
                result_map[filename] = new_row
                improved_in_pass = True
                variant = str(new_row.get("variant", "")).strip().upper()
                if variant:
                    conversion_bestlist_rows[variant] = dict(new_row)
                    store_conversion_bestlist_snapshot_fn(variant, new_row)
            else:
                variant = str(row.get("variant", "")).strip().upper()
                if variant:
                    restore_conversion_bestlist_snapshot_fn(variant)

            quality_logs.append(
                {
                    "pass": pass_idx,
                    "filename": filename,
                    "old_error_per_pixel": prev_error_pp,
                    "new_error_per_pixel": new_error_pp,
                    "old_mean_delta2": prev_mean_delta2,
                    "new_mean_delta2": new_mean_delta2,
                    "improved": improved,
                    "decision": decision,
                    "iteration_budget": adaptive_iteration_budget,
                    "badge_validation_rounds": badge_rounds,
                }
            )

        if not improved_in_pass:
            break

    return stop_after_failure


def _isFiniteNumber(value: object) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return numeric == numeric and numeric not in (float("inf"), float("-inf"))
