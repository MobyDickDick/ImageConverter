class Reflection:
    def __init__(self, raw_desc: dict[str, str]):
        self.raw_desc = raw_desc

    def parse_description(self, base_name: str, img_filename: str):
        canonical_base = get_base_name_from_file(base_name).upper()
        if not canonical_base:
            canonical_base = get_base_name_from_file(img_filename).upper()
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
            "documented_alias_refs": sorted(Reflection._extract_documented_alias_refs(desc)),
            "description_fragments": description_fragments,
            "semantic_priority_order": [
                "family_rule",
                "layout_override",
                "description_heuristic",
            ],
            "semantic_conflicts": [],
            "semantic_sources": {},
        }

        semantic_symbol = symbol_upper.startswith("AC08") or symbol_upper == "AR0100"
        if semantic_symbol:
            params["mode"] = "semantic_badge"

        if base_upper in {
            "AR0100",
            "AC0800",
            "AC0811",
            "AC0810",
            "AC0812",
            "AC0813",
            "AC0814",
            "AC0820",
            "AC0831",
            "AC0832",
            "AC0833",
            "AC0834",
            "AC0835",
            "AC0836",
            "AC0837",
            "AC0838",
            "AC0839",
            "AC0870",
            "AC0881",
            "AC0882",
        }:
            params["mode"] = "semantic_badge"
            family_elements: list[str] = []
            heuristic_elements: list[str] = []
            if base_upper in {"AC0800", "AC0810", "AC0811", "AC0812", "AC0813", "AC0814"}:
                family_elements.append("SEMANTIC: Kreis ohne Buchstabe")
                params["label"] = ""
            elif re.search(r"\bco(?:[_\s\-\^]*2|₂)\b", desc):
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO_2")
                params["label"] = "CO_2"
            elif re.search(r"\bco\b", desc):
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO")
                params["label"] = "CO"
            elif "voc" in desc:
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe VOC")
                params["label"] = "VOC"
            elif "buchstabe" in desc:
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
                params["label"] = "M" if symbol_upper == "AR0100" else "T"
            else:
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
                params["label"] = "M" if base_upper == "AR0100" else "T"
            if base_upper in {"AC0810", "AC0814", "AC0834", "AC0838", "AC0839"}:
                family_elements.append("SEMANTIC: waagrechter Strich rechts vom Kreis")
            if base_upper in {"AC0811", "AC0881", "AC0831", "AC0836"}:
                family_elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")
            if base_upper in {"AC0813", "AC0833"}:
                family_elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
            if base_upper in {"AC0812", "AC0832", "AC0837", "AC0882"}:
                family_elements.append("SEMANTIC: waagrechter Strich links vom Kreis")
            if "waagrechter strich rechts" in desc:
                heuristic_elements.append("SEMANTIC: waagrechter Strich rechts vom Kreis")
            if "senkrechter strich oben" in desc:
                heuristic_elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
            if "senkrechter strich hinter" in desc:
                heuristic_elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")

            params["semantic_sources"] = {
                "family_rule": list(dict.fromkeys(family_elements)),
                "description_heuristic": list(dict.fromkeys(heuristic_elements)),
            }
            params["elements"].extend(params["semantic_sources"]["family_rule"])
            params["semantic_sources"]["description_heuristic"] = list(
                dict.fromkeys(params["semantic_sources"]["description_heuristic"])
            )
            for element in params["semantic_sources"]["description_heuristic"]:
                if element not in params["elements"]:
                    params["elements"].append(element)

            layout_overrides = Reflection._parse_semantic_badge_layout_overrides(desc)
            if layout_overrides:
                params["badge_overrides"] = layout_overrides
                params["semantic_sources"]["layout_override"] = sorted(layout_overrides)
                params["elements"].append("SEMANTIC: Layout-Override für Badge-Text")

            return desc, params

        match = re.search(r"\boven\b.*?\bwie(?:\s+in)?\s+([a-z]{2}\d{3,4})\b", desc)
        if match:
            params["mode"] = "composite"
            params["top_source_ref"] = match.group(1).upper()
            params["elements"].append(
                f"OBEN: Geschnitten aus Originaldatei {params['top_source_ref']}"
            )

        if "unten" in desc and "viereck" in desc and "kreuz" in desc:
            params["mode"] = "composite"
            params["bottom_shape"] = "square_cross"
            params["elements"].append("UNTEN: Parametrisch generiertes Viereck mit Kreuz")

        return desc, params


    @staticmethod
    def _extract_documented_alias_refs(text: str) -> set[str]:
        """Extract explicit "Wie AC0000" style alias references from descriptions."""
        if not text:
            return set()

        refs = {
            match.upper()
            for match in re.findall(r"\bwie(?:\s+in)?\s+([a-z]{2}\d{3,4})\b", text, flags=re.IGNORECASE)
        }
        return refs

    @staticmethod
    def _parse_semantic_badge_layout_overrides(text: str) -> dict[str, float | str]:
        """Extract optional layout directives from semantic badge descriptions."""
        if not text:
            return {}

        normalized = re.sub(r"\s+", " ", text.lower()).strip()
        overrides: dict[str, float | str] = {}

        # Example phrases we intentionally support:
        # - "CO bezüglich des Kreises vertikal zentriert"
        # - "CO_2 bezüglich des Kreises horizontal zentriert"
        if re.search(r"\bco\b[^.\n]*vertikal\s+zentriert", normalized):
            overrides["co2_dy"] = 0.0
            overrides["co2_optical_bias"] = 0.0

        if re.search(r"\bco(?:[_\s-]*2|₂)\b[^.\n]*horizontal\s+zentriert", normalized):
            # Horizontal centering explicitly targets the full CO₂ cluster,
            # not just the dominant "CO" run.
            overrides["co2_anchor_mode"] = "cluster"
            overrides["co2_dx"] = 0.0

        return overrides
