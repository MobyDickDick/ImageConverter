                    " | ".join(str(value) for value in row.get("description_lookup_keys", [])),
                    " | ".join(str(value) for value in row.get("recognized_description_elements", [])),
                    row.get("description_text", ""),
                    " | ".join(str(value) for value in row.get("derived_elements", [])),
                    " > ".join(str(value) for value in row.get("semantic_priority_order", [])),
                    " | ".join(str(value) for value in row.get("semantic_conflicts", [])),
                    row.get("status", ""),
                    row.get("mismatch_reason", ""),
                ]
            )

    json_path = os.path.join(reports_out_dir, "semantic_audit_ac0811_ac0814.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_rows, f, ensure_ascii=False, indent=2)


def _diff_output_dir(output_root: str) -> str:
    return os.path.join(output_root, "diff_pngs")


def _reports_output_dir(output_root: str) -> str:
    return os.path.join(output_root, "reports")


def _is_semantic_template_variant(base_name: str, params: dict[str, object] | None = None) -> bool:
    """Return whether an existing converted SVG should participate as semantic donor."""
    normalized = str(get_base_name_from_file(base_name or "")).upper()
    if not normalized:
        return False
    if normalized.startswith("AC08") or normalized in {"AR0100"}:
        return True
    if isinstance(params, dict) and str(params.get("mode", "")).lower() == "semantic_badge":
        return True
    return False


def _load_existing_conversion_rows(output_root: str, folder_path: str) -> list[dict[str, object]]:
    """Load previously converted variants so they can act as donor templates.

    This lets an earlier conversion batch (for example the already converted
    ``AC08*`` symbols) improve later runs without requiring a fresh full pass.
    """
    reports_path = Path(_reports_output_dir(output_root)) / "Iteration_Log.csv"
    svg_out_dir = Path(_converted_svg_output_dir(output_root))
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

                geometry = _read_svg_geometry(str(svg_path))
                if geometry is None:
                    continue
                w, h, params = geometry
                base = get_base_name_from_file(variant).upper()
                if _is_semantic_template_variant(base, params):
                    params["mode"] = "semantic_badge"

                error_per_pixel_raw = str(raw_row.get("FehlerProPixel", "")).strip().replace(",", ".")
                diff_score_raw = str(raw_row.get("Diff-Score", "")).strip().replace(",", ".")
                best_iter_raw = str(raw_row.get("Beste Iteration", "")).strip()
                image_path = Path(folder_path) / filename
                if image_path.exists():
                    try:
                        width, height = _sniff_raster_size(image_path)
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
