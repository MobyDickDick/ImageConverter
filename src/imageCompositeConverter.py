"""CLI entrypoint for the image composite converter.

The previous refactor eagerly imported deep converter modules at import time.
When one of those modules is temporarily broken, even `--help` crashed before the
CLI could start. This shim keeps startup resilient by loading the heavy core
lazily only when needed.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _load_core():
    try:
        return importlib.import_module("src.iccFs.mF.imageCompositeConverterCore"), None
    except Exception as exc:  # pragma: no cover - depends on local runtime state
        return None, exc


def _fallback_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="imageCompositeConverter",
        description="Robuster Fallback-CLI, wenn der Converter-Core nicht importierbar ist.",
    )
    parser.add_argument("input", nargs="?", help="Eingabebild")
    parser.add_argument("output", nargs="?", help="Ausgabedatei")
    parser.add_argument("--bild-von", "--start-ref", dest="start_ref", default=None, help="Start-Referenz, z. B. AC0831")
    parser.add_argument("--bild-bis", "--end-ref", dest="end_ref", default=None, help="End-Referenz, z. B. AC0831")
    parser.parse_args(argv)
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    core, err = _load_core()
    if core is not None and hasattr(core, "main"):
        return int(core.main(argv))

    if err is not None and argv and not any(flag in argv for flag in ("-h", "--help")):
        print("Konnte den Converter-Core nicht laden.", file=sys.stderr)
        print(f"Ursache: {type(err).__name__}: {err}", file=sys.stderr)
        print("Fallback-CLI wird stattdessen verwendet.", file=sys.stderr)
    return _fallback_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
