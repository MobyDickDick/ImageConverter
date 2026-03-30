from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _sorted_successful_conversion_metrics_rows(
    metrics: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Sort successful-conversion rows by converted image name/variant."""
    return sorted(metrics, key=lambda row: str(row.get('variant', '')).upper())
