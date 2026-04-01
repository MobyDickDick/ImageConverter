def connectorStemDirection(description: str) -> str:
    text = str(description or "").upper()
    if "UP" in text:
        return "up"
    if "DOWN" in text:
        return "down"
    return "none"
