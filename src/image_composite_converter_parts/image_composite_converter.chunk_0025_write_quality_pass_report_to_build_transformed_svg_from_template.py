def _write_quality_pass_report(
    reports_out_dir: str,
    pass_rows: list[dict[str, object]],
) -> None:
    if not pass_rows:
        return

    out_path = os.path.join(reports_out_dir, "quality_tercile_passes.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "pass",
            "filename",
            "old_error_per_pixel",
            "new_error_per_pixel",
            "old_mean_delta2",
            "new_mean_delta2",
            "improved",
            "decision",
            "iteration_budget",
            "badge_validation_rounds",
        ])
        for row in pass_rows:
            writer.writerow([
                row["pass"],
                row["filename"],
                f"{float(row['old_error_per_pixel']):.8f}",
                f"{float(row['new_error_per_pixel']):.8f}",
                f"{float(row.get('old_mean_delta2', float('inf'))):.6f}",
                f"{float(row.get('new_mean_delta2', float('inf'))):.6f}",
                "1" if bool(row["improved"]) else "0",
                row.get("decision", "accepted_improvement" if bool(row["improved"]) else "rejected_regression"),
                row["iteration_budget"],
                row["badge_validation_rounds"],
            ])


def _evaluate_quality_pass_candidate(
    old_row: dict[str, object],
    new_row: dict[str, object],
) -> tuple[bool, str, float, float, float, float]:
    """Return whether a quality-pass candidate should replace the previous result.

    The acceptance rule mirrors AC08 task 1.1: keep the new candidate only when
    at least one core quality metric improves (`error_per_pixel` or
    `mean_delta2`). The caller also receives the normalized metrics so reporting
    can use one consistent decision path for stochastic re-runs and fallback
    template transfers.
    """

    prev_error_pp = float(old_row.get("error_per_pixel", float("inf")))
    new_error_pp = float(new_row.get("error_per_pixel", float("inf")))
    prev_mean_delta2 = float(old_row.get("mean_delta2", float("inf")))
    new_mean_delta2 = float(new_row.get("mean_delta2", float("inf")))
    error_improved = new_error_pp + 1e-9 < prev_error_pp
    delta2_improved = new_mean_delta2 + 1e-6 < prev_mean_delta2
    improved = error_improved or delta2_improved
    decision = "accepted_improvement" if improved else "rejected_regression"
    return improved, decision, prev_error_pp, new_error_pp, prev_mean_delta2, new_mean_delta2


def _extract_svg_inner(svg_text: str) -> str:
    match = re.search(r"<svg[^>]*>(.*)</svg>", svg_text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return svg_text


def _build_transformed_svg_from_template(
    template_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
    scale: float,
) -> str:
    inner = _extract_svg_inner(template_svg_text)
    # Keep donor stroke widths visually stable when trying scale-based transfers.
    # This mirrors the "M->S/L while preserving line thickness" workflow that is
    # often needed for noisy small/large bitmap variants.
    inner = re.sub(
        r"<(circle|ellipse|line|path|polygon|polyline|rect)\\b([^>]*)>",
        lambda m: (
            f"<{m.group(1)}{m.group(2)}>"
            if "vector-effect=" in m.group(2)
            else f"<{m.group(1)}{m.group(2)} vector-effect=\"non-scaling-stroke\">"
        ),
        inner,
        flags=re.IGNORECASE,
    )
    cx = float(target_w) / 2.0
    cy = float(target_h) / 2.0
    return (
        f'<svg width="{target_w}" height="{target_h}" viewBox="0 0 {target_w} {target_h}" '
        'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">\n'
        f'  <g transform="translate({cx:.3f} {cy:.3f}) rotate({int(rotation_deg)}) scale({float(scale):.4f}) '
        f'translate({-cx:.3f} {-cy:.3f})">\n'
        f"{inner}\n"
        "  </g>\n"
        "</svg>"
    )


