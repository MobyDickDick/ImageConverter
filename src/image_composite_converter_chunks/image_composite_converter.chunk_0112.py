        for row in ranking:
            writer.writerow([row["image"], f"{float(row['mean_delta2']):.6f}", f"{float(row['std_delta2']):.6f}"])

    valid = [row for row in ranking if math.isfinite(float(row["mean_delta2"]))]
    count_ok = sum(1 for row in valid if float(row["mean_delta2"]) <= threshold)
    summary_lines = [
        f"images_total={len(valid)}",
        f"threshold_mean_delta2={threshold:.3f}",
        f"images_with_mean_delta2_le_threshold={count_ok}",
    ]
    with open(os.path.join(reports_out_dir, "pixel_delta2_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")


def _load_iteration_log_rows(reports_out_dir: str) -> dict[str, dict[str, str]]:
    """Load Iteration_Log.csv keyed by uppercase filename stem."""
    path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    if not os.path.exists(path):
        return {}

    rows: dict[str, dict[str, str]] = {}
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            filename = str(row.get('Dateiname', '')).strip()
            if not filename:
                continue
            rows[os.path.splitext(filename)[0].upper()] = dict(row)
    return rows


def _find_image_path_by_variant(folder_path: str, variant: str) -> str | None:
    """Return the raster image path for ``variant`` if present."""
    for ext in ('.jpg', '.png', '.bmp', '.gif'):
        candidate = os.path.join(folder_path, f'{variant}{ext}')
        if os.path.exists(candidate):
            return candidate
    return None


def collect_successful_conversion_quality_metrics(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> list[dict[str, object]]:
    """Collect quality metrics for variants listed as successful conversions."""
    if cv2 is None or np is None:
        missing = []
        if cv2 is None:
            missing.append('cv2')
        if np is None:
            missing.append('numpy')
        raise RuntimeError('Required image dependencies are missing: ' + ', '.join(missing))

    variants = [str(v).strip().upper() for v in (successful_variants or SUCCESSFUL_CONVERSIONS) if str(v).strip()]
    iteration_rows = _load_iteration_log_rows(reports_out_dir)
    metrics: list[dict[str, object]] = []
    seen: set[str] = set()
    for variant in variants:
        if variant in seen:
            continue
        seen.add(variant)
        image_path = _find_image_path_by_variant(folder_path, variant)
        svg_path = os.path.join(svg_out_dir, f'{variant}.svg')
        log_path = os.path.join(reports_out_dir, f'{variant}_element_validation.log')

        row: dict[str, object] = {
            'variant': variant,
            'image_found': os.path.exists(image_path) if image_path else False,
            'svg_found': os.path.exists(svg_path),
            'log_found': os.path.exists(log_path),
            'status': '',
            'best_iteration': '',
            'diff_score': float('nan'),
            'error_per_pixel': float('nan'),
            'pixel_count': 0,
            'total_delta2': float('nan'),
            'mean_delta2': float('nan'),
            'std_delta2': float('nan'),
        }

        details = _read_validation_log_details(log_path) if os.path.exists(log_path) else {}
        row['status'] = details.get('status', '')

        iteration = iteration_rows.get(variant, {})
        row['best_iteration'] = str(iteration.get('Beste Iteration', '')).strip()
        try:
            row['diff_score'] = float(str(iteration.get('Diff-Score', '')).strip().replace(',', '.'))
        except ValueError:
            row['diff_score'] = float('nan')
        try:
            row['error_per_pixel'] = float(str(iteration.get('FehlerProPixel', '')).strip().replace(',', '.'))
        except ValueError:
            row['error_per_pixel'] = float('nan')

        if not image_path or not os.path.exists(image_path) or not os.path.exists(svg_path):
            metrics.append(row)
            continue

