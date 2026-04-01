def bootstrapRequiredImageDependencies() -> list[str]:
    missing = missingRequiredImageDependencies()
    if not missing:
        return []

    cmd = [sys.executable, "-m", "pip", "install", *missing]
    print(f"[INFO] Fehlende Bild-Abhängigkeiten gefunden: {', '.join(missing)}")
    print(f"[INFO] Installiere via: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Automatische Installation fehlgeschlagen. "
            "Bitte Abhängigkeiten manuell installieren oder Proxy/Netzwerk prüfen."
        ) from exc

    # Re-import in current process so conversion can run without restart.
    global cv2, np
    if "opencv-python-headless" in missing:
        import cv2 as _cv2

        cv2 = _cv2
    if "numpy" in missing:
        import numpy as _np

        np = _np

    return missing
