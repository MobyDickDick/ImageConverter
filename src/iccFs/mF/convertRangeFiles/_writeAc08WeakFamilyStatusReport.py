def _writeAc08WeakFamilyStatusReport(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
    ranking_threshold: float = 18.0,
) -> None:
    """Summarize currently weak AC08 families and the mitigation status implemented in code."""
    normalized_variants = sorted({str(variant).strip().upper() for variant in selected_variants if str(variant).strip()})
    if not normalized_variants or any(not variant.startswith("AC08") for variant in normalized_variants):
        return

    ranking_rows: list[dict[str, str]] = []
    ranking_path = os.path.join(reports_out_dir, "pixel_delta2_ranking.csv")
    if os.path.exists(ranking_path):
        with open(ranking_path, "r", encoding="utf-8", newline="") as f:
            ranking_rows = list(csv.DictReader(f, delimiter=";"))

    ranking_by_variant: dict[str, dict[str, str]] = {}
    for row in ranking_rows:
        image_name = str(row.get("image", "")).strip()
        if not image_name:
            continue
        variant = os.path.splitext(image_name)[0].upper()
        ranking_by_variant[variant] = row

    focus_by_variant = {case["variant"].upper(): case["focus"] for case in AC08_REGRESSION_CASES}
    weak_rows: list[dict[str, str]] = []
    for variant in normalized_variants:
        base = variant.split("_", 1)[0]
        ranking_row = ranking_by_variant.get(variant, {})
        mean_delta2_raw = str(ranking_row.get("mean_delta2", "")).strip()
        try:
            mean_delta2 = float(mean_delta2_raw) if mean_delta2_raw else float("nan")
        except ValueError:
            mean_delta2 = float("nan")
        is_weak = (not math.isfinite(mean_delta2)) or mean_delta2 > ranking_threshold
        if not is_weak:
            continue

        mitigation = AC08_MITIGATION_STATUS.get(base, {})
        log_path = os.path.join(reports_out_dir, f"{variant}_element_validation.log")
        log_text = ""
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                log_text = f.read()

        active_markers: list[str] = []
        if "adaptive_unlock_applied" in log_text:
            active_markers.append("adaptive_unlock_applied")
        if "small_variant_mode_active" in log_text:
            active_markers.append("small_variant_mode_active")
        if "semantic_audit_status=" in log_text:
            active_markers.append("semantic_audit_logged")
        if "stopped_due_to_stagnation" in log_text:
            active_markers.append("stagnation_guard_triggered")

        weak_rows.append({
            "variant": variant,
            "base_family": base,
            "focus": focus_by_variant.get(variant, "review"),
            "mean_delta2": "nan" if not math.isfinite(mean_delta2) else f"{mean_delta2:.6f}",
            "risk": str(mitigation.get("risk", "unknown")),
            "family_group": str(mitigation.get("family", "unknown")),
            "implemented_mitigations": str(mitigation.get("implemented", "manual_review")),
            "active_log_markers": ",".join(active_markers) if active_markers else "none_observed",
            "status": str(mitigation.get("status", "No family-specific mitigation documented yet; inspect logs and ranking manually.")),
        })

    weak_rows.sort(
        key=lambda row: (
            -float("inf") if row["mean_delta2"] == "nan" else float(row["mean_delta2"]),
            row["variant"],
        ),
        reverse=True,
    )

    csv_path = os.path.join(reports_out_dir, "ac08_weak_family_status.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "variant",
            "base_family",
            "focus",
            "mean_delta2",
            "risk",
            "family_group",
            "implemented_mitigations",
            "active_log_markers",
            "status",
        ])
        for row in weak_rows:
            writer.writerow([
                row["variant"],
                row["base_family"],
                row["focus"],
                row["mean_delta2"],
                row["risk"],
                row["family_group"],
                row["implemented_mitigations"],
                row["active_log_markers"],
                row["status"],
            ])

    summary_lines = [
        f"ranking_threshold_mean_delta2={ranking_threshold:.3f}",
        f"weak_variants={len(weak_rows)}",
        "goal=Verbleibende AC08-Schwachfamilien und ihren aktuellen Mitigation-Status dokumentieren",
    ]
    if weak_rows:
        summary_lines.append("variants=" + ",".join(row["variant"] for row in weak_rows))
        for row in weak_rows:
            summary_lines.append(
                f"{row['variant']}: mean_delta2={row['mean_delta2']}; risk={row['risk']}; markers={row['active_log_markers']}; status={row['status']}"
            )
    else:
        summary_lines.append("variants=none")
        summary_lines.append("All selected AC08 variants are currently at or below the weak-family threshold.")

    with open(os.path.join(reports_out_dir, "ac08_weak_family_status.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")
