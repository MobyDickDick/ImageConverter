            )
        quality_flags = _semantic_quality_flags(perc.base_name, validation_logs)
        if semantic_audit_row is not None:
            semantic_audit_row = _semantic_audit_record(
                base_name=perc.base_name,
                filename=filename,
                description_fragments=list(params.get("description_fragments", [])),
                semantic_elements=list(params.get("elements", [])),
                status="semantic_ok",
                semantic_priority_order=list(params.get("semantic_priority_order", [])),
                semantic_conflicts=list(params.get("semantic_conflicts", [])),
                semantic_sources=dict(params.get("semantic_sources", {})),
            )
        _write_validation_log(
            [
                "status=semantic_ok",
                *(
                    [
                        f"semantic_audit_status={semantic_audit_row.get('status', '')}",
                        "semantic_audit_lookup_keys=" + " | ".join(
                            str(value) for value in semantic_audit_row.get("description_lookup_keys", [])
                        ),
                        "semantic_audit_recognized_description_elements=" + " | ".join(
                            str(value) for value in semantic_audit_row.get("recognized_description_elements", [])
                        ),
                        "semantic_audit_derived_elements=" + " | ".join(
                            str(value) for value in semantic_audit_row.get("derived_elements", [])
                        ),
                        "semantic_audit_priority_order=" + " > ".join(
                            str(value) for value in semantic_audit_row.get("semantic_priority_order", [])
                        ),
                        "semantic_audit_conflicts=" + " | ".join(
                            str(value) for value in semantic_audit_row.get("semantic_conflicts", [])
                        ),
                    ]
                    if semantic_audit_row is not None
                    else []
                ),
                *quality_flags,
                *redraw_variation_logs,
                *validation_logs,
            ]
        )

        svg_content = Action.generate_badge_svg(w, h, badge_params)
        svg_rendered = Action.render_svg_to_numpy(svg_content, w, h)
        if svg_rendered is None:
            _record_render_failure(
                "semantic_badge_final_render_failed",
                svg_content=svg_content,
                params_snapshot=badge_params,
            )
            return None
        _write_attempt_artifacts(svg_content, svg_rendered)
        if semantic_audit_row is not None:
            params = copy.deepcopy(params)
            params["semantic_audit"] = semantic_audit_row
        return base, desc, params, 1, Action.calculate_error(perc.img, svg_rendered)

    if params["mode"] != "composite":
        print("  -> Überspringe Bild, da keine Zerschneide-Anweisung (Compositing) im Text vorliegt.")
        _write_validation_log(["status=skipped_non_composite"])
        return None

    best_error = float("inf")
    best_svg = ""
    best_diff = None
    best_iter = 0

    epsilon_factors = np.linspace(0.05, 0.0005, max_iterations)
    plateau_tolerance = 1e-6
    min_plateau_iterations = min(max_iterations, 12)
    plateau_patience = min(max_iterations, max(8, max_iterations // 6))
    plateau_streak = 0
    previous_error: float | None = None
    stop_reason = "max_iterations"
    for i, eps in enumerate(epsilon_factors):
        svg_content = Action.generate_composite_svg(w, h, params, folder_path, float(eps))

        svg_rendered = Action.render_svg_to_numpy(svg_content, w, h)
        if svg_rendered is None:
            _record_render_failure(
                "composite_iteration_render_failed",
                svg_content=svg_content,
                params_snapshot=params,
            )
            return None
        error = Action.calculate_error(perc.img, svg_rendered)

        if previous_error is not None and abs(error - previous_error) <= plateau_tolerance:
            plateau_streak += 1
        else:
            plateau_streak = 0

        improved = error < best_error
        if improved or i == 0 or (i + 1) == max_iterations:
            print(f"  [Iter {i+1}/{max_iterations}] Epsilon={eps:.4f} -> Diff-Fehler: {error:.2f}")

        if improved:
            best_error, best_svg, best_iter = error, svg_content, i + 1
