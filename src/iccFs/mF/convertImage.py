def convertImage(input_path: str, output_path: str, *, max_iter: int = 120, plateau_limit: int = 14, seed: int = 42) -> Path:
    """Backward-compatible single-image entrypoint.

    - For raster targets (e.g. ``.png``), write an annotated image plus JSON coordinates.
    - For SVG targets or missing image deps, preserve the historical embedded-raster fallback.
    """
    del max_iter, plateau_limit, seed
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.suffix.lower() == ".svg" or cv2 is None or np is None:
        target.write_text(renderEmbeddedRasterSvg(input_path), encoding="utf-8")
        return target

    img = cv2.imread(str(input_path))
    if img is None:
        raise FileNotFoundError(f"Bild konnte nicht gelesen werden: {input_path}")
    regions = detectRelevantRegions(img)
    annotated = annotateImageRegions(img, regions)
    cv2.imwrite(str(target), annotated)
    target.with_suffix(".json").write_text(json.dumps(regions, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
