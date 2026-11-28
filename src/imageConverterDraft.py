"""Bounded native-vector draft when the description compiler has no solution.

The image supplies colour regions, including holes and lettering. These paths
are a visual draft, not a claim that semantic objects have been reconstructed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time


def region_svg(image, colors):
    import numpy as np
    from PIL import Image

    height, width = image.shape[:2]
    reduced = Image.fromarray(image)
    reduced.thumbnail((256, 256))
    palette_image = reduced.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
    labels = np.asarray(palette_image)
    palette = palette_image.getpalette()
    # Run-length regions use exact pixel edges. Unlike contour-centre tracing,
    # this preserves one-pixel lines and holes in tiny catalog images.
    paths = {}
    for y, row in enumerate(labels):
        edges = np.flatnonzero(np.r_[True, row[1:] != row[:-1], True])
        for left, right in zip(edges[:-1], edges[1:]):
            label = int(row[left])
            paths.setdefault(label, []).append(f'M{left} {y}h{right-left}v1h{left-right}z')
    sx, sy = width / labels.shape[1], height / labels.shape[0]
    nodes = []
    for label, segments in paths.items():
        color = '#' + ''.join(f'{v:02x}' for v in palette[label*3:label*3+3])
        for start in range(0, len(segments), 4000):
            nodes.append(f'<path fill="{color}" d="{"".join(segments[start:start+4000])}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"><g transform="scale({sx} {sy})" '
            f'shape-rendering="crispEdges">{"".join(nodes)}</g></svg>')


def draft(source: Path, output: Path, *, deadline: float):
    import numpy as np
    from PIL import Image
    from src.imageConverterSample import render_svg
    from src.imageConverterPreview import atomic_preview
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_candidate_quality, vector_quality_score

    image = np.asarray(Image.open(source).convert('RGB'))
    height, width = image.shape[:2]
    best_rank = None
    report = dict(passed=False, model_confirmed=False, evaluations=0,
                  stop_reason='sources_exhausted', source='image_regions')
    for colors in (4, 8, 16, 32, 64):
        if time.time() >= deadline:
            report['stop_reason'] = 'time_limit'
            break
        svg = region_svg(image, colors)
        rendered = render_svg(svg, width, height)
        quality = vector_candidate_quality(image, rendered, svg)
        report['evaluations'] += 1
        rank = (not quality['passed'], vector_quality_score(quality))
        if best_rank is None or rank < best_rank:
            best_rank = rank
            atomic_preview(output, svg)
            atomic_preview(output.with_name('live-preview.svg'), svg)
            report.update(pixel_quality=quality, colors=colors)
            output.with_suffix('.json').write_text(json.dumps(report), encoding='utf-8')
    output.with_suffix('.json').write_text(json.dumps(report), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    draft(args.source, args.output, deadline=args.deadline)


if __name__ == '__main__':
    main()
