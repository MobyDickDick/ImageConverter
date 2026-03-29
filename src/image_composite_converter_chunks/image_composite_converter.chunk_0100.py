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
