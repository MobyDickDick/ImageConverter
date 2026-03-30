from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _extract_image_specific_description(entry: ET.Element, image_name: str) -> str:
    normalized_name = str(image_name or "").strip()
    if not normalized_name:
        return ""

    for image_tag in entry.findall("./bilder/bild"):
        tag_name = (image_tag.text or "").strip()
        if tag_name == normalized_name:
            attr_desc = (image_tag.attrib.get("beschreibung") or "").strip()
            if attr_desc:
                return attr_desc
            child_desc = (image_tag.findtext("beschreibung") or "").strip()
            if child_desc:
                return child_desc

    for detail_tag in entry.findall("./bildbeschreibungen/bildbeschreibung"):
        detail_name = (detail_tag.attrib.get("bild") or detail_tag.attrib.get("image") or "").strip()
        if detail_name and detail_name == normalized_name:
            text_desc = ("".join(detail_tag.itertext()) or "").strip()
            if text_desc:
                return re.sub(r"\\s+", " ", text_desc).strip()
    return ""
