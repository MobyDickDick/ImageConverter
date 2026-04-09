"""Extracted semantic audit/report helpers for imageCompositeConverter."""

from __future__ import annotations

import csv
import json
import os
from collections.abc import Callable


def semanticAuditRecordImpl(
    *,
    base_name: str,
    filename: str,
    description_fragments: list[dict[str, str]],
    semantic_elements: list[str],
    status: str,
    get_base_name_fn: Callable[[str], str],
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
        "base_name": get_base_name_fn(base_name).upper(),
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


def collectDescriptionFragmentsImpl(
    raw_desc: dict[str, str],
    *,
    base_name: str,
    img_filename: str,
    get_base_name_fn: Callable[[str], str],
) -> list[dict[str, str]]:
    """Return ordered description fragments consulted for one variant lookup."""
    variant_name = os.path.splitext(img_filename)[0]
    canonical_base = get_base_name_fn(base_name).upper()
    canonical_variant = get_base_name_fn(variant_name).upper()

    lookup_keys = [
        ("base_name", str(base_name)),
        ("variant_name", str(variant_name)),
        ("canonical_base", canonical_base),
        ("canonical_variant", canonical_variant),
    ]
    fragments: list[dict[str, str]] = []
    seen_lookup_keys: set[str] = set()
    seen_texts: set[str] = set()
    for source, key in lookup_keys:
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        if normalized_key in seen_lookup_keys:
            continue
        seen_lookup_keys.add(normalized_key)
        value = str(raw_desc.get(normalized_key, "") or "").strip()
        if not value:
            continue
        normalized_value = " ".join(value.split())
        if normalized_value in seen_texts:
            continue
        seen_texts.add(normalized_value)
        fragments.append({"source": source, "key": normalized_key, "text": value})
    return fragments


def writeSemanticAuditReportImpl(reports_out_dir: str, audit_rows: list[dict[str, object]]) -> None:
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


def isSemanticTemplateVariantImpl(
    base_name: str,
    get_base_name_fn: Callable[[str], str],
    params: dict[str, object] | None = None,
) -> bool:
    """Return whether an existing converted SVG should participate as semantic donor."""
    normalized = str(get_base_name_fn(base_name or "")).upper()
    if not normalized:
        return False
    if normalized.startswith("AC08") or normalized in {"AR0100"}:
        return True
    if isinstance(params, dict) and str(params.get("mode", "")).lower() == "semantic_badge":
        return True
    return False
