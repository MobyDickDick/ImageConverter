""" End move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variants.py """


""" Start move to File mainFiles/convert_rangeFiles/_write_ac08_regression_manifest.py
import src
"""
def _write_ac08_regression_manifest(
    reports_out_dir: str,
    *,
    folder_path: str,
    csv_path: str,
    iterations: int,
    selected_variants: list[str],
) -> None:
    """Write a reproducible manifest for the fixed AC08 regression subset."""
    if sorted(selected_variants) != sorted(AC08_REGRESSION_VARIANTS):
        return

    csv_manifest_path = os.path.join(reports_out_dir, "ac08_regression_set.csv")
    with open(csv_manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["set", "variant", "focus", "reason"])
        for case in AC08_REGRESSION_CASES:
            variant = str(case["variant"])
            focus = str(case["focus"])
            reason = str(case["reason"])
            if variant == "AC0811_L" and focus == "stable_good":
                reason = "Known regression-safe good conversion anchor"
            writer.writerow([AC08_REGRESSION_SET_NAME, variant, focus, reason])

    summary_lines = [
        f"set={AC08_REGRESSION_SET_NAME}",
        f"images_total={len(AC08_REGRESSION_CASES)}",
        f"iterations={int(iterations)}",
        f"folder_path={folder_path}",
        f"csv_path={csv_path}",
        "expected_reports=Iteration_Log.csv,quality_tercile_passes.csv,pixel_delta2_ranking.csv,pixel_delta2_summary.txt,ac08_weak_family_status.csv,ac08_weak_family_status.txt,ac08_success_metrics.csv,ac08_success_criteria.txt",
        "expected_logs=variant_harmonization.log,shape_catalog.csv",
        (
            "recommended_command=python -m src.image_composite_converter "
            f"{folder_path} --csv-path {csv_path} --ac08-regression-set {int(iterations)}"
        ),
    ]
    with open(os.path.join(reports_out_dir, "ac08_regression_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")
""" End move to File mainFiles/convert_rangeFiles/_write_ac08_regression_manifest.py """


""" Start move to File mainFiles/convert_rangeFiles/_write_ac08_success_criteria_reportFiles/_summarize_previous_good_ac08_variants.py
import src
"""
def _summarize_previous_good_ac08_variants(reports_out_dir: str) -> dict[str, object]:
    """Summarize whether previously good AC08 variants stayed semantic_ok in the latest run."""
    preserved: list[str] = []
    regressed: list[str] = []
    missing: list[str] = []

    for variant in AC08_PREVIOUSLY_GOOD_VARIANTS:
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
        "expected": list(AC08_PREVIOUSLY_GOOD_VARIANTS),
        "preserved": preserved,
        "regressed": regressed,
        "missing": missing,
    }
""" End move to File mainFiles/convert_rangeFiles/_write_ac08_success_criteria_reportFiles/_summarize_previous_good_ac08_variants.py """


""" Start move to File mainFiles/convert_rangeFiles/_write_ac08_success_criteria_report.py
import src
"""
