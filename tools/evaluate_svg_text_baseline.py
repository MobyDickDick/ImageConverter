"""Audit actual glyph bounds and original-pixel quality with MuPDF and librsvg.

This is a read-only audit of archived vectors. Baseline-only candidates are
written to a fresh output directory; historical acceptance evidence is retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from tools.run_plan_b_variations import measure_quality, render, viewport

ET.register_namespace('', 'http://www.w3.org/2000/svg')


def find_librsvg() -> str:
    executable = shutil.which('rsvg-convert')
    if not executable:
        candidate = Path('C:/msys64/ucrt64/bin/rsvg-convert.exe')
        if candidate.is_file():
            executable = str(candidate)
    if not executable:
        raise FileNotFoundError('Install librsvg rsvg-convert or pass --rsvg-convert')
    return executable


def render_librsvg(svg: str, width: int, height: int, *, executable: str | None = None):
    completed = subprocess.run(
        [executable or find_librsvg(), '--format', 'png', '--background-color', 'white',
         '--width', str(width), '--height', str(height), '-'],
        input=svg.encode('utf-8'), capture_output=True, timeout=30, check=True)
    image = cv2.imdecode(np.frombuffer(completed.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.shape[:2] != (height, width):
        raise ValueError('Independent renderer did not return the requested viewport')
    return image


def mask_bounds(mask, scale=1):
    ys, xs = np.where(mask)
    if not len(xs):
        return None
    return [float(xs.min()/scale), float(ys.min()/scale),
            float((xs.max()+1)/scale), float((ys.max()+1)/scale)]


def glyph_bounds(svg: str, render_fn=render, *, scale=8):
    """Isolate each visible glyph by subtracting the same SVG without that text.

    Text anchors, font-size boxes and neighboring stems never define these bounds.
    Coordinates are viewport pixels at the original intrinsic resolution.
    """
    _, _, _, _, width, height = viewport(svg)
    root = ET.fromstring(svg)
    root.set('width', str(width*scale))
    root.set('height', str(height*scale))
    if root.get('viewBox') is None:
        root.set('viewBox', f'0 0 {width} {height}')
    full = render_fn(ET.tostring(root, encoding='unicode'), width*scale, height*scale)
    bounds = []
    for element in root.iter():
        if element.tag.rsplit('}', 1)[-1] != 'text':
            continue
        previous = element.get('opacity')
        element.set('opacity', '0')
        blank = render_fn(ET.tostring(root, encoding='unicode'), width*scale, height*scale)
        if previous is None:
            del element.attrib['opacity']
        else:
            element.set('opacity', previous)
        mask = np.max(np.abs(full.astype(float)-blank.astype(float)), axis=2) > 25
        bounds.append(mask_bounds(mask, scale))
    return bounds


def square_glyph_position(svg: str, render_fn=render) -> bool:
    """Require visible glyph bounds inside the body's inner contour.

    Glyphs such as a lowercase p need not be centered. Their observed position
    is checked against original pixels by square_glyph_evidence instead.
    """
    root = ET.fromstring(svg)
    square = next(e for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'rect')
    x, y, w, h = (float(square.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
    # The labeled-square contract forbids transforms; emitted coordinates use
    # an identity viewBox. Reject a nonidentity viewport instead of mismeasuring.
    vx, vy, vw, vh, width, height = viewport(svg)
    if (vx, vy, vw, vh) != (0, 0, width, height):
        return False
    boxes = glyph_bounds(svg, render_fn)
    if len(boxes) != 1 or boxes[0] is None:
        return False
    left, top, right, bottom = boxes[0]
    inset = float(square.get('stroke-width', 0))/2
    return x+inset <= left < right <= x+w-inset and y+inset <= top < bottom <= y+h-inset


def square_glyph_evidence(image, svg: str, render_fn=render) -> dict:
    """Compare visible letter bounds with original contrast pixels inside the body."""
    root = ET.fromstring(svg)
    square = next(e for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'rect')
    x, y, w, h = (float(square.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
    margin = max(2., float(square.get('stroke-width', 0))*1.5)
    left, top = max(0, int(np.ceil(x+margin))), max(0, int(np.ceil(y+margin)))
    crop = image[top:min(image.shape[0], int(y+h-margin)),
                 left:min(image.shape[1], int(x+w-margin))]
    result = dict(passed=False, observed_bounds=None, rendered_bounds=None, max_bound_error=None,
                  tolerance_pixels=1.5)
    if crop.size == 0:
        return result
    colors, counts = np.unique(crop.reshape(-1, 3)//16, axis=0, return_counts=True)
    dominant = colors[int(np.argmax(counts))]
    background = np.median(crop[np.all(crop//16 == dominant, axis=2)], axis=0)
    contrast = np.linalg.norm(crop.astype(float)-background, axis=2) > 65
    count, labels, stats, _ = cv2.connectedComponentsWithStats(contrast.astype(np.uint8))
    if count < 2:
        return result
    index = 1+int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    observed = mask_bounds(labels == index)
    observed = [observed[0]+left, observed[1]+top, observed[2]+left, observed[3]+top]
    boxes = glyph_bounds(svg, render_fn)
    if len(boxes) != 1 or boxes[0] is None:
        return result
    error = float(np.max(np.abs(np.array(observed)-boxes[0])))
    result.update(observed_bounds=observed, rendered_bounds=boxes[0], max_bound_error=error,
                  passed=square_glyph_position(svg, render_fn) and error <= result['tolerance_pixels'])
    return result


def audit(archive: Path, output: Path, executable: str) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    independent = lambda svg, w, h: render_librsvg(svg, w, h, executable=executable)
    report = {'schema_version': 'svg_text_baseline_audit_v1',
              'renderer': subprocess.check_output([executable, '--version'], text=True).strip(),
              'cases': []}
    index = json.loads((archive/'index.json').read_text(encoding='utf-8'))
    for case in index['cases']:
        source = archive/case['svg']
        data = source.read_bytes()
        svg = data.decode('utf-8')
        if not any(e.tag.rsplit('}', 1)[-1] == 'text' for e in ET.fromstring(svg).iter()):
            continue
        candidate = svg.replace('dominant-baseline="middle"', 'dominant-baseline="alphabetic"')
        image = cv2.imread(str(archive/case['image']))
        h, w = image.shape[:2]
        before = measure_quality(image, svg, render_fn=independent)
        after = measure_quality(image, candidate, render_fn=independent)
        changed = candidate != svg
        (output/source.name).write_bytes(candidate.encode('utf-8'))
        record = dict(variant=case['variant'], changed=changed,
                      before_sha256=hashlib.sha256(data).hexdigest(),
                      after_sha256=hashlib.sha256(candidate.encode('utf-8')).hexdigest(),
                      production_pixels_equal=bool(np.array_equal(render(svg, w, h), render(candidate, w, h))),
                      before=before, after=after,
                      production_bounds=glyph_bounds(candidate),
                      independent_before_bounds=glyph_bounds(svg, independent),
                      independent_after_bounds=glyph_bounds(candidate, independent))
        report['cases'].append(record)
    report['summary'] = dict(text_svgs=len(report['cases']),
        changed=sum(c['changed'] for c in report['cases']),
        before_passed=sum(c['before']['satisfactory'] for c in report['cases']),
        after_passed=sum(c['after']['satisfactory'] for c in report['cases']),
        production_pixels_equal=all(c['production_pixels_equal'] for c in report['cases']))
    (output/'summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


def audit_cli(manifest_path: Path, output: Path, executable: str) -> dict:
    """Accept saved CLI outputs against original pixels with unchanged raster gates."""
    from tools.evaluate_labeled_square_recheck import labeled_square_semantics
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=False)
    root = manifest_path.parent
    independent = lambda s, w, h: render_librsvg(s, w, h, executable=executable)
    report = {'schema_version': 'svg_text_baseline_cli_v1',
              'renderer': subprocess.check_output([executable, '--version'], text=True).strip(), 'cases': []}
    for case in manifest['cases']:
        image_path, svg_path = root/case['image'], root/case['after_svg']
        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if digest != case['source_sha256']:
            raise ValueError(f"Original raster hash mismatch: {case['case_id']}")
        image = cv2.imread(str(image_path))
        svg = svg_path.read_text(encoding='utf-8')
        record = dict(case_id=case['case_id'], source=case['source'], input_sha256=digest,
                      svg_sha256=hashlib.sha256(svg_path.read_bytes()).hexdigest(),
                      semantic=bool(labeled_square_semantics(svg, manifest['label'],
                                    manifest.get('stem_direction', 'bottom'))))
        for name, renderer in [('production', render), ('independent', independent)]:
            record[name] = dict(quality=measure_quality(image, svg, render_fn=renderer),
                                glyph=square_glyph_evidence(image, svg, renderer))
        record['passed'] = (record['semantic'] and record['independent']['quality']['satisfactory']
                            and all(record[name]['glyph']['passed'] for name in ('production', 'independent')))
        report['cases'].append(record)
    report['summary'] = dict(cases=len(report['cases']), independent_passed=sum(c['passed'] for c in report['cases']),
        production_plan_b_passed=sum(c['production']['quality']['satisfactory'] for c in report['cases']))
    (output/'summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=Path('artifacts/satisfactory_conversions'))
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--rsvg-convert')
    parser.add_argument('--manifest', type=Path, help='Accept fresh labeled-square CLI outputs instead of inventorying the archive')
    args = parser.parse_args()
    if args.manifest:
        report = audit_cli(args.manifest, args.output_dir, args.rsvg_convert or find_librsvg())
        print(json.dumps(report['summary']))
        return 0 if report['summary']['cases'] and report['summary']['independent_passed'] == report['summary']['cases'] else 1
    report = audit(args.archive, args.output_dir, args.rsvg_convert or find_librsvg())
    print(json.dumps(report['summary']))
    # Inventory failures are preserved and reported; they are not positive acceptance.
    return 0 if report['summary']['after_passed'] == report['summary']['text_svgs'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
