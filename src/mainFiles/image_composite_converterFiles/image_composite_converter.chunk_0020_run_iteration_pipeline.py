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

    ref = Reflection(perc.raw_desc)
    desc, params = ref.parse_description(perc.base_name, filename)
    semantic_audit_targets = {"AC0811", "AC0812", "AC0813", "AC0814"}
    semantic_audit_row: dict[str, object] | None = None
    if get_base_name_from_file(perc.base_name).upper() in semantic_audit_targets:
        semantic_audit_row = _semantic_audit_record(
            base_name=perc.base_name,
            filename=filename,
            description_fragments=list(params.get("description_fragments", [])),
            semantic_elements=list(params.get("elements", [])),
            status="semantic_pending",
            semantic_priority_order=list(params.get("semantic_priority_order", [])),
            semantic_conflicts=list(params.get("semantic_conflicts", [])),
            semantic_sources=dict(params.get("semantic_sources", {})),
        )

    if not desc.strip() and params["mode"] != "semantic_badge":
        print("  -> Überspringe Bild, da keine begleitende textliche Beschreibung vorliegt.")
        return None

    print(f"\n--- Verarbeite {filename} ---")
    elements = ", ".join(params["elements"]) if params["elements"] else "Kein Compositing-Befehl gefunden"
    print(f"Befehl erkannt: {elements}")

    os.makedirs(svg_out_dir, exist_ok=True)
    os.makedirs(diff_out_dir, exist_ok=True)
    if reports_out_dir:
        os.makedirs(reports_out_dir, exist_ok=True)

    base = os.path.splitext(filename)[0]
    log_path = None
    if reports_out_dir:
        log_path = os.path.join(reports_out_dir, f"{base}_element_validation.log")

    def _write_validation_log(lines: list[str]) -> None:
        if not log_path:
            return
        payload = [
            (
                "run-meta: "
                f"run_seed={int(Action.STOCHASTIC_RUN_SEED)} "
                f"pass_seed_offset={int(Action.STOCHASTIC_SEED_OFFSET)} "
                f"nonce_ns={time.time_ns()}"
            )
        ]
        payload.extend(str(line) for line in lines)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(payload).rstrip() + "\n")

    def _params_snapshot(snapshot: dict[str, object]) -> str:
        return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, default=str)

    def _record_render_failure(reason: str, *, svg_content: str | None = None, params_snapshot: dict[str, object] | None = None) -> None:
        if svg_content:
            _write_attempt_artifacts(svg_content, failed=True)
        lines = [
            "status=render_failure",
            f"failure_reason={reason}",
            f"filename={filename}",
        ]
        if svg_content:
            lines.append(f"best_attempt_svg={base}_failed.svg")
        if params_snapshot is not None:
            lines.append("params_snapshot=" + _params_snapshot(params_snapshot))
        _write_validation_log(lines)

    def _write_attempt_artifacts(svg_content: str, rendered_img=None, diff_img=None, *, failed: bool = False) -> None:
        suffix = "_failed" if failed else ""
        svg_path = os.path.join(svg_out_dir, f"{base}{suffix}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        # Failed attempts are tracked in logs/leaderboard but should not emit
        # additional diff artifacts.
        if failed:
            return

        render = rendered_img
        if render is None:
            render = Action.render_svg_to_numpy(svg_content, w, h)
        if render is None:
            return
        diff = diff_img if diff_img is not None else Action.create_diff_image(perc.img, render)
        cv2.imwrite(os.path.join(diff_out_dir, f"{base}{suffix}_diff.png"), diff)

    if params["mode"] == "semantic_badge":
        badge_params = Action.make_badge_params(w, h, perc.base_name, perc.img)
        if badge_params is None:
            return None
        # Persist source raster dimensions so variant-specific finalizers can
        # enforce width/height-relative geometry rules reliably.
        badge_params.setdefault("width", float(w))
        badge_params.setdefault("height", float(h))
        badge_overrides = params.get("badge_overrides")
        if isinstance(badge_overrides, dict):
            badge_params.update(badge_overrides)

        semantic_issues = Action.validate_semantic_description_alignment(
            perc.img,
            list(params.get("elements", [])),
            badge_params,
        )
        if semantic_issues:
            failed_svg = Action.generate_badge_svg(w, h, badge_params)
            _write_attempt_artifacts(failed_svg, failed=True)
            structural = Action._detect_semantic_primitives(perc.img, badge_params)
            connector_orientation = str(structural.get("connector_orientation", "unknown"))
            circle_source = str(structural.get("circle_detection_source", "unknown"))
            connector_debug_line = (
                "semantic_connector_classification="
                f"{connector_orientation};"
                f"circle_source={circle_source};"
                f"horizontal_candidates={int(structural.get('horizontal_line_candidates', 0) or 0)};"
                f"vertical_candidates={int(structural.get('vertical_line_candidates', 0) or 0)}"
            )
            print("[ERROR] Semantik-Abgleich fehlgeschlagen:")
            print(f"  - {connector_debug_line}")
            for issue in semantic_issues:
                print(f"  - {issue}")
            if semantic_audit_row is not None:
                semantic_audit_row = _semantic_audit_record(
                    base_name=perc.base_name,
                    filename=filename,
                    description_fragments=list(params.get("description_fragments", [])),
                    semantic_elements=list(params.get("elements", [])),
                    status="semantic_mismatch",
                    mismatch_reasons=semantic_issues,
                    semantic_priority_order=list(params.get("semantic_priority_order", [])),
                    semantic_conflicts=list(params.get("semantic_conflicts", [])),
                    semantic_sources=dict(params.get("semantic_sources", {})),
                )
            _write_validation_log(
                [
                    "status=semantic_mismatch",
                    f"best_attempt_svg={base}_failed.svg",
                    connector_debug_line,
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
                            f"semantic_audit_mismatch_reason={semantic_audit_row.get('mismatch_reason', '')}",
                        ]
                        if semantic_audit_row is not None
                        else []
                    ),
                    *[f"issue={issue}" for issue in semantic_issues],
                ]
            )
            return None

        validation_logs: list[str] = []
        debug_dir = None
        if debug_element_diff_dir:
            debug_dir = os.path.join(debug_element_diff_dir, os.path.splitext(filename)[0])
            os.makedirs(debug_dir, exist_ok=True)
        elif debug_ac0811_dir and perc.base_name.upper() == "AC0811":
            debug_dir = os.path.join(debug_ac0811_dir, os.path.splitext(filename)[0])
            os.makedirs(debug_dir, exist_ok=True)
        if not bool(badge_params.get("draw_text", False)):
            validation_logs.append("semantic-guard: Text bewusst deaktiviert (plain-ring Familie ohne Buchstabe).")
        else:
            validation_logs.append(
                "semantic-guard: Textmodus aktiv ("
                + str(badge_params.get("text_mode", "unknown"))
                + ")."
            )
        validation_logs.extend(
            Action.validate_badge_by_elements(
            perc.img,
            badge_params,
            max_rounds=max(1, int(badge_validation_rounds)),
            debug_out_dir=debug_dir,
            )
        )
        badge_params = Action._enforce_semantic_connector_expectation(
            perc.base_name,
            list(params.get("elements", [])),
            badge_params,
            w,
            h,
        )
        badge_params, redraw_variation_logs = Action.apply_redraw_variation(badge_params, w, h)
        if badge_params.get("arm_enabled"):
            validation_logs.append(
                "semantic-guard: Erwartete Arm-Geometrie bestätigt/wiederhergestellt (z.B. AC0812 links)."
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
            best_diff = Action.create_diff_image(perc.img, svg_rendered)

        previous_error = error

        if (i + 1) >= min_plateau_iterations and plateau_streak >= plateau_patience:
            print(
                "  -> Früher Abbruch: Diff-Fehler blieb "
                f"{plateau_streak + 1} Iterationen innerhalb ±{plateau_tolerance:.0e}"
            )
            stop_reason = "plateau"
            break

    print(f"-> Bester Match in Iteration {best_iter} (Fehler auf {best_error:.2f} reduziert)")
    if stop_reason == "plateau":
        if best_iter <= 1:
            print("-> Konvergenzdiagnose: Plateau ohne messbare Verbesserung (Parameterraum ggf. erweitern)")
        else:
            print("-> Konvergenzdiagnose: Plateau nach Verbesserung erreicht (lokales Optimum wahrscheinlich)")
    else:
        print("-> Konvergenzdiagnose: Iterationsbudget ausgeschöpft (Optimum unklar, ggf. Suchraum erweitern)")

    if best_svg:
        _write_attempt_artifacts(best_svg, diff_img=best_diff)

    _write_validation_log([
        "status=composite_ok",
        f"convergence={stop_reason}",
        f"best_iter={int(best_iter)}",
        f"best_error={float(best_error):.6f}",
    ])
    return base, desc, params, best_iter, best_error
