from pathlib import Path


def _default_converted_symbols_root() -> str:
    repo_root = Path(__file__).resolve().parents[4]
    return str(repo_root / "artifacts" / "converted_images")
