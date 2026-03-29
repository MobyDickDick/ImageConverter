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
def _render_svg_to_numpy_inprocess(svg_string: str, size_w: int, size_h: int):
    if fitz is None or np is None or cv2 is None:
        return None

    svg_string = str(svg_string or "")
    if re.search(r"(?<![A-Za-z])(nan|inf)(?![A-Za-z])", svg_string, flags=re.IGNORECASE):
        return None

    attempts = [svg_string]
    normalized_svg = re.sub(r">\s+<", "><", svg_string.strip())
    if normalized_svg and normalized_svg != svg_string:
        attempts.append(normalized_svg)

    for candidate_svg in attempts:
        page = None
        pix = None
        try:
            with fitz.open("pdf", candidate_svg.encode("utf-8")) as doc:
                page = doc.load_page(0)
                zoom_x = size_w / page.rect.width if page.rect.width > 0 else 1
                zoom_y = size_h / page.rect.height if page.rect.height > 0 else 1
                mat = fitz.Matrix(zoom_x, zoom_y)
