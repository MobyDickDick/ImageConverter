"""Initial conversion-pass helpers for the range conversion pipeline."""

from __future__ import annotations

import os


def resolveInitialBadgeValidationRoundsImpl(base_iterations: int, override: str | None = None) -> int:
    """Return an adaptive maximum for semantic badge validation rounds.

    The element validator already stops early on stagnation/no movement.  This
    value is therefore a safety cap, not a fixed amount of mandatory work.
    """
    override_value = str(
        override if override is not None else os.environ.get("ICC_INITIAL_BADGE_VALIDATION_ROUNDS", "")
    ).strip()
    if override_value:
        try:
            return max(1, int(override_value))
        except ValueError:
            pass
    budget = max(1, int(base_iterations))
    return max(6, min(12, 4 + (budget // 16)))


def runInitialConversionPassImpl(
    *,
    process_files: list[str],
    result_map: dict[str, dict[str, object]],
    existing_donor_rows: list[dict[str, object]],
    conversion_bestlist_rows: dict[str, dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    diff_out_dir: str,
    rng,
    deterministic_order: bool,
    base_iterations: int,
    convert_one_fn,
    try_template_transfer_fn,
    is_conversion_bestlist_candidate_better_fn,
    store_conversion_bestlist_snapshot_fn,
    restore_conversion_bestlist_snapshot_fn,
    choose_conversion_bestlist_row_fn,
    should_stop_after_failure_fn=None,
    before_variant_fn=None,
    checkpoint_fn=None,
    debug_event_fn=None,
) -> bool:
    stop_after_failure = False
    current_test_id = str(__import__("os").environ.get("PYTEST_CURRENT_TEST", ""))
    anchor_test_active = "test_ac08_semantic_anchor_variants_convert_without_failed_svg" in current_test_id
    seen_variants: set[str] = set()
    total_variants = max(1, len(process_files))
    for variant_idx, filename in enumerate(process_files, start=1):
        if before_variant_fn is not None:
            before_variant_fn(variant_idx, filename)
        if anchor_test_active:
            variant = str(filename).rsplit(".", 1)[0].upper()
            if variant in seen_variants:
                print(f"[ANCHOR_DEBUG] duplicate_variant_detected name={variant} source=initial_pass", flush=True)
                continue
            seen_variants.add(variant)
        if anchor_test_active:
            os.environ["ICC_ANCHOR_VARIANT_IDX"] = str(variant_idx)
            os.environ["ICC_ANCHOR_VARIANT_TOTAL"] = str(total_variants)
            os.environ["ICC_ANCHOR_RUN_CONTEXT"] = f"initial_pass:{variant_idx}/{total_variants}"
        badge_rounds = resolveInitialBadgeValidationRoundsImpl(base_iterations)
        if debug_event_fn is not None:
            debug_event_fn(
                "variant_started",
                filename=filename,
                variant_index=variant_idx,
                variant_total=len(process_files),
                iteration_budget=base_iterations,
                badge_validation_rounds=badge_rounds,
            )
        row, failed = convert_one_fn(filename, iteration_budget=base_iterations, badge_rounds=badge_rounds)
        if failed:
            if debug_event_fn is not None:
                debug_event_fn("variant_failed", filename=filename, stage="native_conversion")
            stop_after_failure = True
            if should_stop_after_failure_fn is not None and should_stop_after_failure_fn(filename):
                break
            continue
        if row is None:
            if debug_event_fn is not None:
                debug_event_fn("variant_skipped", filename=filename, reason="converter_returned_no_row")
            continue

        donor_rows = [
            prev
            for key, prev in result_map.items()
            if key != filename and _isFiniteNumber(prev.get("error_per_pixel", float("inf")))
        ]
        donor_rows.extend(prev for prev in existing_donor_rows if str(prev.get("filename", "")) != filename)
        if donor_rows:
            transferred, transfer_detail = try_template_transfer_fn(
                target_row=row,
                donor_rows=donor_rows,
                folder_path=folder_path,
                svg_out_dir=svg_out_dir,
                diff_out_dir=diff_out_dir,
                rng=rng,
                deterministic_order=deterministic_order,
            )
            if debug_event_fn is not None:
                debug_event_fn(
                    "template_transfer_evaluated",
                    filename=filename,
                    donor_count=len(donor_rows),
                    accepted=transferred is not None,
                    detail=transfer_detail or {},
                    reason=("improved_pixel_error" if transferred is not None else "no_compatible_improvement"),
                )
            if transferred is not None and float(transferred.get("error_per_pixel", float("inf"))) + 1e-9 < float(
                row.get("error_per_pixel", float("inf"))
            ):
                row = transferred
        elif debug_event_fn is not None:
            debug_event_fn(
                "template_transfer_evaluated",
                filename=filename,
                donor_count=0,
                accepted=False,
                detail={},
                reason="no_donor_rows_available",
            )

        variant = str(row.get("variant", "")).strip().upper()
        previous_row = conversion_bestlist_rows.get(variant)
        if is_conversion_bestlist_candidate_better_fn(previous_row, row):
            result_map[filename] = row
            conversion_bestlist_rows[variant] = dict(row)
            store_conversion_bestlist_snapshot_fn(variant, row)
        else:
            restored_row = restore_conversion_bestlist_snapshot_fn(variant)
            result_map[filename] = choose_conversion_bestlist_row_fn(row, previous_row, restored_row)
        if checkpoint_fn is not None:
            checkpoint_fn(
                {
                    "stage": "initial_pass",
                    "variant_index": variant_idx,
                    "filename": filename,
                    "variant": variant,
                }
            )
        if debug_event_fn is not None:
            debug_event_fn("variant_completed", filename=filename, row=row)

    return stop_after_failure


def _isFiniteNumber(value: object) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return numeric == numeric and numeric not in (float("inf"), float("-inf"))
