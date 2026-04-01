def successfulConversionSnapshotPaths(reports_out_dir: str, variant: str) -> dict[str, Path]:
    base_dir = successfulConversionSnapshotDir(reports_out_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return {
        'svg': base_dir / f'{variant}.svg',
        'log': base_dir / f'{variant}_element_validation.log',
        'metrics': base_dir / f'{variant}.json',
    }
