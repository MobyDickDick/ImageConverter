from __future__ import annotations

import importlib
import os
import re
from dataclasses import dataclass

from src.iCCModules import imageCompositeConverterAudit as audit_helpers
from src.iCCModules import imageCompositeConverterDescriptions as description_mapping_helpers
from src.iCCModules import imageCompositeConverterDualArrowBadge as dual_arrow_badge_helpers
from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers
from src.iCCModules import imageCompositeConverterSemantic as semantic_helpers


def _get_base_name_from_file(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r"(-\d+)$", "", name)
    while True:
        prev = name
        name = re.sub(r"_sia$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"_([1-9]|L|M|S|[1-9]S|W|X)$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"_([A-Z]{2,3})$", "", name, flags=re.IGNORECASE)
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


def _build_description_contract(desc_raw: str) -> dict[str, object]:
    normalized = re.sub(r"\s+", " ", str(desc_raw or "")).strip().lower()
    reference_tokens = ("wie ", "analog ", "referenz", "entspricht")
    geometry_tokens = (
        "kreis",
        "ellipse",
        "rechteck",
        "viereck",
        "dreieck",
        "linie",
        "band",
        "kreuz",
        "pfeil",
        "symbol",
        "gradient",
        "kompressor",
        "kopressor",
        "ventil",
        "kelle",
    )
    condition_tokens = ("wenn", "falls", "nur", "außer", "nicht", "ohne", "mit")
    has_reference = any(token in normalized for token in reference_tokens)
    has_geometry_terms = any(token in normalized for token in geometry_tokens)
    has_conditions = any(token in normalized for token in condition_tokens)
    deficits: list[str] = []
    if not normalized:
        deficits.append("missing_description")
    if not has_geometry_terms and not has_reference:
        deficits.append("missing_geometry_terms")
    return {
        "has_reference": has_reference,
        "has_geometry_terms": has_geometry_terms,
        "has_conditions": has_conditions,
        "deficits": deficits,
        "status": "ok" if not deficits else "insufficient_description",
    }


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

    def parseDescription(self, base_name: str, img_filename: str, _visited: set[str] | None = None):
        if _visited is None:
            _visited = set()
        canonical_base = _get_base_name_from_file(base_name).upper()
        if not canonical_base:
            canonical_base = _get_base_name_from_file(img_filename).upper()
        if canonical_base in _visited:
            return "", {"mode": "auto", "elements": []}
        _visited.add(canonical_base)
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
            "description_contract": _build_description_contract(desc_raw),
            "description_constraints": geometry_ir_helpers.buildDescriptionConstraintsImpl(desc_raw),
            "geometry_ir": geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(desc_raw),
        }

        contract_status = str(params["description_contract"].get("status", "ok"))
        params["contract_status"] = contract_status

        compact_reference_badge = "AR" + "0100"
        semantic_symbol = symbol_upper.startswith("AC08") or symbol_upper == compact_reference_badge
        if semantic_symbol:
            params["mode"] = "semantic_badge"

        if semantic_helpers.apply_semantic_badge_family_rules(
            base_upper=base_upper,
            symbol_upper=symbol_upper,
            desc=desc,
            params=params,
        ):
            if contract_status == "insufficient_description":
                params["contract_status"] = "family_rule"
                params["description_contract"]["status"] = "family_rule"
            return desc, params

        if any(
            str(element.get("id", "")) == "rh_badge_circle"
            for element in params["geometry_ir"]
        ):
            params["mode"] = "non_composite"
            params["label"] = ""
            params["elements"].append(
                "GEOMETRIE: Anschlussfreies Kreis-/Text-Badge wird über Geometry-IR rekonstruiert"
            )
            return desc, params

        if contract_status == "insufficient_description":
            params["mode"] = "insufficient_description"
            params["label"] = ""
            params["elements"].append(
                "MANUELL: Beschreibung unzureichend (fehlende Geometriehinweise oder leerer Beschreibungstext)."
            )
            return desc, params

        if semantic_helpers.apply_semantic_badge_description_rules(desc=desc, params=params):
            return desc, params

        if dual_arrow_badge_helpers.looksLikeDualArrowDescriptionImpl(desc):
            params["mode"] = "dual_arrow_badge"
            params["elements"].append("SEMANTIC: zwei vertikale farbige Pfeile (blau runter, rot hoch)")
            params["label"] = ""
            return desc, params


        ac0030_alias = Reflection._extract_reference_symbol(desc_raw) == "AC0030" or "wie ac0030" in desc
        has_cross_hint = any(token in desc for token in ("diagonalen", "andreaskreuz", "kreuz"))
        has_cooler_hint = any(token in desc for token in ("kühlelement", "rechteck", "minus-minus"))
        if ac0030_alias and (has_cross_hint or has_cooler_hint):
            params["mode"] = "composite"
            params["top_source_ref"] = None
            params["bottom_shape"] = "square_cross"
            params["elements"].append("GEOMETRIE: Referenzartige Kreuz-/Kühlelement-Beschreibung wird über Geometry-IR rekonstruiert")
            params["elements"].append("UNTEN: Parametrisch generiertes Viereck mit Andreaskreuz")
            return desc, params

        reference_symbol = Reflection._extract_reference_symbol(desc_raw)
        if reference_symbol and reference_symbol != symbol_upper:
            inherited = self._inherit_mode_from_reference(reference_symbol=reference_symbol, img_filename=img_filename, visited=_visited)
            if inherited is not None:
                _ref_desc_text, inherited_params = inherited
                inherited_params["documented_alias_refs"] = sorted(Reflection._extractDocumentedAliasRefs(desc))
                inherited_params["description_fragments"] = description_fragments
                inherited_params["variant_name"] = os.path.splitext(str(img_filename))[0].upper()
                return desc, inherited_params

        non_traceable_hint = Reflection._detect_non_traceable_hint(desc)
        if non_traceable_hint:
            params["review_reason"] = non_traceable_hint
            if Reflection._should_allow_auto_for_unclassified_geometry(desc, non_traceable_hint):
                params["elements"].append(
                    "AUTO: Trotz unzugeordneter Familienzuordnung wurde wegen ausreichender Geometriehinweise automatisch konvertiert."
                )
            else:
                params["mode"] = "manual_review"
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
    def _extract_reference_symbol(text: str) -> str | None:
        normalized = str(text or "")
        match = re.search(r"\bwie\s+([a-z]{2}\d{3,4})\b", normalized, flags=re.IGNORECASE)
        if not match:
            return None
        return match.group(1).upper()

    def _inherit_mode_from_reference(self, *, reference_symbol: str, img_filename: str, visited: set[str]) -> tuple[str, dict[str, object]] | None:
        reference_desc = self.raw_desc.get(reference_symbol)
        if not reference_desc:
            return None
        ref_desc_text, ref_params = self.parseDescription(reference_symbol, img_filename, _visited=set(visited))
        ref_mode = str(ref_params.get("mode", "")).strip()
        if ref_mode in {"manual_review", "auto"}:
            return None
        inherited = {
            key: value
            for key, value in ref_params.items()
            if key not in {"description_fragments", "variant_name"}
        }
        inherited.setdefault("elements", [])
        if isinstance(inherited.get("elements"), list):
            inherited["elements"] = list(inherited["elements"])
            inherited["elements"].append(f"REFERENZ: Abgeleitet aus {reference_symbol}")
        return ref_desc_text, inherited


    @staticmethod
    def _should_allow_auto_for_unclassified_geometry(text: str, non_traceable_hint: str | None) -> bool:
        if not non_traceable_hint:
            return False
        normalized = re.sub(r"\s+", " ", str(text or "").lower()).strip()
        if not normalized:
            return False
        if not any(
            token in non_traceable_hint.lower()
            for token in ("familienzuordnung", "unzugeordnete wurzelform", "fachlich noch nicht klassifiziert")
        ):
            return False
        geometry_tokens = (
            "kreis",
            "ellipse",
            "rechteck",
            "polygon",
            "dreieck",
            "linie",
            "griff",
            "symmetrieachse",
        )
        hits = sum(1 for token in geometry_tokens if token in normalized)
        return hits >= 2

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
