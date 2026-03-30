from src import image_composite_converter as _icc

globals().update(vars(_icc))

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

        img_orig = cv2.imread(image_path)
        if img_orig is None:
            metrics.append(row)
            continue
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        rendered = Action.render_svg_to_numpy(svg_content, img_orig.shape[1], img_orig.shape[0])
        if rendered is None:
            metrics.append(row)
            continue

        diff = img_orig.astype(np.float32) - rendered.astype(np.float32)
        delta2 = np.sum(diff * diff, axis=2)
        row['pixel_count'] = int(delta2.shape[0] * delta2.shape[1])
        row['total_delta2'] = float(np.sum(delta2))
        row['mean_delta2'] = float(np.mean(delta2))
        row['std_delta2'] = float(np.std(delta2))
        metrics.append(row)

    metrics.sort(key=lambda item: str(item.get('variant', '')))
    return metrics
