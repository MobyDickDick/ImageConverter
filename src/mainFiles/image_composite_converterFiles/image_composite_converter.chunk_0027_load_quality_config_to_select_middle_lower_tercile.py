def _load_quality_config(reports_out_dir: str) -> dict[str, object]:
    path = _quality_config_path(reports_out_dir)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}
""" End move to File mainFiles/convert_rangeFiles/_load_quality_config.py """


""" Start move to File mainFiles/convert_rangeFiles/_write_quality_config.py
import src
"""
def _write_quality_config(
    reports_out_dir: str,
    *,
    allowed_error_per_pixel: float,
    skipped_variants: list[str],
    source: str,
) -> None:
    path = _quality_config_path(reports_out_dir)
    normalized_error_pp = float(allowed_error_per_pixel) if math.isfinite(allowed_error_per_pixel) else 0.0
    payload = {
        "allowed_error_per_pixel": float(max(0.0, normalized_error_pp)),
        "skip_variants": sorted(set(skipped_variants)),
        "notes": (
            "Varianten in skip_variants werden in Folge-Pässen nicht erneut konvertiert. "
            "Loeschen der Datei setzt den Ablauf zurueck, dann werden wieder alle Bitmaps bearbeitet."
        ),
        "source": source,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
""" End move to File mainFiles/convert_rangeFiles/_write_quality_config.py """


def _quality_sort_key(row: dict[str, object]) -> float:
    value = float(row.get("error_per_pixel", float("inf")))
    if math.isfinite(value):
        return value
    return float("inf")




""" Start move to File mainFiles/convert_rangeFiles/_compute_successful_conversions_error_threshold.py
import src
"""
def _compute_successful_conversions_error_threshold(
    rows: list[dict[str, object]],
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> float:
    """Return mean(error_per_pixel) + 2*std(error_per_pixel) for successful rows.

    The successful set is sourced from ``successful_conversions.txt`` (via
    ``SUCCESSFUL_CONVERSIONS``) unless explicitly provided. Returns ``inf`` when
    no finite samples are available.
    """
    selected = {str(v).strip().upper() for v in (successful_variants or SUCCESSFUL_CONVERSIONS) if str(v).strip()}
    if not selected:
        return float("inf")

    values: list[float] = []
    for row in rows:
        variant = str(row.get("variant", "")).strip().upper()
        if variant not in selected:
            continue
        err = float(row.get("error_per_pixel", float("inf")))
        if math.isfinite(err):
            values.append(err)

    if not values:
        return float("inf")

    mean_val = float(statistics.fmean(values))
    std_val = float(statistics.pstdev(values)) if len(values) > 1 else 0.0
    return float(mean_val + 2.0 * std_val)
""" End move to File mainFiles/convert_rangeFiles/_compute_successful_conversions_error_threshold.py """


""" Start move to File mainFiles/convert_rangeFiles/_select_middle_lower_tercile.py
import src
"""
def _select_middle_lower_tercile(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if len(rows) < 3:
        return []

    ranked = sorted(rows, key=_quality_sort_key)
    first_cut = max(1, len(ranked) // 3)
    return ranked[first_cut:]
""" End move to File mainFiles/convert_rangeFiles/_select_middle_lower_tercile.py """


""" Start move to File mainFiles/convert_rangeFiles/_select_open_quality_cases.py
import src
"""
