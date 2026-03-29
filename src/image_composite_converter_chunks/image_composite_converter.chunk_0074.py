
        return changed_any

    @staticmethod
    def _refine_stem_geometry_from_masks(params: dict, mask_orig: np.ndarray, mask_svg: np.ndarray, w: int) -> tuple[bool, str | None]:
        """Refine stem width/position when validation detects a geometric mismatch."""
        orig_bbox = Action._mask_bbox(mask_orig)
        svg_bbox = Action._mask_bbox(mask_svg)
        if orig_bbox is None or svg_bbox is None:
            return False, None

        ox1, _oy1, ox2, _oy2 = orig_bbox
        sx1, _sy1, sx2, _sy2 = svg_bbox
        orig_w = max(1.0, (ox2 - ox1) + 1.0)
        svg_w = max(1.0, (sx2 - sx1) + 1.0)
        ratio = svg_w / orig_w

        expected_cx = float(params.get("cx", (ox1 + ox2) / 2.0))
        stroke = float(params.get("stroke_circle", 1.0))
        # Skip a small band right below the circle edge so anti-aliased ring/fill
        # pixels do not inflate stem width estimation.
        y_start = float(params.get("stem_top", 0.0)) + max(1.0, stroke * 2.0)
        y_end = float(params.get("stem_bottom", mask_orig.shape[0]))
        est = Action._estimate_vertical_stem_from_mask(mask_orig, expected_cx, int(y_start), int(y_end))

        if est is not None:
            est_cx, est_width = est
            min_w = max(1.0, float(params.get("stroke_circle", 1.0)) * 0.70)
            max_w = max(
                min_w,
                min(
                    float(params.get("stem_width_max", float(w) * 0.18)),
                    min(float(w) * 0.18, float(params.get("r", 1.0)) * 0.80),
                ),
            )
            target_width = max(min_w, min(est_width, max_w))
            if bool(params.get("lock_stem_center_to_circle", False)):
                circle_cx = float(params.get("cx", est_cx))
                max_offset = float(params.get("stem_center_lock_max_offset", max(0.35, target_width * 0.75)))
                target_cx = float(Action._clip_scalar(est_cx, circle_cx - max_offset, circle_cx + max_offset))
            else:
                target_cx = est_cx
            estimate_mode = "iter"
        else:
            if 0.95 <= ratio <= 1.05:
                return False, None
            target_width = float(params.get("stem_width", svg_w)) * (orig_w / svg_w)
            stem_width_cap = float(params.get("stem_width_max", float(w) * 0.20))
            target_width = max(1.0, min(target_width, min(float(w) * 0.20, stem_width_cap)))
            target_cx = (ox1 + ox2) / 2.0
            estimate_mode = "bbox"

        old_width = float(params.get("stem_width", svg_w))
        width_delta = abs(target_width - old_width)
        ratio_after = target_width / max(1.0, orig_w)

        if width_delta < 0.05 and 0.90 <= ratio_after <= 1.12:
            return False, None

        stem_width_cap = float(params.get("stem_width_max", float(w) * 0.20))
        target_width = min(target_width, stem_width_cap)
        target_width = Action._snap_int_px(target_width, minimum=1.0)
        old_x = float(params.get("stem_x", 0.0))
        old_w = float(params.get("stem_width", 1.0))
        new_x = Action._snap_half(max(0.0, min(float(w) - target_width, target_cx - (target_width / 2.0))))
        if abs(target_width - old_w) < 0.05 and abs(new_x - old_x) < 0.05:
            return False, None
        params["stem_width"] = target_width
        params["stem_x"] = new_x
        return True, (
            f"stem: Breitenkorrektur mode={estimate_mode}, ratio={ratio:.3f}, "
            f"alt={old_width:.3f}, neu={target_width:.3f}"
        )

    @staticmethod
    def _expected_semantic_presence(semantic_elements: list[str]) -> dict[str, bool]:
        normalized = [str(elem).lower() for elem in semantic_elements]
        has_text = any(
            ("kreis + buchstabe" in elem)
            or (("buchstab" in elem) and ("ohne buchstabe" not in elem))
            or ("voc" in elem)
            or ("co_2" in elem)
            or ("co₂" in elem)
            for elem in normalized
        )
        has_circle = any("kreis" in elem for elem in normalized)
        return {
            "circle": has_circle,
            "stem": any("senkrechter strich" in elem for elem in normalized),
            "arm": any("waagrechter strich" in elem for elem in normalized),
            "text": has_text,
        }

    @staticmethod
    def _semantic_presence_mismatches(expected: dict[str, bool], observed: dict[str, bool]) -> list[str]:
        labels = {
            "circle": "Kreis",
            "stem": "senkrechter Strich",
            "arm": "waagrechter Strich",
            "text": "Buchstabe/Text",
