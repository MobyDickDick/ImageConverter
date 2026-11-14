"""Publish improving rendered SVG candidates for the local GUI only.

Uses the raster already computed by the search, without another render. Preview
scores never influence candidate selection or the converter's quality gates.
"""
from __future__ import annotations

import os
from pathlib import Path
from xml.etree import ElementTree as ET

_publisher = None
_configuration = None


class PreviewPublisher:
    def __init__(self, source: Path, output: Path):
        import numpy as np
        from PIL import Image

        with Image.open(source) as image:
            self.target = np.asarray(image.convert('RGB'), dtype=np.float32)
        self.output = output
        self.best_error = float('inf')

    def consider(self, svg, rendered, *, bgr=True):
        import numpy as np

        if rendered is None or rendered.shape != self.target.shape:
            return
        pixels = rendered[:, :, ::-1] if bgr else rendered
        # Empty search seeds are not useful previews of a nonempty source.
        if self.target.min() < 220 and pixels.min() >= 245:
            return
        error = float(np.square(self.target-pixels.astype(np.float32)).mean())
        if not np.isfinite(error) or error >= self.best_error - 1e-7:
            return
        root = ET.fromstring(svg)
        if root.tag.rsplit('}', 1)[-1] != 'svg' or any(
                node.tag.rsplit('}', 1)[-1] in {'image', 'foreignObject', 'script'}
                for node in root.iter()):
            return
        self.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.output.with_suffix('.svg.tmp')
        temporary.write_text(svg, encoding='utf-8')
        temporary.replace(self.output)
        self.best_error = error


def publish_preview(svg, rendered, *, bgr=True):
    """Best-effort observer; unavailable previews must never fail a conversion."""
    global _publisher, _configuration
    source = os.environ.get('ICC_GUI_PREVIEW_SOURCE')
    output = os.environ.get('ICC_GUI_PREVIEW_OUTPUT')
    if not source or not output:
        return
    try:
        configuration = (source, output)
        if configuration != _configuration:
            _publisher = PreviewPublisher(Path(source), Path(output))
            _configuration = configuration
        _publisher.consider(svg, rendered, bgr=bgr)
    except (OSError, ValueError, TypeError, ET.ParseError):
        pass
