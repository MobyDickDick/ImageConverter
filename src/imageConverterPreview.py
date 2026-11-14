"""Publish rendered SVG attempts and improving previews for the local GUI only.

Uses the raster already computed by the search, without another render. Preview
scores never influence candidate selection or the converter's quality gates.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from xml.etree import ElementTree as ET

_publisher = None
_configuration = None


class AttemptJournal:
    """Append-only SVG records with fixed-size offsets for bounded page reads.

    Workers run sequentially. Commit an offset only after its full record has
    been flushed, so a cancelled worker cannot expose a partial SVG.
    """
    def __init__(self, folder: Path):
        self.records = folder / 'attempts.jsonl'
        self.index = folder / 'attempts.idx'

    @property
    def count(self):
        return self.index.stat().st_size // 8 if self.index.exists() else 0

    def append(self, svg, error):
        record = dict(svg=svg, mse=error / 255**2,
                      phase=os.environ.get('ICC_GUI_PREVIEW_PHASE', 'Suche'))
        self.records.parent.mkdir(parents=True, exist_ok=True)
        with self.records.open('ab') as stream:
            offset = stream.tell()
            stream.write((json.dumps(record, ensure_ascii=False) + '\n').encode('utf-8'))
            stream.flush()
        with self.index.open('a+b') as stream:
            # Discard an incomplete offset left by a terminated worker.
            stream.truncate(stream.tell() // 8 * 8)
            stream.write(offset.to_bytes(8, 'little'))

    def read(self, number):
        if not 1 <= number <= self.count:
            raise IndexError(number)
        with self.index.open('rb') as index, self.records.open('rb') as stream:
            index.seek((number - 1) * 8)
            stream.seek(int.from_bytes(index.read(8), 'little'))
            return dict(json.loads(stream.readline()), number=number)

    def page(self, after=0, limit=12):
        total = self.count
        items = []
        for number in range(after + 1, min(total, after + limit) + 1):
            record = self.read(number)
            record.pop('svg')
            items.append(record)
        return dict(total=total, attempts=items)


class PreviewPublisher:
    def __init__(self, source: Path, output: Path):
        import numpy as np
        from PIL import Image

        with Image.open(source) as image:
            self.target = np.asarray(image.convert('RGB'), dtype=np.float32)
        self.output = output
        self.attempts = AttemptJournal(output.parent)
        self.best_error = float('inf')

    def consider(self, svg, rendered, *, bgr=True):
        import numpy as np

        if rendered is None or rendered.shape != self.target.shape:
            return
        pixels = rendered[:, :, ::-1] if bgr else rendered
        error = float(np.square(self.target-pixels.astype(np.float32)).mean())
        if not np.isfinite(error):
            return
        root = ET.fromstring(svg)
        if root.tag.rsplit('}', 1)[-1] != 'svg' or any(
                node.tag.rsplit('}', 1)[-1] in {'image', 'foreignObject', 'script'}
                for node in root.iter()):
            return
        # Keep every rendered native attempt, including worse/duplicate/blank
        # search seeds. Best-result selection below remains independent.
        self.attempts.append(svg, error)
        if self.target.min() < 220 and pixels.min() >= 245:
            return
        if error >= self.best_error - 1e-7:
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
