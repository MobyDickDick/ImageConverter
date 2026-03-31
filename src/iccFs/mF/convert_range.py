def convert_range(
    folder_path: str,
    csv_path: str,
    iterations: int,
    start_ref: str = "AR0102",
    end_ref: str = "AR0104",
    debug_ac0811_dir: str | None = None,
    debug_element_diff_dir: str | None = None,
    output_root: str | None = None,
    selected_variants: set[str] | None = None,
) -> str:
    out_root = output_root or _default_converted_symbols_root()
    svg_out_dir = _converted_svg_output_dir(out_root)
    diff_out_dir = _diff_output_dir(out_root)
    reports_out_dir = _reports_output_dir(out_root)

    os.makedirs(svg_out_dir, exist_ok=True)
    os.makedirs(diff_out_dir, exist_ok=True)
    os.makedirs(reports_out_dir, exist_ok=True)

    normalized_selected_variants = {str(v).upper() for v in (selected_variants or set()) if str(v).strip()}
    files = sorted(
        f
        for f in os.listdir(folder_path)
        if f.lower().endswith((".bmp", ".jpg", ".png", ".gif"))
        and _in_requested_range(f, start_ref, end_ref)
        and (not normalized_selected_variants or os.path.splitext(f)[0].upper() in normalized_selected_variants)
    )
    if cv2 is None or np is None:
        log_path = os.path.join(reports_out_dir, "Iteration_Log.csv")
        with open(log_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Dateiname", "Gefundene Elemente", "Beste Iteration", "Diff-Score", "FehlerProPixel"])
            for filename in files:
                stem = os.path.splitext(filename)[0]
                image_path = os.path.join(folder_path, filename)
                svg_content = _render_embedded_raster_svg(image_path)
                svg_path = os.path.join(svg_out_dir, f"{stem}.svg")
                with open(svg_path, "w", encoding="utf-8") as svg_file:
                    svg_file.write(svg_content)
                if fitz is not None:
                    diff = _create_diff_image_without_cv2(image_path, svg_content)
                    diff.save(os.path.join(diff_out_dir, f"{stem}_diff.png"))
                writer.writerow([filename, "embedded-raster", 0, "0.00", "0.00000000"])
        with open(os.path.join(reports_out_dir, "fallback_mode.txt"), "w", encoding="utf-8") as f:
            f.write(
                "Fallback-Modus aktiv: fehlende numpy/opencv-Abhängigkeiten; "
                "SVG-Dateien wurden als eingebettete Rasterbilder erzeugt"
                + (" und Differenzbilder via Pillow/PyMuPDF geschrieben.\n" if fitz is not None else ".\n")
            )
        generateConversionOverviews(diff_out_dir, svg_out_dir, reports_out_dir)
        return out_root
    rng = _conversion_random()
    run_seed = rng.randrange(1 << 30)
    Action.STOCHASTIC_RUN_SEED = int(run_seed)
    process_files = list(files)
    rng.shuffle(process_files)

    base_iterations = max(1, int(iterations))
    # Continue quality iterations while a pass still improves at least one case.
    # Abort as soon as the next pass cannot beat the previous state.
    max_quality_passes = 4
    quality_logs: list[dict[str, object]] = []
    result_map: dict[str, dict[str, object]] = {}
    batch_failures: list[dict[str, str]] = []
    stop_after_failure = False
    existing_donor_rows = _load_existing_conversion_rows(out_root, folder_path)

    def _convert_one(filename: str, iteration_budget: int, badge_rounds: int) -> tuple[dict[str, object] | None, bool]:
        image_path = os.path.join(folder_path, filename)
        base = os.path.splitext(filename)[0]
        log_file = os.path.join(reports_out_dir, f"{base}_element_validation.log")
        try:
            res = run_iteration_pipeline(
                image_path,
                csv_path,
                max(1, int(iteration_budget)),
                svg_out_dir,
                diff_out_dir,
                reports_out_dir,
                debug_ac0811_dir,
                debug_element_diff_dir,
                badge_validation_rounds=max(1, int(badge_rounds)),
            )
        except Exception as exc:
            batch_failures.append(
                {
                    "filename": filename,
                    "status": "batch_error",
                    "reason": type(exc).__name__,
                    "details": str(exc),
                    "log_file": os.path.basename(log_file),
                }
            )
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"status=batch_error\nfilename={filename}\nreason={type(exc).__name__}\ndetails={exc}\n")
            print(f"[WARN] {filename}: Batchlauf setzt nach Fehler fort ({type(exc).__name__}: {exc})")
            return None, True
        if not res:
            details = _read_validation_log_details(log_file)
            status = details.get("status", "")
            if status in {"render_failure", "batch_error"}:
                batch_failures.append(
                    {
                        "filename": filename,
                        "status": status,
                        "reason": details.get("failure_reason", details.get("reason", "unknown")),
                        "details": details.get("params_snapshot", details.get("details", "")),
                        "log_file": os.path.basename(log_file),
                    }
                )
                print(f"[WARN] {filename}: Fehler protokolliert, Batchlauf wird fortgesetzt ({status}).")
                return None, True
            if status == "semantic_mismatch":
                batch_failures.append(
                    {
                        "filename": filename,
                        "status": status,
                        "reason": "semantic_mismatch",
                        "details": details.get("issue", ""),
                        "log_file": os.path.basename(log_file),
                    }
                )
                print(f"[WARN] {filename}: Semantischer Fehlmatch, Batchlauf stoppt nach diesem Fehler.")
                return None, True
            return None, False

        _base, _desc, params, best_iter, best_error = res
        details = _read_validation_log_details(log_file)
        img = cv2.imread(image_path)
        pixel_count = 1.0
        width = 0
        height = 0
        mean_delta2 = float("inf")
        std_delta2 = float("inf")
        if img is not None:
            height, width = img.shape[:2]
            pixel_count = float(max(1, width * height))
            svg_path = os.path.join(svg_out_dir, f"{os.path.splitext(filename)[0]}.svg")
            if os.path.exists(svg_path):
                try:
                    with open(svg_path, "r", encoding="utf-8") as f:
                        svg_content = f.read()
                except OSError:
                    svg_content = ""
                if svg_content:
                    rendered = Action.render_svg_to_numpy(svg_content, width, height)
                    mean_delta2, std_delta2 = Action.calculate_delta2_stats(img, rendered)

        return {
            "filename": filename,
            "params": params,
            "best_iter": int(best_iter),
            "best_error": float(best_error),
            "convergence": str(details.get("convergence", "")).strip().lower(),
            "error_per_pixel": float(best_error) / pixel_count,
            "mean_delta2": float(mean_delta2),
            "std_delta2": float(std_delta2),
            "w": int(width),
            "h": int(height),
            "base": get_base_name_from_file(os.path.splitext(filename)[0]).upper(),
            "variant": os.path.splitext(filename)[0].upper(),
        }, False

    # Initial conversion pass for all forms.
    for filename in process_files:
        row, failed = _convert_one(filename, iteration_budget=base_iterations, badge_rounds=6)
        if failed:
            stop_after_failure = True
            break
        if row is None:
            continue

        donor_rows = [
            prev
            for key, prev in result_map.items()
            if key != filename and math.isfinite(float(prev.get("error_per_pixel", float("inf"))))
        ]
        donor_rows.extend(prev for prev in existing_donor_rows if str(prev.get("filename", "")) != filename)
        if donor_rows:
            transferred, _detail = _try_template_transfer(
                target_row=row,
                donor_rows=donor_rows,
                folder_path=folder_path,
                svg_out_dir=svg_out_dir,
                diff_out_dir=diff_out_dir,
                rng=rng,
            )
            if transferred is not None and float(transferred.get("error_per_pixel", float("inf"))) + 1e-9 < float(row.get("error_per_pixel", float("inf"))):
                row = transferred

        result_map[filename] = row

    current_rows = [
        row
        for row in result_map.values()
        if math.isfinite(float(row.get("error_per_pixel", float("inf"))))
    ]
    ranked_rows = sorted(current_rows, key=_quality_sort_key)
    first_cut = max(1, len(ranked_rows) // 3) if ranked_rows else 0
    initial_top_tercile = ranked_rows[:first_cut]
    initial_threshold = float(initial_top_tercile[-1]["error_per_pixel"]) if initial_top_tercile else float("inf")

    successful_threshold = _compute_successful_conversions_error_threshold(current_rows)
    threshold_source = "successful-conversions-mean-plus-2std"
    if not math.isfinite(successful_threshold):
        successful_threshold = initial_threshold
        threshold_source = "initial-first-tercile"

    cfg = _load_quality_config(reports_out_dir)
    allowed_error_pp = successful_threshold
    cfg_value = cfg.get("allowed_error_per_pixel")
    if cfg_value is not None:
        try:
            allowed_error_pp = max(0.0, float(cfg_value))
            threshold_source = "manual-config"
        except (TypeError, ValueError):
            allowed_error_pp = successful_threshold

    # Global policy: do not freeze individual variants. Every quality pass keeps
    # all variants eligible so each run can re-evaluate with stochastic search
    # while still converging by only accepting strict improvements.
    skip_variants: set[str] = set()

    _write_quality_config(
        reports_out_dir,
        allowed_error_per_pixel=allowed_error_pp,
        skipped_variants=sorted(v for v in skip_variants if v),
        source=threshold_source,
    )

    # Iteratively refine unresolved quality cases while preserving all already
    # successful outputs (replace only when strictly better).
    strategy_logs: list[dict[str, object]] = []
    for pass_idx in range(1, max_quality_passes + 1):
        if stop_after_failure:
            break
        Action.STOCHASTIC_SEED_OFFSET = pass_idx
        current_rows = [
            row
            for row in result_map.values()
            if math.isfinite(float(row.get("error_per_pixel", float("inf"))))
        ]
        candidates = _select_open_quality_cases(
            current_rows,
            allowed_error_per_pixel=allowed_error_pp,
            skip_variants=skip_variants,
        )
        # Fallback to the historical selection when no explicit open set exists
        # (e.g. without threshold config).
        if not candidates:
            candidates = _select_middle_lower_tercile(current_rows)
        if not candidates:
            break

        improved_in_pass = False
        iteration_budget, badge_rounds = _iteration_strategy_for_pass(pass_idx, base_iterations)
        if len(candidates) > 1:
            rng.shuffle(candidates)
        for row in candidates:
            filename = str(row["filename"])
            adaptive_iteration_budget = _adaptive_iteration_budget_for_quality_row(row, iteration_budget)
            new_row, failed = _convert_one(filename, iteration_budget=adaptive_iteration_budget, badge_rounds=badge_rounds)
            if failed:
                stop_after_failure = True
                break
            if new_row is None:
                continue

            improved, decision, prev_error_pp, new_error_pp, prev_mean_delta2, new_mean_delta2 = _evaluate_quality_pass_candidate(
                row,
                new_row,
            )
            if improved:
                result_map[filename] = new_row
                improved_in_pass = True

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

        # Stop as soon as a full pass yields no strict improvement.
        if stop_after_failure or not improved_in_pass:
            break

    _write_quality_pass_report(reports_out_dir, quality_logs)
    _write_batch_failure_summary(reports_out_dir, batch_failures)
    if strategy_logs:
        strategy_path = os.path.join(reports_out_dir, "strategy_switch_template_transfers.csv")
        with open(strategy_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([
                "filename",
                "donor_variant",
                "rotation_deg",
                "scale",
                "old_error_per_pixel",
                "new_error_per_pixel",
            ])
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
    generated_overviews = generateConversionOverviews(diff_out_dir, svg_out_dir, reports_out_dir)
    if generated_overviews:
        print(
            "[INFO] Übersichts-Kacheln erzeugt: "
            + ", ".join(f"{key}={path}" for key, path in sorted(generated_overviews.items()))
        )

    Action.STOCHASTIC_SEED_OFFSET = 0
    Action.STOCHASTIC_RUN_SEED = 0
    return out_root
