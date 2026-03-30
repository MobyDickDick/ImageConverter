from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _diff_output_dir(output_root: str) -> str:
    return os.path.join(output_root, "diff_pngs")
