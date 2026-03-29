
        has_text = any(bool(dict(row["params"]).get("draw_text", False)) for row in variant_rows)
        has_stem = any(bool(dict(row["params"]).get("stem_enabled", False)) for row in variant_rows)
        has_arm = any(bool(dict(row["params"]).get("arm_enabled", False)) for row in variant_rows)
        has_connector = has_stem or has_arm
        category = "Kreise mit Buchstaben" if has_text and not has_connector else (
            "Kreise ohne Buchstaben" if (not has_text and not has_connector) else (
                "Kellen mit Buchstaben" if has_text else "Kellen ohne Buchstaben"
            )
        )
        variants_joined = "|".join(sorted(str(r["variant"]) for r in variant_rows))
        category_logs.append(f"{base};{category};{variants_joined}")

        sigs = {
            row["variant"]: _normalized_geometry_signature(int(row["w"]), int(row["h"]), dict(row["params"]))
            for row in variant_rows
        }
        max_delta = 0.0
        for i in range(len(variant_rows)):
            for j in range(i + 1, len(variant_rows)):
                vi = str(variant_rows[i]["variant"])
                vj = str(variant_rows[j]["variant"])
                max_delta = max(max_delta, _max_signature_delta(sigs[vi], sigs[vj]))

        # Do not skip families with one badly fitted outlier variant. We still
        # validate every harmonization candidate against raster error before write.

        def _anchor_rank(row: dict[str, object]) -> tuple[int, float]:
            suffix = str(row.get("suffix", ""))
            # Connector families ("Kellen") tend to under-fit large variants
            # when we derive L from M. Prefer L as harmonization anchor so the
            # largest geometry stays authoritative and M/S scale down from it.
            priority = _harmonization_anchor_priority(suffix, prefer_large=has_connector)
            err = float(dict(row["entry"]).get("error", float("inf")))
            return priority, err

        anchor = min(variant_rows, key=_anchor_rank)
        anchor_variant = str(anchor["variant"])
        anchor_w = int(anchor["w"])
        anchor_h = int(anchor["h"])
        anchor_params = dict(anchor["params"])
        family_colors = _family_harmonized_badge_colors(variant_rows)

        for row in variant_rows:
            target_variant = str(row["variant"])
            target_w = int(row["w"])
            target_h = int(row["h"])
            scaled = _scale_badge_params(
                anchor_params,
                anchor_w,
                anchor_h,
                target_w,
                target_h,
                target_variant=target_variant,
            )
            scaled.update(family_colors)
            if scaled.get("draw_text"):
                scaled["text_gray"] = int(family_colors["text_gray"])
            if scaled.get("stem_enabled"):
                scaled["stem_gray"] = int(family_colors["stem_gray"])
            svg = Action.generate_badge_svg(target_w, target_h, scaled)

            target_filename = str(dict(row["entry"])["filename"])
            target_path = os.path.join(folder_path, target_filename)
            target_img = cv2.imread(target_path)
            if target_img is None:
                harmonized_logs.append(f"{base}: {target_variant} übersprungen (Bild fehlt: {target_filename})")
                continue

            rendered = Action.render_svg_to_numpy(svg, target_w, target_h)
            candidate_error = Action.calculate_error(target_img, rendered)
            baseline_error = float(dict(row["entry"]).get("error", float("inf")))
            if candidate_error > baseline_error + 0.25:
                harmonized_logs.append(
                    (
                        f"{base}: {target_variant} nicht harmonisiert "
                        f"(Fehler {candidate_error:.2f} > Basis {baseline_error:.2f})"
                    )
                )
                continue

            with open(os.path.join(svg_out_dir, f"{target_variant}.svg"), "w", encoding="utf-8") as f:
                f.write(svg)
            harmonized_logs.append(
                (
                    f"{base}: {target_variant} aus {anchor_variant} harmonisiert "
                    f"(max_delta={max_delta:.4f}, Fehler {baseline_error:.2f}->{candidate_error:.2f}, "
                    f"Farben fill/stroke={family_colors['fill_gray']}/{family_colors['stroke_gray']})"
                )
            )

    if harmonized_logs:
        with open(os.path.join(reports_out_dir, "variant_harmonization.log"), "w", encoding="utf-8") as f:
            f.write("\n".join(harmonized_logs).rstrip() + "\n")
    if category_logs:
        with open(os.path.join(reports_out_dir, "shape_catalog.csv"), "w", encoding="utf-8") as f:
            f.write("base;category;variants\n")
            f.write("\n".join(category_logs).rstrip() + "\n")


