"""Run unrelated axial-panel specimens through the real, reference-blocked CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.run_plan_b_variations import run_case, write_cases


def independent_cases():
    for axis in (0, 1):
        for size in (8, 24):
            for paint, colors in (
                ('blaue', ['#4060b0', '#a0c0f0', '#204080', '#6080d0']),
                ('graue', ['#707070', '#cccccc', '#505050', '#909090']),
            ):
                w, h = (64, size) if axis else (size, 64)
                coords = 'x1="0" x2="0" y1="0" y2="1"' if axis else 'x1="0" x2="1" y1="0" y2="0"'
                stops = ''.join(f'<stop offset="{t}" stop-color="{color}"/>'
                                for t, color in zip([0, .3, .8, 1], colors))
                svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w+8}" height="{h+6}">'
                       f'<defs><linearGradient id="unrelatedPaint" {coords}>{stops}</linearGradient></defs>'
                       f'<rect x="4" y="3" width="{w}" height="{h}" fill="url(#unrelatedPaint)"/></svg>')
                desc = f'Ein einzelnes Rechteck ohne Kontur. Die {paint} Füllung hat einen {"vertikalen" if axis else "horizontalen"} Farbverlauf.'
                yield dict(case_id=f'foreign_{axis}_{size}_{paint}', svg=svg, description=desc, width=w+8, height=h+6)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    cases = list(independent_cases())
    write_cases(cases, args.output_dir)
    results = []
    for case in cases:
        result = run_case(case, args.output_dir, timeout=60, iterations=64)
        results.append(result)
        print(case['case_id'], result['satisfactory'], flush=True)
    (args.output_dir/'summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return 0 if all(r['satisfactory'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
