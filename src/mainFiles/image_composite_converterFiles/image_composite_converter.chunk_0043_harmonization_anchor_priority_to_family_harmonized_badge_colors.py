""" End move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_scale_badge_params.py """


def _harmonization_anchor_priority(suffix: str, prefer_large: bool) -> int:
    """Return size-priority rank for L/M/S harmonization anchors."""
    if prefer_large:
        # For connector families we keep L authoritative to avoid undersized
        # large variants caused by propagating medium geometry upwards.
        return {"L": 0, "M": 1, "S": 2}.get(str(suffix), 3)
    # Plain circles remain more stable when M is used as anchor.
    return {"M": 0, "L": 1, "S": 2}.get(str(suffix), 3)


""" Start move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_family_harmonized_badge_colorsFiles/_clip_gray.py
import src
"""
def _clip_gray(value: float) -> int:
    return int(max(0, min(255, round(float(value)))))
""" End move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_family_harmonized_badge_colorsFiles/_clip_gray.py """


""" Start move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_family_harmonized_badge_colors.py
import src
"""
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
""" End move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variantsFiles/_family_harmonized_badge_colors.py """


""" Start move to File mainFiles/convert_rangeFiles/_harmonize_semantic_size_variants.py
import src
"""
