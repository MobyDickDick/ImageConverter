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
    def __init__(self, folder: Path, *, persistent=False):
        self.records = folder / 'attempts.jsonl'
        self.index = folder / 'attempts.idx'
        self.persistent = persistent
        self._writers = None

    def close(self):
        writers, self._writers = getattr(self,'_writers',None), None
        if writers:
            for stream in writers:
                stream.close()

    def __del__(self):
        self.close()

    @property
    def count(self):
        return self.index.stat().st_size // 8 if self.index.exists() else 0

    def append(self, svg, error, *, selection_rank=None):
        record = dict(svg=svg, mse=error / 255**2,
                      phase=os.environ.get('ICC_GUI_PREVIEW_PHASE', 'Suche'))
        if selection_rank is not None:
            record['selection_rank'] = selection_rank
        def commit(stream,index):
            offset = stream.tell()
            stream.write((json.dumps(record, ensure_ascii=False) + '\n').encode('utf-8'))
            stream.flush()
            index.write(offset.to_bytes(8, 'little'))
            index.flush()
        if self.persistent:
            if self._writers is None:
                self.records.parent.mkdir(parents=True, exist_ok=True)
                stream = self.records.open('ab')
                try:
                    index = self.index.open('a+b')
                    index.truncate(index.tell() // 8 * 8)
                    self._writers = stream,index
                except OSError:
                    stream.close()
                    raise
            commit(*self._writers)
        else:
            self.records.parent.mkdir(parents=True, exist_ok=True)
            with self.records.open('ab') as stream, self.index.open('a+b') as index:
                # Discard an incomplete offset left by a terminated worker.
                index.truncate(index.tell() // 8 * 8)
                commit(stream,index)

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

    def best(self, validator=None):
        """Read committed records with bounded memory, across worker phases."""
        import math
        best = None
        best_rank = (True, float('inf'))
        if not self.count:
            return None
        with self.index.open('rb') as index, self.records.open('rb') as stream:
            for _ in range(self.count):
                offset = index.read(8)
                if len(offset) != 8:
                    break
                stream.seek(int.from_bytes(offset, 'little'))
                try:
                    record = json.loads(stream.readline())
                    if validator is not None and not validator(record.get('svg', '')):
                        continue
                    error = float(record['mse'])
                    rank = record.get('selection_rank', (True, error))
                    if len(rank) != 2 or not math.isfinite(float(rank[1])):
                        continue
                    rank = (bool(rank[0]), float(rank[1]))
                    if (isinstance(record.get('svg'),str) and math.isfinite(error) and error >= 0
                            and (best is None or rank < best_rank)):
                        best = dict(record, mse=error)
                        best_rank = rank
                except (ValueError, KeyError, TypeError):
                    continue
        return best


class PreviewPublisher:
    def __init__(self, source: Path, output: Path, *, description=''):
        import numpy as np
        from PIL import Image

        with Image.open(source) as image:
            self.target = np.asarray(image.convert('RGB'), dtype=np.float32)
        self.output = output
        self.attempts = AttemptJournal(output.parent,persistent=True)
        self.best_error = float('inf')
        self.best_rank = (True, float('inf'))
        from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions
        try:
            self.assertions = description_assertions(description)
            self.assertion_error = False
        except ValueError:
            self.assertions, self.assertion_error = {}, True
        # Recovery is a new process. Recheck the previous phase's preview so
        # its first (usually poor) seed cannot reset the displayed incumbent.
        if output.is_file():
            try:
                import cv2
                import fitz
                from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
                h, w = self.target.shape[:2]
                raster = render_svg_to_numpy_inprocess(output.read_text(encoding='utf-8'), w, h,
                    fitz_module=fitz, np_module=np, cv2_module=cv2)
                if raster is not None and raster.shape == self.target.shape:
                    self.best_error = float(np.square(self.target-raster[:, :, ::-1].astype(np.float32)).mean())
                    self.best_rank = self.rank(output.read_text(encoding='utf-8'), raster[:, :, ::-1])
            except (OSError, ValueError, TypeError):
                pass

    def close(self):
        self.attempts.close()

    def rank(self, svg, pixels):
        from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_candidate_quality, vector_quality_score
        from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
        quality = vector_candidate_quality(self.target, pixels, svg)
        qualified = quality['passed'] and not self.assertion_error
        if qualified:
            try:
                validate_svg_assertions(svg, self.assertions)
            except ValueError:
                qualified = False
        return (not qualified, vector_quality_score(quality))

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
        rank = self.rank(svg, pixels)
        self.attempts.append(svg, error, selection_rank=rank)
        # The attempt journal remains a diagnostic record. Only the full
        # described inventory may become the displayed/downloadable draft.
        from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
        if self.assertion_error:
            return
        try:
            validate_svg_assertions(svg, self.assertions)
        except ValueError:
            return
        if self.target.min() < 220 and pixels.min() >= 245:
            return
        if rank >= self.best_rank:
            return
        self.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.output.with_suffix('.svg.tmp')
        temporary.write_text(svg, encoding='utf-8')
        temporary.replace(self.output)
        self.best_error = error
        self.best_rank = rank


def publish_preview(svg, rendered, *, bgr=True):
    """Best-effort observer; unavailable previews must never fail a conversion."""
    global _publisher, _configuration
    source = os.environ.get('ICC_GUI_PREVIEW_SOURCE')
    output = os.environ.get('ICC_GUI_PREVIEW_OUTPUT')
    if not source or not output:
        return
    try:
        description_file = os.environ.get('ICC_GUI_PREVIEW_DESCRIPTION_FILE')
        configuration = (source, output, description_file)
        if configuration != _configuration:
            if _publisher is not None:
                _publisher.close()
            description = Path(description_file).read_text(encoding='utf-8') if description_file else ''
            _publisher = PreviewPublisher(Path(source), Path(output), description=description)
            _configuration = configuration
        _publisher.consider(svg, rendered, bgr=bgr)
    except (OSError, ValueError, TypeError, ET.ParseError):
        pass
