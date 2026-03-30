from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _default_converted_symbols_root() -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(repo_root, "artifacts", "converted_images")
