def _missingRequiredImageDependencies() -> list[str]:
    missing: list[str] = []
    if cv2 is None:
        missing.append("opencv-python-headless")
    if np is None:
        missing.append("numpy")
    return missing
