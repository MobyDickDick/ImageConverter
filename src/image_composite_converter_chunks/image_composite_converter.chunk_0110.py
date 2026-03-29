        f"semantic_mismatch_count={semantic_mismatch_count}",
        f"batch_abort_or_render_failure_count={batch_abort_count}",
        f"rejected_regression_count={rejected_regression_count}",
        f"accepted_regression_count={accepted_regression_count}",
        f"previous_good_expected={len(previous_good['expected'])}",
        f"previous_good_preserved_count={previous_good_preserved_count}",
        f"previous_good_regressed_count={previous_good_regressed_count}",
        f"previous_good_missing_count={previous_good_missing_count}",
        f"mean_validation_rounds_per_file={mean_validation_rounds:.3f}",
        f"criterion_no_new_batch_aborts={int(no_new_batch_aborts)}",
        f"criterion_no_accepted_regressions={int(no_accepted_regressions)}",
        f"criterion_validation_rounds_recorded={int(validation_rounds_recorded)}",
        f"criterion_regression_set_improved={int(regression_set_improved)}",
        f"criterion_stable_families_not_worse={int(stable_families_not_worse)}",
        f"overall_success={int(overall_success)}",
    ]
    if missing_variants:
        summary_lines.append("missing_variants=" + ",".join(missing_variants))
    if previous_good["preserved"]:
        summary_lines.append("previous_good_preserved=" + ",".join(previous_good["preserved"]))
    if previous_good["regressed"]:
        summary_lines.append("previous_good_regressed=" + ",".join(previous_good["regressed"]))
    if previous_good["missing"]:
        summary_lines.append("previous_good_missing=" + ",".join(previous_good["missing"]))

    with open(os.path.join(reports_out_dir, "ac08_success_criteria.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")

    return {
        "overall_success": overall_success,
        "criterion_no_new_batch_aborts": no_new_batch_aborts,
        "criterion_no_accepted_regressions": no_accepted_regressions,
        "criterion_validation_rounds_recorded": validation_rounds_recorded,
        "criterion_regression_set_improved": regression_set_improved,
        "criterion_stable_families_not_worse": stable_families_not_worse,
        "mean_validation_rounds_per_file": mean_validation_rounds,
    }


def _write_ac08_weak_family_status_report(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
    ranking_threshold: float = 18.0,
) -> None:
    """Summarize currently weak AC08 families and the mitigation status implemented in code."""
    normalized_variants = sorted({str(variant).strip().upper() for variant in selected_variants if str(variant).strip()})
    if not normalized_variants or any(not variant.startswith("AC08") for variant in normalized_variants):
        return

    ranking_rows: list[dict[str, str]] = []
    ranking_path = os.path.join(reports_out_dir, "pixel_delta2_ranking.csv")
    if os.path.exists(ranking_path):
        with open(ranking_path, "r", encoding="utf-8", newline="") as f:
            ranking_rows = list(csv.DictReader(f, delimiter=";"))

    ranking_by_variant: dict[str, dict[str, str]] = {}
    for row in ranking_rows:
        image_name = str(row.get("image", "")).strip()
        if not image_name:
            continue
        variant = os.path.splitext(image_name)[0].upper()
        ranking_by_variant[variant] = row

    focus_by_variant = {case["variant"].upper(): case["focus"] for case in AC08_REGRESSION_CASES}
    weak_rows: list[dict[str, str]] = []
    for variant in normalized_variants:
        base = variant.split("_", 1)[0]
        ranking_row = ranking_by_variant.get(variant, {})
        mean_delta2_raw = str(ranking_row.get("mean_delta2", "")).strip()
        try:
            mean_delta2 = float(mean_delta2_raw) if mean_delta2_raw else float("nan")
        except ValueError:
            mean_delta2 = float("nan")
        is_weak = (not math.isfinite(mean_delta2)) or mean_delta2 > ranking_threshold
        if not is_weak:
            continue

        mitigation = AC08_MITIGATION_STATUS.get(base, {})
        log_path = os.path.join(reports_out_dir, f"{variant}_element_validation.log")
        log_text = ""
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                log_text = f.read()

        active_markers: list[str] = []
        if "adaptive_unlock_applied" in log_text:
            active_markers.append("adaptive_unlock_applied")
        if "small_variant_mode_active" in log_text:
            active_markers.append("small_variant_mode_active")
        if "semantic_audit_status=" in log_text:
            active_markers.append("semantic_audit_logged")
        if "stopped_due_to_stagnation" in log_text:
            active_markers.append("stagnation_guard_triggered")

        weak_rows.append({
            "variant": variant,
            "base_family": base,
            "focus": focus_by_variant.get(variant, "review"),
            "mean_delta2": "nan" if not math.isfinite(mean_delta2) else f"{mean_delta2:.6f}",
