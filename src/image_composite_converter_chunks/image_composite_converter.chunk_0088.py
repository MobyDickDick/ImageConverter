        writer.writerow(["filename", "status", "reason", "details", "log_file"])
        for failure in failures:
            writer.writerow([
                failure.get("filename", ""),
                failure.get("status", ""),
                failure.get("reason", ""),
                failure.get("details", ""),
                failure.get("log_file", ""),
            ])



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
