from pathlib import Path


def _defaultConvertedSymbolsRoot() -> str:
    repo_root = Path(__file__).resolve().parents[4]
    return str(repo_root / "artifacts" / "converted_images")
