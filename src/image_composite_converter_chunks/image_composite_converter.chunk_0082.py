                    logs.append(
                        "switch_to_fallback_search: deaktiviere Circle-Geometry-Penalty für eine letzte Ausweichrunde"
                    )
                    continue
                logs.append("stopped_due_to_stagnation: keine weitere Parameterbewegung erkennbar")
                break

        if math.isfinite(best_full_err):
            params.clear()
            params.update(best_params)

        for element in elements:
            if element == "text" and not params.get("draw_text", True):
                continue
            mask_orig = Action.extract_badge_element_mask(img_orig, params, element)
            if mask_orig is None:
                continue
            color_changed = Action._optimize_element_color_bracket(img_orig, params, element, mask_orig, logs)
            if color_changed:
                logs.append(f"{element}: Farboptimierung in Abschlussphase angewendet")

        params.update(Action._apply_canonical_badge_colors(params))

        return logs


def _semantic_quality_flags(base_name: str, validation_logs: list[str]) -> list[str]:
    """Derive non-fatal quality markers from semantic element-validation logs.

    Semantic structure checks can pass even when one fitted element is still a
    visually weak match. We keep the conversion successful, but annotate such
    cases in the per-image validation log so downstream review can spot them.
    """

    if get_base_name_from_file(base_name).upper() != "AC0811":
        return []

    error_pattern = re.compile(r"^(circle|stem|arm|text): Fehler=([0-9]+(?:\.[0-9]+)?)$")
    element_errors: dict[str, float] = {}
    for entry in validation_logs:
        match = error_pattern.match(str(entry).strip())
        if not match:
            continue
        element_errors[match.group(1)] = float(match.group(2))

    if not element_errors:
        return []

    highest_element, highest_error = max(element_errors.items(), key=lambda item: item[1])
    elevated = [name for name, value in element_errors.items() if value >= 8.0]

    if highest_error < 10.0 and len(elevated) < 2:
        return []

    markers = [
        "quality=borderline",
        (
            "quality_reason="
            f"semantic_ok_trotz_hohem_elementfehler:{highest_element}={highest_error:.3f}"
        ),
    ]
    if elevated:
        markers.append("quality_elevated_elements=" + ",".join(sorted(elevated)))
    return markers


def run_iteration_pipeline(
    img_path: str,
    csv_path: str,
    max_iterations: int,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str | None = None,
    debug_ac0811_dir: str | None = None,
    debug_element_diff_dir: str | None = None,
    badge_validation_rounds: int = 6,
):
    if cv2 is None or np is None:
        missing = []
        if cv2 is None:
            missing.append("cv2")
        if np is None:
            missing.append("numpy")
        raise RuntimeError(
            "Required image dependencies are missing: " + ", ".join(missing) + ". "
            "Install dependencies before running the conversion pipeline."
        )
    if fitz is None:
        raise RuntimeError(
            "Required SVG renderer dependency is missing: fitz (PyMuPDF). "
            "Install PyMuPDF before running the conversion pipeline."
        )

    folder_path = os.path.dirname(img_path)
    filename = os.path.basename(img_path)

    perc = Perception(img_path, csv_path)
    if perc.img is None:
        return None
    h, w = perc.img.shape[:2]
