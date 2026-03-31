def _loadExistingConversionRows(output_root: str, folder_path: str) -> list[dict[str, object]]:
    """Load previously converted variants so they can act as donor templates.

    This lets an earlier conversion batch (for example the already converted
    ``AC08*`` symbols) improve later runs without requiring a fresh full pass.
    """
    reports_path = Path(_reportsOutputDir(output_root)) / "Iteration_Log.csv"
    svg_out_dir = Path(_convertedSvgOutputDir(output_root))
    if not reports_path.exists() or not svg_out_dir.exists():
        return []

    rows: list[dict[str, object]] = []
    try:
        with reports_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for raw_row in reader:
                filename = str(raw_row.get("Dateiname", "")).strip()
                if not filename:
                    continue

                variant = os.path.splitext(filename)[0].upper()
                svg_path = svg_out_dir / f"{variant}.svg"
                if not svg_path.exists():
                    continue

                geometry = _readSvgGeometry(str(svg_path))
                if geometry is None:
                    continue
                w, h, params = geometry
                base = getBaseNameFromFile(variant).upper()
                if _isSemanticTemplateVariant(base, params):
                    params["mode"] = "semantic_badge"

                error_per_pixel_raw = str(raw_row.get("FehlerProPixel", "")).strip().replace(",", ".")
                diff_score_raw = str(raw_row.get("Diff-Score", "")).strip().replace(",", ".")
                best_iter_raw = str(raw_row.get("Beste Iteration", "")).strip()
                image_path = Path(folder_path) / filename
                if image_path.exists():
                    try:
                        width, height = _sniffRasterSize(image_path)
                        w = int(width)
                        h = int(height)
                    except Exception:
                        pass

                try:
                    error_per_pixel = float(error_per_pixel_raw)
                except ValueError:
                    error_per_pixel = float("inf")
                try:
                    best_error = float(diff_score_raw)
                except ValueError:
                    best_error = float("inf")
                try:
                    best_iter = int(best_iter_raw)
                except ValueError:
                    best_iter = 0

                rows.append(
                    {
                        "filename": filename,
                        "params": params,
                        "best_iter": best_iter,
                        "best_error": best_error,
                        "error_per_pixel": error_per_pixel,
                        "w": int(w),
                        "h": int(h),
                        "base": base,
                        "variant": variant,
                    }
                )
    except OSError:
        return []

    return [
        row
        for row in rows
        if math.isfinite(float(row.get("error_per_pixel", float("inf"))))
    ]
