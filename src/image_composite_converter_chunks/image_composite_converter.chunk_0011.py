                raw_desc[candidate] = normalized_desc

    def _merge_entry_and_image_desc(entry_desc: str, image_desc: str) -> str:
        e = entry_desc.strip()
        i = image_desc.strip()
        if e and i and e != i:
            return f"{e} {i}".strip()
        return i or e

    def _extract_image_specific_description(entry: ET.Element, image_name: str) -> str:
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

    for entry in root.findall(".//entry"):
        desc = (entry.findtext("beschreibung") or "").strip()
        root_form = (entry.findtext("wurzelform") or "").strip()
        key = str(entry.attrib.get("key", "")).strip()

        if root_form and desc:
            _register_description(root_form, desc)
        if key and desc:
            _register_description(key, desc)

        for image_tag in entry.findall("./bilder/bild"):
            image_name = (image_tag.text or "").strip()
            image_stem = os.path.splitext(image_name)[0].strip()
            image_specific_desc = _extract_image_specific_description(entry, image_name)
            merged_desc = _merge_entry_and_image_desc(desc, image_specific_desc)
            if merged_desc:
                _register_description(image_name, merged_desc)
                _register_description(image_stem, merged_desc)

    return raw_desc


def _resolve_description_xml_path(path: str) -> str | None:
    candidate = Path(path)
    if candidate.exists():
        return str(candidate)

    basename = candidate.name
    if not basename:
        return None

    fallback_candidates = [
        Path("artifacts/descriptions") / basename,
        Path("artifacts/images_to_convert") / basename,
    ]
    for fallback in fallback_candidates:
        if fallback.exists():
            return str(fallback)
    return None


def _required_vendor_packages() -> list[str]:
    return [
        "numpy",
        "opencv-python-headless",
        "Pillow",
        "PyMuPDF",
    ]


def build_linux_vendor_install_command(
    vendor_dir: str = "vendor",
    platform_tag: str = "manylinux2014_x86_64",
    python_version: str | None = None,
) -> list[str]:
    if python_version is None:
        python_version = f"{sys.version_info.major}{sys.version_info.minor}"

    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        vendor_dir,
