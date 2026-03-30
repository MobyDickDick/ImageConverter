def _load_description_mapping(path: str) -> dict[str, str]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xml":
        return _load_description_mapping_from_xml(path)
    return _load_description_mapping_from_csv(path)
