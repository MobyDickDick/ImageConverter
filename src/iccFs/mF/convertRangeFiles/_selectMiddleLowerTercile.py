def selectMiddleLowerTercile(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if len(rows) < 3:
        return []

    ranked = sorted(rows, key=qualitySortKey)
    first_cut = max(1, len(ranked) // 3)
    return ranked[first_cut:]
