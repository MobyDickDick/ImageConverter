"""Compare private MuPDF rendering against independent, installed sharp/librsvg.

sharp is an audit dependency only; it is never used by conversion or scoring.
The source bytes are preserved and hashed. Both renderers receive the same
explicit pixel viewport, preserving content, viewBox, transforms and styles.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np

from tools.run_plan_b_variations import make_original_case, make_variations, render


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--svg', type=Path, required=True)
    parser.add_argument('--description-file', type=Path, required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--node', required=True)
    parser.add_argument('--sharp-module', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    svg = args.svg.read_text(encoding='utf-8')
    description = args.description_file.read_text(encoding='utf-8')
    (args.output_dir/'source.svg').write_bytes(args.svg.read_bytes())
    script = args.output_dir/'independent.cjs'
    script.write_text('''const fs = require('fs');
const sharp = require(process.argv[2]);
(async () => {
  await sharp(fs.readFileSync(process.argv[3])).flatten({background:'#ffffff'}).png().toFile(process.argv[4]);
  console.log(JSON.stringify(sharp.versions));
})();
''', encoding='utf-8')
    report = dict(source_svg=str(args.svg), source_sha256=hashlib.sha256(args.svg.read_bytes()).hexdigest(),
                  seed=args.seed, pymupdf=fitz.VersionBind, viewport='explicit pixel width/height, unchanged viewBox', cases=[])
    for case in [make_original_case(svg, description), *make_variations(svg, description, args.seed)]:
        for scale in (1, 10):
            w, h = case['width']*scale, case['height']*scale
            root = ET.fromstring(case['svg'])
            root.set('width', str(w))
            root.set('height', str(h))
            document = ET.tostring(root, encoding='unicode')
            stem = f'{case["case_id"]}-{scale}x'
            source = args.output_dir/f'{stem}.svg'
            independent = args.output_dir/f'{stem}-librsvg.png'
            source.write_text(document, encoding='utf-8')
            result = subprocess.run([args.node, str(script), args.sharp_module, str(source), str(independent)],
                                    check=True, capture_output=True, text=True)
            report['independent_renderer'] = json.loads(result.stdout)
            actual = render(document, w, h)
            expected = cv2.imread(str(independent))
            cv2.imwrite(str(args.output_dir/f'{stem}-mupdf.png'), actual)
            delta = abs(actual.astype(float)-expected)
            report['cases'].append(dict(case=case['case_id'], scale=scale, width=w, height=h,
                                       mean_absolute_error=float(delta.mean()), max_channel_error=float(delta.max()),
                                       normalized_mse=float(np.mean(delta**2)/255**2)))
    report['passed'] = all(case['normalized_mse'] < .001 for case in report['cases'])
    (args.output_dir/'summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], cases=len(report['cases']),
                         max_mse=max(c['normalized_mse'] for c in report['cases']))))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
