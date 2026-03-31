def _extractImageSpecificDescription(entry: ET.Element, image_name: str) -> str:
    image_name = str(image_name or "").strip()
    if not image_name:
        return ""

    # Variante 1: <bilder><bild beschreibung="...">datei.jpg</bild></bilder>
    for image_tag in entry.findall("./bilder/bild"):
        tag_name = (image_tag.text or "").strip()
        if tag_name == image_name:
            attr_desc = (image_tag.attrib.get("beschreibung") or "").strip()
            if attr_desc:
                return attr_desc
            child_desc = (image_tag.findtext("beschreibung") or "").strip()
            if child_desc:
                return child_desc

    # Variante 2: <bildbeschreibungen><bildbeschreibung bild="datei.jpg">...</bildbeschreibung></bildbeschreibungen>
    for detail_tag in entry.findall("./bildbeschreibungen/bildbeschreibung"):
        detail_name = (detail_tag.attrib.get("bild") or detail_tag.attrib.get("image") or "").strip()
        if detail_name and detail_name == image_name:
            text_desc = ("".join(detail_tag.itertext()) or "").strip()
            if text_desc:
                return re.sub(r"\s+", " ", text_desc).strip()
    return ""
