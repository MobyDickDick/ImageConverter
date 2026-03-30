

""" Start move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/collect_successful_conversion_quality_metricsFiles/_read_validation_log_details.py
import src
"""
def _read_validation_log_details(log_path: str) -> dict[str, str]:
    if not os.path.exists(log_path):
        return {}
    details: dict[str, str] = {}
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or ": " in line.split("=", 1)[0]:
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                details[key] = value
    except OSError:
        return {}
    return details
""" End move to File mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/collect_successful_conversion_quality_metricsFiles/_read_validation_log_details.py """


""" Start move to File mainFiles/convert_rangeFiles/_write_batch_failure_summary.py
import src
"""
def _write_batch_failure_summary(reports_out_dir: str, failures: list[dict[str, str]]) -> None:
    summary_path = os.path.join(reports_out_dir, "batch_failure_summary.csv")
    with open(summary_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["filename", "status", "reason", "details", "log_file"])
        for failure in failures:
            writer.writerow([
                failure.get("filename", ""),
                failure.get("status", ""),
                failure.get("reason", ""),
                failure.get("details", ""),
                failure.get("log_file", ""),
            ])
""" End move to File mainFiles/convert_rangeFiles/_write_batch_failure_summary.py """



def _collect_description_fragments(raw_desc: dict[str, str], base_name: str, img_filename: str) -> list[dict[str, str]]:
    """Return the ordered description fragments consulted for one variant lookup."""
    variant_name = os.path.splitext(img_filename)[0]
    canonical_base = get_base_name_from_file(base_name).upper()
    canonical_variant = get_base_name_from_file(variant_name).upper()

    lookup_keys = [
        ("base_name", str(base_name)),
        ("variant_name", str(variant_name)),
        ("canonical_base", canonical_base),
        ("canonical_variant", canonical_variant),
    ]
    fragments: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source, key in lookup_keys:
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        marker = (source, normalized_key)
        if marker in seen:
            continue
        seen.add(marker)
        value = str(raw_desc.get(normalized_key, "") or "").strip()
        if not value:
            continue
        fragments.append({"source": source, "key": normalized_key, "text": value})
    return fragments


