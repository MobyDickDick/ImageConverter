def loadDescriptionMappingFromXml(path: str) -> dict[str, str]:
    raw_desc: dict[str, str] = {}
    resolved_path = resolveDescriptionXmlPath(path)
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
            registerDescription(raw_desc, root_form, desc)
        if key and desc:
            registerDescription(raw_desc, key, desc)

        for image_tag in entry.findall("./bilder/bild"):
            image_name = (image_tag.text or "").strip()
            image_stem = os.path.splitext(image_name)[0].strip()
            image_specific_desc = extractImageSpecificDescription(entry, image_name)
            merged_desc = mergeEntryAndImageDesc(desc, image_specific_desc)
            if merged_desc:
                registerDescription(raw_desc, image_name, merged_desc)
                registerDescription(raw_desc, image_stem, merged_desc)

    return raw_desc
