def _loadDescriptionMapping(path: str) -> dict[str, str]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xml":
        return _loadDescriptionMappingFromXml(path)
    return _loadDescriptionMappingFromCsv(path)
