from src import image_composite_converter as _icc

globals().update(vars(_icc))

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
