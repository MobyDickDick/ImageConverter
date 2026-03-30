from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _successful_conversion_snapshot_dir(reports_out_dir: str) -> Path:
    """Directory used to persist best-of artifacts for successful conversions."""
    return Path(reports_out_dir) / 'successful_conversions_bestlist'
