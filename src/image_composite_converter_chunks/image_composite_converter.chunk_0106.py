        scaled["r"] = r

    return scaled


def _harmonization_anchor_priority(suffix: str, prefer_large: bool) -> int:
    """Return size-priority rank for L/M/S harmonization anchors."""
    if prefer_large:
        # For connector families we keep L authoritative to avoid undersized
        # large variants caused by propagating medium geometry upwards.
        return {"L": 0, "M": 1, "S": 2}.get(str(suffix), 3)
    # Plain circles remain more stable when M is used as anchor.
    return {"M": 0, "L": 1, "S": 2}.get(str(suffix), 3)


def _clip_gray(value: float) -> int:
    return int(max(0, min(255, round(float(value)))))


def _family_harmonized_badge_colors(variant_rows: list[dict[str, object]]) -> dict[str, int]:
    """Derive a family palette from L/M/S variants and slightly boost contrast."""
    buckets: dict[str, list[float]] = {
        "fill_gray": [],
        "stroke_gray": [],
        "text_gray": [],
        "stem_gray": [],
    }
    for row in variant_rows:
        params = dict(row["params"])
        for key in buckets:
            value = params.get(key)
            if value is None:
                continue
            try:
                buckets[key].append(float(value))
            except (TypeError, ValueError):
                continue

    fill_avg = sum(buckets["fill_gray"]) / max(1, len(buckets["fill_gray"]))
    stroke_avg = sum(buckets["stroke_gray"]) / max(1, len(buckets["stroke_gray"]))
    if fill_avg < stroke_avg:
        fill_avg, stroke_avg = stroke_avg, fill_avg

    center = (fill_avg + stroke_avg) / 2.0
    delta = abs(fill_avg - stroke_avg)
    boosted_delta = max(18.0, delta * 1.12)
    fill_gray = _clip_gray(center + (boosted_delta / 2.0))
    stroke_gray = _clip_gray(center - (boosted_delta / 2.0))
    if fill_gray <= stroke_gray:
        fill_gray = _clip_gray(max(fill_gray, stroke_gray + 1.0))

    colors = {
        "fill_gray": fill_gray,
        "stroke_gray": stroke_gray,
        "text_gray": stroke_gray,
        "stem_gray": stroke_gray,
    }

    if buckets["text_gray"]:
        text_avg = sum(buckets["text_gray"]) / float(len(buckets["text_gray"]))
        colors["text_gray"] = _clip_gray(min(text_avg, float(stroke_gray)))

    if buckets["stem_gray"]:
        stem_avg = sum(buckets["stem_gray"]) / float(len(buckets["stem_gray"]))
        colors["stem_gray"] = _clip_gray(min(stem_avg, float(stroke_gray)))

    return colors


def _harmonize_semantic_size_variants(
    results: list[dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
) -> None:
    grouped: dict[str, list[dict[str, object]]] = {}
    for result in results:
        base = str(result.get("base", ""))
        grouped.setdefault(base, []).append(result)

    harmonized_logs: list[str] = []
    category_logs: list[str] = []
    for base, entries in sorted(grouped.items()):
        if len(entries) < 2:
            continue

        variant_rows: list[dict[str, object]] = []
        for entry in entries:
            variant = str(entry["variant"])
            suffix = variant.rsplit("_", 1)[-1] if "_" in variant else ""
            if suffix not in {"L", "M", "S"}:
                continue
            parsed = _read_svg_geometry(os.path.join(svg_out_dir, f"{variant}.svg"))
            if parsed is None:
                continue
            w, h, params = parsed
            variant_rows.append({"entry": entry, "variant": variant, "suffix": suffix, "w": w, "h": h, "params": params})

        if len(variant_rows) < 2:
            continue
