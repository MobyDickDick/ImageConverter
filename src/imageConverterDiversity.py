"""Observable output comparisons; diversity never implies conversion quality."""
from __future__ import annotations

import hashlib
import json
from xml.etree import ElementTree as ET

import numpy as np


def geometry_hash(svg):
    """Ignore comments, metadata, prefixes and attribute order, retain geometry."""
    root = ET.fromstring(svg)
    def node(element):
        tag = element.tag.rsplit('}', 1)[-1]
        if tag in {'metadata', 'title', 'desc'}:
            return None
        return [tag, sorted((k, v) for k, v in element.attrib.items()
                            if not k.startswith('data-')),
                (element.text or '').strip(),
                [value for child in element if (value := node(child)) is not None]]
    return hashlib.sha256(json.dumps(node(root), ensure_ascii=False).encode('utf-8')).hexdigest()


def foreground_similarity(a, b):
    """1 - mean absolute RGB difference / 255 on the union of nonwhite pixels."""
    union = (a.min(axis=2) < 245) | (b.min(axis=2) < 245)
    if not union.any():
        return 1.
    return float(1.-np.abs(a[union].astype(float)-b[union]).mean()/255.)


def compare_results(a, b):
    from src.imageConverterSample import render_svg
    first, second = render_svg(a, 96, 96), render_svg(b, 96, 96)
    return dict(geometry_identical=geometry_hash(a) == geometry_hash(b),
                raster_identical=bool(np.array_equal(first, second)),
                foreground_similarity=foreground_similarity(first, second),
                raster_size=[96, 96])
