#!/usr/bin/env python3
"""Convert Inkscape-authored SVG to a cleaner plain SVG subset.

Keeps visual elements, removes editor metadata (inkscape/sodipodi namespaces,
attributes and tags), and optionally writes in-place.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def sanitize_svg(svg_text: str) -> str:
    text = svg_text
    text = re.sub(r"<\?xml[^>]*\?>\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<!-- Created with Inkscape[^>]*-->\s*", "", text, flags=re.IGNORECASE)

    text = re.sub(r"<\/?(?:sodipodi|inkscape):[^>]*?>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\sxmlns:(?:inkscape|sodipodi)=\"[^\"]*\"", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\sxmlns:(?:inkscape|sodipodi)='[^']*'", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s(?:sodipodi|inkscape):[\w.-]+=\"[^\"]*\"", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s(?:sodipodi|inkscape):[\w.-]+='[^']*'", "", text, flags=re.IGNORECASE)

    text = re.sub(r">\s+<", "><", text).strip()
    return text + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Strip Inkscape/Sodipodi metadata from SVG files.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()

    if args.in_place and args.output is not None:
        parser.error("Use either --in-place or --output, not both.")

    src = args.input
    out = src if args.in_place else (args.output or src.with_name(src.stem + "_plain.svg"))

    sanitized = sanitize_svg(src.read_text(encoding="utf-8"))
    out.write_text(sanitized, encoding="utf-8")
    print(f"Wrote sanitized SVG: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
