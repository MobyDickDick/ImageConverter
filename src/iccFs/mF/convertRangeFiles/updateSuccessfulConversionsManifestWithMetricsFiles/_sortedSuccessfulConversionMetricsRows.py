def sortedSuccessfulConversionMetricsRows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(rows or [], key=lambda row: str(row.get("filename", "")))
