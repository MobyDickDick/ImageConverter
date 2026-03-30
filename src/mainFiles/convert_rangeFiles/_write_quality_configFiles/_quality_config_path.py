from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _quality_config_path(reports_out_dir: str) -> str:
    return os.path.join(reports_out_dir, "quality_tercile_config.json")
