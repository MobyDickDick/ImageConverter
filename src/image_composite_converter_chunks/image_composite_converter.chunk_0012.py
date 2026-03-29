        "--platform",
        platform_tag,
        "--implementation",
        "cp",
        "--python-version",
        python_version,
        "--only-binary=:all:",
        "--upgrade-strategy",
        "eager",
        *_required_vendor_packages(),
    ]


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
