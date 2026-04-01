def successfulConversionSnapshotDir(reports_out_dir: str) -> Path:
    """Directory used to persist best-of artifacts for successful conversions."""
    return Path(reports_out_dir) / 'successful_conversions_bestlist'
