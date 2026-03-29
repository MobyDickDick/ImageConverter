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
