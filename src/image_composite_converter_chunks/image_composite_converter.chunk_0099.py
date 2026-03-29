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
        generate_conversion_overviews(diff_out_dir, svg_out_dir, reports_out_dir)
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
