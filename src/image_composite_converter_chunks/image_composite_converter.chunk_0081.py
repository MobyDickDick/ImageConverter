                # Color fitting is intentionally deferred to the end so
                # geometry convergence is not biased by temporary palette noise.

            global_search_changed = Action._optimize_global_parameter_vector_sampling(
                img_orig,
                params,
                logs,
            )
            if global_search_changed:
                round_changed = True

            full_svg = Action.generate_badge_svg(w, h, params)
            full_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(full_svg, w, h))
            full_err = Action.calculate_error(img_orig, full_render)
            logs.append(f"Runde {round_idx + 1}: Gesamtfehler={full_err:.3f}")
            if math.isfinite(full_err) and full_err < best_full_err:
                best_full_err = full_err
                best_params = copy.deepcopy(params)

            current_round_state = (_stagnation_fingerprint(params), round(float(full_err), 6))
            if previous_round_state is not None:
                same_fingerprint = current_round_state[0] == previous_round_state[0]
                nearly_same_error = abs(current_round_state[1] - previous_round_state[1]) <= 1e-6
                if same_fingerprint and nearly_same_error:
                    logs.append(
                        "stagnation_detected: identischer Parameter-Fingerprint und praktisch unveränderter Gesamtfehler"
                    )
                    adaptive_unlock_applied = Action._activate_ac08_adaptive_locks(
                        params,
                        logs,
                        full_err=full_err,
                        reason="identical_fingerprint",
                    )
                    if adaptive_unlock_applied:
                        previous_round_state = None
                        fallback_search_active = True
                        if round_idx + 1 < max_rounds:
                            logs.append(
                                "switch_to_fallback_search: adaptive family-unlocks aktiviert und Circle-Geometry-Penalty deaktiviert"
                            )
                            continue
                    if not fallback_search_active and round_idx + 1 < max_rounds:
                        Action._release_ac08_adaptive_locks(
                            params,
                            logs,
                            reason="stagnation_same_fingerprint",
                            current_error=full_err,
                        )
                        fallback_search_active = True
                        logs.append(
                            "switch_to_fallback_search: deaktiviere Circle-Geometry-Penalty für eine letzte Ausweichrunde"
                        )
                        previous_round_state = current_round_state
                        continue
                    logs.append("stopped_due_to_stagnation: Validierung vorzeitig beendet")
                    break
            previous_round_state = current_round_state

            if full_err <= 8.0:
                if stop_when_error_below_threshold:
                    logs.append("Gesamtfehler unter Schwellwert, Validierung beendet")
                    break
                logs.append("Gesamtfehler unter Schwellwert, Suche nach besserem Optimum wird fortgesetzt")
            elif round_idx >= 1:
                Action._release_ac08_adaptive_locks(
                    params,
                    logs,
                    reason="high_residual_error",
                    current_error=full_err,
                )

            if round_idx + 1 >= max_rounds:
                break

            if not round_changed:
                adaptive_unlock_applied = Action._activate_ac08_adaptive_locks(
                    params,
                    logs,
                    full_err=full_err,
                    reason="no_geometry_movement",
                )
                if adaptive_unlock_applied:
                    previous_round_state = None
                    fallback_search_active = True
                    if round_idx + 1 < max_rounds:
                        logs.append(
                            "switch_to_fallback_search: adaptive family-unlocks aktiviert und Circle-Geometry-Penalty deaktiviert"
                        )
                        continue
                if not fallback_search_active and round_idx + 1 < max_rounds:
                    Action._release_ac08_adaptive_locks(
                        params,
                        logs,
                        reason="stagnation_no_geometry_change",
                        current_error=full_err,
                    )
                    fallback_search_active = True
                    logs.append(
                        "stagnation_detected: keine relevante Geometrieänderung in der letzten Validierungsrunde"
                    )
