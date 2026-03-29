                center_now = 0.0
                if plateau:
                    center_now = sum(
                        float(getattr(plateau[0][0], key) if len(plateau) == 1 else (min(float(getattr(cand, key)) for cand, _ in plateau) + max(float(getattr(cand, key)) for cand, _ in plateau)) / 2.0)
                        for key in active_keys
                    ) / max(1, len(active_keys))
                center_shift = abs(center_now - prev_center)
                stability = "stabil" if center_shift <= 0.35 else "dynamisch"
                plateau_rounds.append({"size": len(plateau), "mean_span": mean_span, "center_mean": center_now})
            else:
                center_now = 0.0
                if plateau:
                    center_now = sum(
                        float(getattr(plateau[0][0], key) if len(plateau) == 1 else (min(float(getattr(cand, key)) for cand, _ in plateau) + max(float(getattr(cand, key)) for cand, _ in plateau)) / 2.0)
                        for key in active_keys
                    ) / max(1, len(active_keys))
                plateau_rounds.append({"size": len(plateau), "mean_span": mean_span, "center_mean": center_now})
            for key in active_keys:
                spans[key] = max(0.12, spans[key] * 0.78)
            logs.append(
                f"global-search: Runde {round_idx + 1} best_err={best_err:.3f}, akzeptierte_kandidaten={accepted}, sigma_mittel={sum(spans.values()) / max(1, len(spans)):.3f}"
            )
            logs.append(
                "global-search: near-optimum-plateau "
                f"(runde={round_idx + 1}, punkte={len(plateau)}, epsilon={epsilon:.3f}, "
                f"mittlere_spannweite={mean_span:.3f}, stabilitaet={stability}, "
                f"spannweite={'; '.join(span_labels) if span_labels else 'n/a'})"
            )
            logs.append(
                "global-search: plateau-repräsentant "
                f"(runde={round_idx + 1}, kandidat={representative_source}, err={representative_err:.3f}, "
                f"begründung={representative_reason})"
            )

        if not improved:
            logs.append("global-search: keine relevante Verbesserung")
            return False

        old_values = {key: float(getattr(vector, key)) for key in active_keys}
        new_values = {key: float(getattr(best, key)) for key in active_keys}
        params.update(best.apply_to_params(params))
        delta_labels = [
            f"{key} {old_values[key]:.3f}->{new_values[key]:.3f}"
            for key in active_keys
            if abs(new_values[key] - old_values[key]) >= 0.01
        ]
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, float(params.get("r", 0.0)))
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + float(params.get("r", 0.0))
        Action._log_global_parameter_vector(logs, params, w, h, label="global-search: final")
        logs.append(
            "global-search: übernommen "
            f"(best_err={best_err:.3f}, verbessert={', '.join(delta_labels) if delta_labels else 'keine sichtbare delta-liste'})"
        )
        return True

    @staticmethod
    def _enforce_semantic_connector_expectation(base_name: str, semantic_elements: list[str], params: dict, w: int, h: int) -> dict:
        """Restore mandatory connector geometry for directional semantic badges."""
        normalized_base = get_base_name_from_file(str(base_name)).upper()
        normalized_elements = [str(elem).lower() for elem in (semantic_elements or [])]
        expects_left_arm = any("waagrechter strich links" in elem for elem in normalized_elements)
        expects_right_arm = any("waagrechter strich rechts" in elem for elem in normalized_elements)

        # AC0812/AC0837/AC0882 are directional left-arm families. If noisy element
        # extraction temporarily drops arm flags, regenerate canonical connector geometry
        # from the fitted circle before final SVG serialization.
        if normalized_base in {"AC0812", "AC0837", "AC0882"} or expects_left_arm:
            return Action._enforce_left_arm_badge_geometry(params, w, h)
        if normalized_base in {"AC0810", "AC0814", "AC0834", "AC0838", "AC0839"} or expects_right_arm:
            return Action._enforce_right_arm_badge_geometry(params, w, h)
        return params

    @staticmethod
    def _element_width_key_and_bounds(
        element: str, params: dict, w: int, h: int, img_orig: np.ndarray | None = None
    ) -> tuple[str, float, float] | None:
        lock_strokes = bool(params.get("lock_stroke_widths"))
        min_dim = float(min(w, h))
        if element == "stem" and params.get("stem_enabled"):
            if lock_strokes:
                fixed = float(Action.AC08_STROKE_WIDTH_PX)
                if not bool(params.get("allow_stem_width_tuning", False)):
                    return "stem_width", fixed, fixed
                high = min(
                    float(params.get("stem_width_max", fixed + 1.0)),
                    max(fixed, fixed + float(params.get("stem_width_tuning_px", 1.0))),
                )
                return "stem_width", fixed, max(fixed, high)
            low = max(1.0, float(params.get("stroke_circle", 1.0)) * 0.65)
            high = max(low, min(float(w) * 0.25, float(params.get("stem_width_max", float(w) * 0.25))))
            return "stem_width", low, high
        if element == "arm" and params.get("arm_enabled"):
            if lock_strokes:
                fixed = float(Action.AC08_STROKE_WIDTH_PX)
                return "arm_stroke", fixed, fixed
            low = max(1.0, float(params.get("stroke_circle", 1.0)) * 0.65)
            high = max(low, min(float(min(w, h)) * 0.20, float(params.get("r", min(w, h))) * 0.9))
            return "arm_stroke", low, high
