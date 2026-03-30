def _auto_detect_csv_path(folder_path: str) -> str | None:
    """Best-effort table lookup for CLI compatibility mode.

    Priority:
    1) CSV/TSV/XML files directly inside ``folder_path``
    2) CSV/TSV/XML files in the parent directory of ``folder_path``
    """
    candidates: list[str] = []
    roots = [folder_path, os.path.dirname(folder_path)]
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            lower = name.lower()
            if lower.endswith(".csv") or lower.endswith(".tsv") or lower.endswith(".xml"):
                candidates.append(os.path.join(root, name))
        if candidates:
            break

    if not candidates:
        return None

    # Prefer obvious mapping files if several exist.
    preferred = [
        p
        for p in candidates
        if any(tag in os.path.basename(p).lower() for tag in ("reference", "roundtrip", "export", "mapping"))
    ]
    return preferred[0] if preferred else candidates[0]
