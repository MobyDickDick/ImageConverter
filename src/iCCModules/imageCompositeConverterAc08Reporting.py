from __future__ import annotations

import csv
import math
import os
import re


def writeAc08RegressionManifestImpl(
    reports_out_dir: str,
    *,
    folder_path: str,
    csv_path: str,
    iterations: int,
    selected_variants: list[str],
    ac08_regression_variants: tuple[str, ...],
    ac08_regression_cases: tuple[dict[str, str], ...],
    ac08_regression_set_name: str,
) -> None:
    """Write a reproducible manifest for the fixed AC08 regression subset."""
    if sorted(selected_variants) != sorted(ac08_regression_variants):
        return

    csv_manifest_path = os.path.join(reports_out_dir, "ac08_regression_set.csv")
    with open(csv_manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["set", "variant", "focus", "reason"])
        for case in ac08_regression_cases:
            variant = str(case["variant"])
            focus = str(case["focus"])
            reason = str(case["reason"])
            if variant == "AC0811_L" and focus == "stable_good":
                reason = "Known regression-safe good conversion anchor"
            writer.writerow([ac08_regression_set_name, variant, focus, reason])

    summary_lines = [
        f"set={ac08_regression_set_name}",
        f"images_total={len(ac08_regression_cases)}",
        f"iterations={int(iterations)}",
        f"folder_path={folder_path}",
        f"csv_path={csv_path}",
        "expected_reports=Iteration_Log.csv,quality_tercile_passes.csv,pixel_delta2_ranking.csv,pixel_delta2_summary.txt,ac08_weak_family_status.csv,ac08_weak_family_status.txt,ac08_success_metrics.csv,ac08_success_criteria.txt",
        "expected_logs=variant_harmonization.log,shape_catalog.csv",
        (
            "recommended_command=python -m src.imageCompositeConverter "
            f"{folder_path} --csv-path {csv_path} --ac08-regression-set {int(iterations)}"
        ),
    ]
    with open(os.path.join(reports_out_dir, "ac08_regression_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")


def summarizePreviousGoodAc08VariantsImpl(
    reports_out_dir: str,
    *,
    previous_good_variants: tuple[str, ...],
) -> dict[str, object]:
    """Summarize whether previously good AC08 variants stayed semantic_ok in the latest run."""
    preserved: list[str] = []
    regressed: list[str] = []
    missing: list[str] = []

    for variant in previous_good_variants:
        log_path = os.path.join(reports_out_dir, f"{variant}_element_validation.log")
        if not os.path.exists(log_path):
            missing.append(variant)
            continue
        with open(log_path, "r", encoding="utf-8") as f:
            log_text = f.read()
        if "status=semantic_ok" in log_text and "status=semantic_mismatch" not in log_text:
            preserved.append(variant)
        else:
            regressed.append(variant)

    return {
        "expected": list(previous_good_variants),
        "preserved": preserved,
        "regressed": regressed,
        "missing": missing,
    }


def writeAc08SuccessCriteriaReportImpl(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
    ac08_regression_variants: tuple[str, ...],
    ac08_regression_set_name: str,
    summarize_previous_good_fn,
) -> dict[str, object] | None:
    """Persist the written AC08 success criteria and the current measured status."""
    if sorted(selected_variants) != sorted(ac08_regression_variants):
        return None

    expected_variants = sorted(selected_variants)
    iteration_rows: list[dict[str, str]] = []
    iteration_log_path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    if os.path.exists(iteration_log_path):
        with open(iteration_log_path, "r", encoding="utf-8-sig", newline="") as f:
            iteration_rows = list(csv.DictReader(f, delimiter=";"))

    quality_rows: list[dict[str, str]] = []
    quality_path = os.path.join(reports_out_dir, "quality_tercile_passes.csv")
    if os.path.exists(quality_path):
        with open(quality_path, "r", encoding="utf-8", newline="") as f:
            quality_rows = list(csv.DictReader(f, delimiter=";"))

    converted_variants = {
        os.path.splitext(str(row.get("Dateiname", "")).strip())[0].upper()
        for row in iteration_rows
        if str(row.get("Dateiname", "")).strip()
    }
    missing_variants = [variant for variant in expected_variants if variant not in converted_variants]

    improved_error_count = 0
    improved_mean_delta2_count = 0
    rejected_regression_count = 0
    accepted_regression_count = 0
    for row in quality_rows:
        decision = str(row.get("decision", "")).strip()
        old_error = float(row.get("old_error_per_pixel", "inf"))
        new_error = float(row.get("new_error_per_pixel", "inf"))
        old_delta2 = float(row.get("old_mean_delta2", "inf"))
        new_delta2 = float(row.get("new_mean_delta2", "inf"))
        if math.isfinite(old_error) and math.isfinite(new_error) and new_error + 1e-9 < old_error:
            improved_error_count += 1
        if math.isfinite(old_delta2) and math.isfinite(new_delta2) and new_delta2 + 1e-6 < old_delta2:
            improved_mean_delta2_count += 1
        if decision == "rejected_regression":
            rejected_regression_count += 1
        if decision == "accepted_regression":
            accepted_regression_count += 1

    semantic_mismatch_count = 0
    render_failure_count = 0
    validation_round_counts: list[int] = []
    for variant in expected_variants:
        log_path = os.path.join(reports_out_dir, f"{variant}_element_validation.log")
        if not os.path.exists(log_path):
            continue
        with open(log_path, "r", encoding="utf-8") as f:
            log_text = f.read()
        if "status=semantic_mismatch" in log_text:
            semantic_mismatch_count += 1
        if "konnte nicht gerendert werden" in log_text or "Abbruch: SVG konnte nicht gerendert werden" in log_text:
            render_failure_count += 1
        rounds = len(re.findall(r"^Runde\s+\d+: elementweise Validierung gestartet$", log_text, flags=re.MULTILINE))
        if rounds > 0:
            validation_round_counts.append(rounds)

    batch_abort_count = len(missing_variants) + render_failure_count
    mean_validation_rounds = (
        sum(validation_round_counts) / float(len(validation_round_counts))
        if validation_round_counts
        else 0.0
    )

    previous_good = summarize_previous_good_fn(reports_out_dir)
    previous_good_preserved_count = len(previous_good["preserved"])
    previous_good_regressed_count = len(previous_good["regressed"])
    previous_good_missing_count = len(previous_good["missing"])

    regression_set_improved = improved_error_count > 0 or improved_mean_delta2_count > 0
    no_new_batch_aborts = batch_abort_count == 0
    no_accepted_regressions = accepted_regression_count == 0
    validation_rounds_recorded = mean_validation_rounds > 0.0
    stable_families_not_worse = (
        no_accepted_regressions
        and previous_good_regressed_count == 0
        and previous_good_missing_count == 0
    )
    overall_success = (
        no_new_batch_aborts
        and no_accepted_regressions
        and validation_rounds_recorded
        and regression_set_improved
        and stable_families_not_worse
    )

    metrics_path = os.path.join(reports_out_dir, "ac08_success_metrics.csv")
    with open(metrics_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["metric", "value"])
        writer.writerow(["regression_set", ac08_regression_set_name])
        writer.writerow(["images_expected", len(expected_variants)])
        writer.writerow(["images_converted", len(converted_variants)])
        writer.writerow(["images_missing", len(missing_variants)])
        writer.writerow(["improved_error_per_pixel_count", improved_error_count])
        writer.writerow(["improved_mean_delta2_count", improved_mean_delta2_count])
        writer.writerow(["semantic_mismatch_count", semantic_mismatch_count])
        writer.writerow(["batch_abort_or_render_failure_count", batch_abort_count])
        writer.writerow(["rejected_regression_count", rejected_regression_count])
        writer.writerow(["accepted_regression_count", accepted_regression_count])
        writer.writerow(["previous_good_expected", len(previous_good["expected"])])
        writer.writerow(["previous_good_preserved_count", previous_good_preserved_count])
        writer.writerow(["previous_good_regressed_count", previous_good_regressed_count])
        writer.writerow(["previous_good_missing_count", previous_good_missing_count])
        writer.writerow(["mean_validation_rounds_per_file", f"{mean_validation_rounds:.3f}"])
        writer.writerow(["criterion_no_new_batch_aborts", int(no_new_batch_aborts)])
        writer.writerow(["criterion_no_accepted_regressions", int(no_accepted_regressions)])
        writer.writerow(["criterion_validation_rounds_recorded", int(validation_rounds_recorded)])
        writer.writerow(["criterion_regression_set_improved", int(regression_set_improved)])
        writer.writerow(["criterion_stable_families_not_worse", int(stable_families_not_worse)])
        writer.writerow(["overall_success", int(overall_success)])

    summary_lines = [
        f"set={ac08_regression_set_name}",
        "goal=Abschluss einer AC08-Maßnahme objektiv bewerten",
        "success_metrics=improved_error_per_pixel_count,improved_mean_delta2_count,semantic_mismatch_count,batch_abort_or_render_failure_count,mean_validation_rounds_per_file",
        (
            "success_definition=no_new_batch_aborts && no_accepted_regressions "
            "&& validation_rounds_recorded && regression_set_improved && stable_families_not_worse"
        ),
        f"images_expected={len(expected_variants)}",
        f"images_converted={len(converted_variants)}",
        f"images_missing={len(missing_variants)}",
        f"improved_error_per_pixel_count={improved_error_count}",
        f"improved_mean_delta2_count={improved_mean_delta2_count}",
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


def writeAc08WeakFamilyStatusReportImpl(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
    ac08_regression_cases: tuple[dict[str, str], ...],
    ac08_mitigation_status: dict[str, dict[str, str]],
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

    focus_by_variant = {case["variant"].upper(): case["focus"] for case in ac08_regression_cases}
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

        mitigation = ac08_mitigation_status.get(base, {})
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
            "risk": str(mitigation.get("risk", "unknown")),
            "family_group": str(mitigation.get("family", "unknown")),
            "implemented_mitigations": str(mitigation.get("implemented", "manual_review")),
            "active_log_markers": ",".join(active_markers) if active_markers else "none_observed",
            "status": str(mitigation.get("status", "No family-specific mitigation documented yet; inspect logs and ranking manually.")),
        })

    weak_rows.sort(
        key=lambda row: (
            -float("inf") if row["mean_delta2"] == "nan" else float(row["mean_delta2"]),
            row["variant"],
        ),
        reverse=True,
    )

    csv_path = os.path.join(reports_out_dir, "ac08_weak_family_status.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "variant",
            "base_family",
            "focus",
            "mean_delta2",
            "risk",
            "family_group",
            "implemented_mitigations",
            "active_log_markers",
            "status",
        ])
        for row in weak_rows:
            writer.writerow([
                row["variant"],
                row["base_family"],
                row["focus"],
                row["mean_delta2"],
                row["risk"],
                row["family_group"],
                row["implemented_mitigations"],
                row["active_log_markers"],
                row["status"],
            ])

    summary_lines = [
        f"ranking_threshold_mean_delta2={ranking_threshold:.3f}",
        f"weak_variants={len(weak_rows)}",
        "goal=Verbleibende AC08-Schwachfamilien und ihren aktuellen Mitigation-Status dokumentieren",
    ]
    if weak_rows:
        summary_lines.append("variants=" + ",".join(row["variant"] for row in weak_rows))
        for row in weak_rows:
            summary_lines.append(
                f"{row['variant']}: mean_delta2={row['mean_delta2']}; risk={row['risk']}; markers={row['active_log_markers']}; status={row['status']}"
            )
    else:
        summary_lines.append("variants=none")
        summary_lines.append("All selected AC08 variants are currently at or below the weak-family threshold.")

    with open(os.path.join(reports_out_dir, "ac08_weak_family_status.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")
