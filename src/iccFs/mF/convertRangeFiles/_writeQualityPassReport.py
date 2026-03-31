def _writeQualityPassReport(
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
