"""CLI entrypoint for the image-to-composite-SVG conversion pipeline."""

from __future__ import annotations

import sys

from src.mainFiles import image_composite_converter_runtime as _runtime

if __name__ != "__main__":
    _runtime.__file__ = __file__
    sys.modules[__name__] = _runtime


def main(argv: list[str] | None = None) -> int:
    return _runtime.main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
