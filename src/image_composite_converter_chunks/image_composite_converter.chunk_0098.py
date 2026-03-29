                        candidate_params = _semantic_transfer_badge_params(
                            dict(donor_geom_params),
                            dict(target_geom_params),
                            target_w=w,
                            target_h=h,
                            rotation_deg=rotation,
                            scale=float(scale),
                        )
                        try:
                            candidate_svg = Action.generate_badge_svg(w, h, candidate_params)
                            rendered = Action.render_svg_to_numpy(candidate_svg, w, h)
                        except Exception:
                            continue
                        error = Action.calculate_error(img_orig, rendered)
                        error_pp = float(error) / pixel_count
                        if error_pp + 1e-9 < best_error_pp:
                            best_error = float(error)
                            best_error_pp = error_pp
                            best_svg = candidate_svg
                            best_donor = donor_variant
                            best_rotation = rotation
                            best_scale = float(scale)

        if target_is_semantic:
            # Semantic badges encode meaning in connector/text geometry.
            # Generic donor SVG transforms can remove those semantics.
            continue

        for rotation, scale in _template_transfer_transform_candidates(
            target_variant,
            donor_variant,
            estimated_scale_by_rotation=estimated_scales,
        ):
            candidate_svg = _build_transformed_svg_from_template(
                donor_svg_text,
                w,
                h,
                rotation_deg=rotation,
                scale=scale,
            )
            rendered = Action.render_svg_to_numpy(candidate_svg, w, h)
            error = Action.calculate_error(img_orig, rendered)
            error_pp = float(error) / pixel_count
            if error_pp + 1e-9 < best_error_pp:
                best_error = float(error)
                best_error_pp = error_pp
                best_svg = candidate_svg
                best_donor = donor_variant
                best_rotation = rotation
                best_scale = scale

    if best_svg is None:
        return None, None

    stem = os.path.splitext(filename)[0]
    svg_path = os.path.join(svg_out_dir, f"{stem}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(best_svg)

    rendered = Action.render_svg_to_numpy(best_svg, w, h)
    mean_delta2 = float(target_row.get("mean_delta2", float("inf")))
    std_delta2 = float(target_row.get("std_delta2", float("inf")))
    if rendered is not None:
        diff = Action.create_diff_image(img_orig, rendered)
        cv2.imwrite(os.path.join(diff_out_dir, f"{stem}_diff.png"), diff)
        try:
            mean_delta2, std_delta2 = Action.calculate_delta2_stats(img_orig, rendered)
        except Exception:
            mean_delta2 = float(target_row.get("mean_delta2", float("inf")))
            std_delta2 = float(target_row.get("std_delta2", float("inf")))

    updated_row = dict(target_row)
    updated_row["best_error"] = float(best_error)
    updated_row["error_per_pixel"] = float(best_error_pp)
    updated_row["mean_delta2"] = float(mean_delta2)
    updated_row["std_delta2"] = float(std_delta2)

    detail = {
        "filename": filename,
        "donor_variant": best_donor,
        "rotation_deg": int(best_rotation),
        "scale": float(best_scale),
        "old_error_per_pixel": float(prev_error_pp),
        "new_error_per_pixel": float(best_error_pp),
        "old_mean_delta2": float(target_row.get("mean_delta2", float("inf"))),
        "new_mean_delta2": float(mean_delta2),
    }
    return updated_row, detail


def convert_range(
    folder_path: str,
    csv_path: str,
    iterations: int,
    start_ref: str = "AR0102",
    end_ref: str = "AR0104",
    debug_ac0811_dir: str | None = None,
    debug_element_diff_dir: str | None = None,
    output_root: str | None = None,
    selected_variants: set[str] | None = None,
