def _load_description_mapping_from_xml(path: str) -> dict[str, str]:
    raw_desc: dict[str, str] = {}
    resolved_path = _resolve_description_xml_path(path)
    if resolved_path is None:
        return raw_desc

    try:
        tree = ET.parse(resolved_path)
    except ET.ParseError as exc:
        raise DescriptionMappingError(
            "Description XML could not be parsed.",
            span=SourceSpan(path=resolved_path, line=exc.position[0], column=exc.position[1] + 1),
        ) from exc

    root = tree.getroot()

    for entry in root.findall(".//entry"):
        desc = (entry.findtext("beschreibung") or "").strip()
        root_form = (entry.findtext("wurzelform") or "").strip()
        key = str(entry.attrib.get("key", "")).strip()

        if root_form and desc:
            _register_description(raw_desc, root_form, desc)
        if key and desc:
            _register_description(raw_desc, key, desc)

        for image_tag in entry.findall("./bilder/bild"):
            image_name = (image_tag.text or "").strip()
            image_stem = os.path.splitext(image_name)[0].strip()
            image_specific_desc = _extract_image_specific_description(entry, image_name)
            merged_desc = _merge_entry_and_image_desc(desc, image_specific_desc)
            if merged_desc:
                _register_description(raw_desc, image_name, merged_desc)
                _register_description(raw_desc, image_stem, merged_desc)

    return raw_desc
