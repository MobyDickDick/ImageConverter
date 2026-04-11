from __future__ import annotations

import importlib
import os
import re
from dataclasses import dataclass

from src.iCCModules import imageCompositeConverterAudit as audit_helpers
from src.iCCModules import imageCompositeConverterDescriptions as description_mapping_helpers
from src.iCCModules import imageCompositeConverterSemantic as semantic_helpers


def _get_base_name_from_file(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r"(-\d+)$", "", name)
    while True:
        prev = name
        name = re.sub(r"_([1-9]|L|M|S|[1-9]S|W|X)$", "", name, flags=re.IGNORECASE)
        if name == prev:
            break
    return name


def _load_description_mapping(path: str) -> dict[str, str]:
    return description_mapping_helpers.loadDescriptionMappingImpl(
        path,
        get_base_name_from_file_fn=_get_base_name_from_file,
    )


def _collect_description_fragments(raw_desc: dict[str, str], base_name: str, img_filename: str) -> list[dict[str, str]]:
    return audit_helpers.collectDescriptionFragmentsImpl(
        raw_desc,
        base_name=base_name,
        img_filename=img_filename,
        get_base_name_fn=_get_base_name_from_file,
    )


@dataclass
class Perception:
    img_path: str
    csv_path: str

    def __post_init__(self) -> None:
        self.base_name = _get_base_name_from_file(os.path.basename(self.img_path))
        try:
            cv2_module = importlib.import_module("cv2")
        except Exception:
            cv2_module = None
        self.img = cv2_module.imread(self.img_path) if cv2_module is not None else None
        self.raw_desc = self._loadDescriptions()

    def _loadDescriptions(self) -> dict[str, str]:
        return _load_description_mapping(self.csv_path)


class Reflection:
    def __init__(self, raw_desc: dict[str, str]):
        self.raw_desc = raw_desc

    def parseDescription(self, base_name: str, img_filename: str):
        canonical_base = _get_base_name_from_file(base_name).upper()
        if not canonical_base:
            canonical_base = _get_base_name_from_file(img_filename).upper()
        description_fragments = _collect_description_fragments(self.raw_desc, base_name, img_filename)
        desc_raw = " ".join(fragment["text"] for fragment in description_fragments)
        desc = desc_raw.lower().strip()
        base_upper = canonical_base or base_name.upper()
        symbol_upper = canonical_base or base_upper

        params = {
            "mode": "auto",
            "top_source_ref": None,
            "bottom_shape": None,
            "elements": [],
            "label": "M",
            "variant_name": os.path.splitext(str(img_filename))[0].upper(),
            "documented_alias_refs": sorted(Reflection._extractDocumentedAliasRefs(desc)),
            "description_fragments": description_fragments,
            "semantic_priority_order": ["family_rule", "layout_override", "description_heuristic"],
            "semantic_conflicts": [],
            "semantic_sources": {},
        }

        semantic_symbol = symbol_upper.startswith("AC08") or symbol_upper == "AR0100"
        if semantic_symbol:
            params["mode"] = "semantic_badge"

        if semantic_helpers.apply_semantic_badge_family_rules(
            base_upper=base_upper,
            symbol_upper=symbol_upper,
            desc=desc,
            params=params,
        ):
            return desc, params

        non_traceable_hint = Reflection._detect_non_traceable_hint(desc)
        if non_traceable_hint:
            params["mode"] = "manual_review"
            params["review_reason"] = non_traceable_hint
            params["label"] = ""
            params["elements"].append(f"MANUELL: {non_traceable_hint}")
            return desc, params

        match = re.search(r"\boven\b.*?\bwie(?:\s+in)?\s+([a-z]{2}\d{3,4})\b", desc)
        if match:
            params["mode"] = "composite"
            params["top_source_ref"] = match.group(1).upper()
            params["elements"].append(f"OBEN: Geschnitten aus Originaldatei {params['top_source_ref']}")

        if "unten" in desc and "viereck" in desc and "kreuz" in desc:
            params["mode"] = "composite"
            params["bottom_shape"] = "square_cross"
            params["elements"].append("UNTEN: Parametrisch generiertes Viereck mit Kreuz")

        return desc, params

    def parse_description(self, base_name: str, img_filename: str):
        return self.parseDescription(base_name, img_filename)

    @staticmethod
    def _extractDocumentedAliasRefs(text: str) -> set[str]:
        return semantic_helpers.extract_documented_alias_refs(text)

    @staticmethod
    def _extract_documented_alias_refs(text: str) -> set[str]:
        return Reflection._extractDocumentedAliasRefs(text)

    @staticmethod
    def _detect_non_traceable_hint(text: str) -> str | None:
        normalized = re.sub(r"\s+", " ", str(text or "").lower()).strip()
        if not normalized:
            return None
        hint_patterns = [
            (r"nicht automatisch nachzeichnbar", "Beschreibung markiert Symbol als nicht automatisch nachzeichnbar."),
            (r"nur eingeschränkt.*reproduzierbar", "Beschreibung markiert Symbol als nur eingeschränkt reproduzierbar."),
            (r"außerhalb der robust unterstützten standard-geometrien", "Beschreibung markiert Symbol außerhalb der robust unterstützten Standard-Geometrien."),
            (r"bitte einer finalen wurzelform-kategorie zuordnen", "Beschreibung fordert manuelle Zuordnung zu einer finalen Wurzelform-Kategorie."),
            (r"noch nicht fachlich klassifiziert", "Beschreibung markiert Symbol als fachlich noch nicht klassifiziert."),
            (r"ohne finale familienzuordnung", "Beschreibung markiert Symbol ohne finale Familienzuordnung."),
            (r"unzugeordnete wurzelform", "Beschreibung markiert Symbol als unzugeordnete Wurzelform."),
        ]
        for pattern, message in hint_patterns:
            if re.search(pattern, normalized):
                return message
        return None

    @staticmethod
    def _parseSemanticBadgeLayoutOverrides(text: str) -> dict[str, float | str]:
        return semantic_helpers.parse_semantic_badge_layout_overrides(text)

    @staticmethod
    def _parse_semantic_badge_layout_overrides(text: str) -> dict[str, float | str]:
        return Reflection._parseSemanticBadgeLayoutOverrides(text)
