"""Initial conversion-pass helpers for the range conversion pipeline."""

from __future__ import annotations


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
) -> bool:
    stop_after_failure = False
    for filename in process_files:
        row, failed = convert_one_fn(filename, iteration_budget=base_iterations, badge_rounds=6)
        if failed:
            stop_after_failure = True
            break
        if row is None:
            continue

        donor_rows = [
            prev
            for key, prev in result_map.items()
            if key != filename and _isFiniteNumber(prev.get("error_per_pixel", float("inf")))
        ]
        donor_rows.extend(prev for prev in existing_donor_rows if str(prev.get("filename", "")) != filename)
        if donor_rows:
            transferred, _detail = try_template_transfer_fn(
                target_row=row,
                donor_rows=donor_rows,
                folder_path=folder_path,
                svg_out_dir=svg_out_dir,
                diff_out_dir=diff_out_dir,
                rng=rng,
                deterministic_order=deterministic_order,
            )
            if transferred is not None and float(transferred.get("error_per_pixel", float("inf"))) + 1e-9 < float(
                row.get("error_per_pixel", float("inf"))
            ):
                row = transferred

        variant = str(row.get("variant", "")).strip().upper()
        previous_row = conversion_bestlist_rows.get(variant)
        if is_conversion_bestlist_candidate_better_fn(previous_row, row):
            result_map[filename] = row
            conversion_bestlist_rows[variant] = dict(row)
            store_conversion_bestlist_snapshot_fn(variant, row)
        else:
            restored_row = restore_conversion_bestlist_snapshot_fn(variant)
            result_map[filename] = choose_conversion_bestlist_row_fn(row, previous_row, restored_row)

    return stop_after_failure


def _isFiniteNumber(value: object) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return numeric == numeric and numeric not in (float("inf"), float("-inf"))
