from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_default_semantic_audit_targets() -> set[str]:
    config_path = Path(__file__).resolve().parents[2] / "config" / "semantic_audit_targets.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return set()
    return {str(target).upper() for target in payload.get("targets", [])}


def shouldCreateSemanticAuditForBaseNameImpl(
    base_name: str,
    *,
    get_base_name_from_file_fn,
    semantic_audit_targets: set[str] | None = None,
) -> bool:
    targets = semantic_audit_targets or _load_default_semantic_audit_targets()
    normalized_base_name = str(get_base_name_from_file_fn(base_name)).upper()
    return normalized_base_name in targets


def buildSemanticAuditRecordKwargsImpl(
    *,
    filename: str,
    params: dict[str, object],
    status: str,
    mismatch_reasons: list[str] | None = None,
) -> dict[str, object]:
    return {
        "filename": filename,
        "description_fragments": list(params.get("description_fragments", [])),
        "semantic_elements": list(params.get("elements", [])),
        "status": status,
        "mismatch_reasons": mismatch_reasons,
        "semantic_priority_order": list(params.get("semantic_priority_order", [])),
        "semantic_conflicts": list(params.get("semantic_conflicts", [])),
        "semantic_sources": dict(params.get("semantic_sources", {})),
    }
