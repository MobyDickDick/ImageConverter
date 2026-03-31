def _load_description_mapping_from_csv(path: str) -> dict[str, str]:
    raw_desc: dict[str, str] = {}
    if not os.path.exists(path):
        return raw_desc

    with open(path, mode="r", encoding="utf-8-sig") as f:
        content = f.read()
        delimiter = ";" if ";" in content.split("\n", 1)[0] else ","
        f.seek(0)
        reader = csv.reader(f, delimiter=delimiter)
        headers = next(reader, None)
        if not headers:
            return raw_desc

        root_idx, desc_idx = -1, -1
        for i, h in enumerate(headers):
            low = h.lower()
            if "wurzelform" in low:
                root_idx = i
            elif "beschreibung" in low:
                desc_idx = i
        if root_idx == -1:
            root_idx = 1
        if desc_idx == -1:
            desc_idx = 2

        for row_number, row in enumerate(reader, start=2):
            if len(row) > max(root_idx, desc_idx):
                root_name = row[root_idx].strip()
                desc = row[desc_idx].strip()
                if root_name:
                    raw_desc[root_name] = desc
                continue

            expected_columns = max(root_idx, desc_idx) + 1
            raise DescriptionMappingError(
                (
                    "Description table row is missing expected columns "
                    f"(expected at least {expected_columns}, got {len(row)})."
                ),
                span=SourceSpan(path=path, line=row_number, column=1),
            )
    return raw_desc
