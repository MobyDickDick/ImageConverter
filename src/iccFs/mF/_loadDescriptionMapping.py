def loadDescriptionMapping(path: str) -> dict[str, str]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xml":
        return loadDescriptionMappingFromXml(path)
    return loadDescriptionMappingFromCsv(path)
