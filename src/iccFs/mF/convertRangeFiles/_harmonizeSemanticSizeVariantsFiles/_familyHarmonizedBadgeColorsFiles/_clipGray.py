def clipGray(value: float) -> int:
    return int(max(0, min(255, round(float(value)))))
