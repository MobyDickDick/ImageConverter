def _merge_entry_and_image_desc(entry_desc: str, image_desc: str) -> str:
    e = entry_desc.strip()
    i = image_desc.strip()
    if e and i and e != i:
        return f"{e} {i}".strip()
    return i or e
