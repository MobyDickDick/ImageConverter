def _semantic_audit_record(
    *,
    base_name: str,
    filename: str,
    description_fragments: list[dict[str, str]],
    semantic_elements: list[str],
    status: str,
    mismatch_reasons: list[str] | None = None,
    semantic_priority_order: list[str] | None = None,
    semantic_conflicts: list[str] | None = None,
    semantic_sources: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a normalized semantic-audit record for AC0811..AC0814 style families."""
    mismatch_reasons = [str(reason) for reason in (mismatch_reasons or []) if str(reason).strip()]
    joined_description = " ".join(fragment["text"] for fragment in description_fragments).strip()
    return {
        "filename": str(filename),
        "base_name": get_base_name_from_file(base_name).upper(),
        "description_fragments": description_fragments,
        "recognized_description_elements": [fragment["text"] for fragment in description_fragments],
        "description_lookup_keys": [fragment["key"] for fragment in description_fragments],
        "description_text": joined_description,
        "derived_elements": [str(element) for element in semantic_elements],
        "semantic_priority_order": [str(item) for item in (semantic_priority_order or [])],
        "semantic_conflicts": [str(item) for item in (semantic_conflicts or [])],
        "semantic_sources": dict(semantic_sources or {}),
        "status": str(status),
        "mismatch_reason": " | ".join(mismatch_reasons),
        "mismatch_reasons": mismatch_reasons,
    }


""" Start move to File mainFiles/convert_rangeFiles/_write_semantic_audit_report.py
import src
"""
def _write_semantic_audit_report(reports_out_dir: str, audit_rows: list[dict[str, object]]) -> None:
    """Persist semantic audit rows as CSV/JSON for targeted AC0811..AC0814 review."""
    if not audit_rows:
        return

    csv_path = os.path.join(reports_out_dir, "semantic_audit_ac0811_ac0814.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "filename",
                "base_name",
                "description_lookup_keys",
                "recognized_description_elements",
                "description_text",
                "derived_elements",
                "semantic_priority_order",
                "semantic_conflicts",
                "status",
                "mismatch_reason",
            ]
        )
        for row in audit_rows:
            writer.writerow(
                [
                    row.get("filename", ""),
                    row.get("base_name", ""),
                    " | ".join(str(value) for value in row.get("description_lookup_keys", [])),
                    " | ".join(str(value) for value in row.get("recognized_description_elements", [])),
                    row.get("description_text", ""),
                    " | ".join(str(value) for value in row.get("derived_elements", [])),
                    " > ".join(str(value) for value in row.get("semantic_priority_order", [])),
                    " | ".join(str(value) for value in row.get("semantic_conflicts", [])),
                    row.get("status", ""),
                    row.get("mismatch_reason", ""),
                ]
            )

    json_path = os.path.join(reports_out_dir, "semantic_audit_ac0811_ac0814.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_rows, f, ensure_ascii=False, indent=2)
""" End move to File mainFiles/convert_rangeFiles/_write_semantic_audit_report.py """


""" Start move to File mainFiles/convert_rangeFiles/_diff_output_dir.py
import src
"""
def _diff_output_dir(output_root: str) -> str:
    return os.path.join(output_root, "diff_pngs")
""" End move to File mainFiles/convert_rangeFiles/_diff_output_dir.py """


""" Start move to File mainFiles/convert_rangeFiles/_reports_output_dir.py
import src
"""
def _reports_output_dir(output_root: str) -> str:
    return os.path.join(output_root, "reports")
""" End move to File mainFiles/convert_rangeFiles/_reports_output_dir.py """


""" Start move to File mainFiles/convert_rangeFiles/_load_existing_conversion_rowsFiles/_is_semantic_template_variant.py
import src
"""
