"""Polish-notation alias module for ``image_composite_converter_core``."""

from __future__ import annotations

import src.iccFs.mF.image_composite_converter_core as _legacy

for _name in dir(_legacy):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_legacy, _name)
