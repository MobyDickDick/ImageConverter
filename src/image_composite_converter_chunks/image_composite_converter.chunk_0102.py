            for row in strategy_logs:
                writer.writerow([
                    row["filename"],
                    row["donor_variant"],
                    row["rotation_deg"],
                    f"{float(row['scale']):.4f}",
                    f"{float(row['old_error_per_pixel']):.8f}",
                    f"{float(row['new_error_per_pixel']):.8f}",
                ])

    log_path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    semantic_results: list[dict[str, object]] = []
    with open(log_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Dateiname", "Gefundene Elemente", "Beste Iteration", "Diff-Score", "FehlerProPixel"])
        for filename in files:
            row = result_map.get(filename)
            if row is None:
                continue
            params = dict(row["params"])
            writer.writerow([
                filename,
                " + ".join(params.get("elements", [])),
                int(row["best_iter"]),
                f"{float(row['best_error']):.2f}",
                f"{float(row['error_per_pixel']):.8f}",
            ])

            if params.get("mode") == "semantic_badge":
                semantic_results.append(
                    {
                        "filename": filename,
                        "base": row["base"],
                        "variant": row["variant"],
                        "w": int(row.get("w", 0)),
                        "h": int(row.get("h", 0)),
                        "error": float(row["best_error"]),
                    }
                )

    _harmonize_semantic_size_variants(semantic_results, folder_path, svg_out_dir, reports_out_dir)
    semantic_audit_rows = [
        dict(audit)
        for row in result_map.values()
        for audit in [dict(row.get("params", {}).get("semantic_audit", {}))]
        if audit
    ]
    _write_semantic_audit_report(reports_out_dir, semantic_audit_rows)
    _write_pixel_delta2_ranking(folder_path, svg_out_dir, reports_out_dir)
    _write_ac08_weak_family_status_report(
        reports_out_dir,
        selected_variants=sorted(normalized_selected_variants),
    )
    _write_ac08_regression_manifest(
        reports_out_dir,
        folder_path=folder_path,
        csv_path=csv_path,
        iterations=iterations,
        selected_variants=sorted(normalized_selected_variants),
    )
    ac08_success_gate = _write_ac08_success_criteria_report(
        reports_out_dir,
        selected_variants=sorted(normalized_selected_variants),
    )
    if ac08_success_gate is not None:
        failed_criteria = [
            key
            for key in (
                "criterion_no_new_batch_aborts",
                "criterion_no_accepted_regressions",
                "criterion_validation_rounds_recorded",
                "criterion_regression_set_improved",
                "criterion_stable_families_not_worse",
            )
            if not bool(ac08_success_gate.get(key, False))
        ]
        if failed_criteria:
            print(
                "[WARN] AC08 success gate failed: "
                + ", ".join(failed_criteria)
                + f" (mean_validation_rounds_per_file={float(ac08_success_gate.get('mean_validation_rounds_per_file', 0.0)):.3f})"
            )
        else:
            print(
                "[INFO] AC08 success gate passed "
                f"(mean_validation_rounds_per_file={float(ac08_success_gate.get('mean_validation_rounds_per_file', 0.0)):.3f})."
            )
    if SUCCESSFUL_CONVERSIONS_MANIFEST.exists():
        update_successful_conversions_manifest_with_metrics(
            folder_path=folder_path,
            svg_out_dir=svg_out_dir,
            reports_out_dir=reports_out_dir,
            manifest_path=SUCCESSFUL_CONVERSIONS_MANIFEST,
        )
    generated_overviews = generate_conversion_overviews(diff_out_dir, svg_out_dir, reports_out_dir)
    if generated_overviews:
        print(
            "[INFO] Übersichts-Kacheln erzeugt: "
            + ", ".join(f"{key}={path}" for key, path in sorted(generated_overviews.items()))
        )
