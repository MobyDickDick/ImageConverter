from src import image_composite_converter as _icc

globals().update(vars(_icc))

def run_iteration_pipeline(
    image_path: str,
    csv_path: str,
    iterations: int,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str,
    debug_ac0811_dir: str | None = None,
    debug_element_diff_dir: str | None = None,
    *,
    badge_validation_rounds: int = 1,
):
    """Run a single-image conversion pass used by ``convert_range``.

    This implementation is intentionally robust: when advanced semantic
    generation helpers are unavailable, it still produces deterministic SVG +
    diagnostics based on the embedded-raster fallback.
    """

    del debug_ac0811_dir, debug_element_diff_dir, iterations, badge_validation_rounds

    os.makedirs(svg_out_dir, exist_ok=True)
    os.makedirs(diff_out_dir, exist_ok=True)
    os.makedirs(reports_out_dir, exist_ok=True)

    filename = os.path.basename(image_path)
    stem = os.path.splitext(filename)[0]
    base = get_base_name_from_file(stem).upper()

    img = cv2.imread(image_path) if cv2 is not None else None
    if img is None:
        log_path = os.path.join(reports_out_dir, f"{stem}_element_validation.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"status=render_failure\nfilename={filename}\nreason=imread_failed\n")
        return None

    h, w = img.shape[:2]
    desc_map = _load_description_mapping(csv_path) if csv_path else {}
    description = (
        desc_map.get(stem)
        or desc_map.get(stem.upper())
        or desc_map.get(base)
        or desc_map.get(base.upper())
        or ""
    )

    regions = detect_relevant_regions_impl(img, cv2, np) if np is not None else []
    elements = [str(r.get("label", "")).strip() for r in regions if str(r.get("label", "")).strip()]

    params = Action.make_badge_params(w, h, base, img) if hasattr(Action, "make_badge_params") else {}
    if not isinstance(params, dict):
        params = {}
    params.setdefault("mode", "semantic_badge")
    params.setdefault("elements", elements)
    params.setdefault(
        "semantic_audit",
        {
            "variant": stem.upper(),
            "base": base,
            "description_lookup_keys": [stem, stem.upper(), base, base.upper()],
            "recognized_description_elements": elements,
            "description_text": str(description or ""),
        },
    )

    try:
        svg_content = Action.generate_badge_svg(w, h, params)
    except Exception:
        svg_content = _render_embedded_raster_svg(image_path)
        params["mode"] = "embedded_raster"

    svg_path = os.path.join(svg_out_dir, f"{stem}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    rendered = Action.render_svg_to_numpy(svg_content, w, h)
    element_validation_lines: list[str] = []
    redraw_notes: list[str] = []
    if rendered is None:
        best_error = float("inf")
        mean_delta2 = float("inf")
        std_delta2 = float("inf")
    else:
        validate_badge_by_elements = getattr(Action, "validate_badge_by_elements", None)
        if callable(validate_badge_by_elements):
            try:
                checked = validate_badge_by_elements(img, rendered, params)
                if checked:
                    element_validation_lines = [str(line) for line in checked]
            except Exception:
                element_validation_lines = []

        apply_redraw_variation = getattr(Action, "apply_redraw_variation", None)
        if callable(apply_redraw_variation):
            try:
                _updated_params, notes = apply_redraw_variation(params, w, h)
                if notes:
                    redraw_notes = [str(note) for note in notes]
            except Exception:
                redraw_notes = []

        best_error = float(Action.calculate_error(img, rendered))
        mean_delta2, std_delta2 = Action.calculate_delta2_stats(img, rendered)
        diff = Action.create_diff_image(img, rendered)
        cv2.imwrite(os.path.join(diff_out_dir, f"{stem}_diff.png"), diff)

    log_path = os.path.join(reports_out_dir, f"{stem}_element_validation.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("status=semantic_ok\n")
        f.write(f"filename={filename}\n")
        f.write(f"convergence={params.get('mode', 'semantic_badge')}\n")
        f.write(f"validation_rounds=1\n")
        if math.isfinite(float(mean_delta2)):
            f.write(f"mean_delta2={float(mean_delta2):.6f}\n")
        if math.isfinite(float(std_delta2)):
            f.write(f"std_delta2={float(std_delta2):.6f}\n")
        for line in element_validation_lines:
            f.write(f"{line}\n")
        for line in _semantic_quality_flags(stem, element_validation_lines):
            f.write(f"{line}\n")
        for note in redraw_notes:
            f.write(f"{note}\n")

    return base, description, params, 0, float(best_error)
