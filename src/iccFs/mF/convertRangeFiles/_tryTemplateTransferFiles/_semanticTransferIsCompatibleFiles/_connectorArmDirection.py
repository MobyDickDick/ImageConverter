def connectorArmDirection(description: str) -> str:
    text = str(description or "").upper()
    if "LEFT" in text:
        return "left"
    if "RIGHT" in text:
        return "right"
    return "none"
