from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _select_middle_lower_tercile(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if len(rows) < 3:
        return []

    ranked = sorted(rows, key=_quality_sort_key)
    first_cut = max(1, len(ranked) // 3)
    return ranked[first_cut:]
