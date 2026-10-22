"""Recheck local CLI evidence before writing the compact gradient-scene summary."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.evaluate_layered_scene import verify_report

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(local):
    specs = {
        'parent-real': ('frozen-real', 'parent-real', False),
        'first-plan-b': ('final-variations-inputs', 'final-variations', False),
        'wording-corrected-plan-b': ('final-variations-inputs', 'accepted-variations', False),
        'refined-plan-b': ('final-variations-inputs', 'geometry-refined-variations', True),
        'real': ('corrected-real', 'accepted-real', True),
        'independent': ('sealed-after-freeze', 'accepted-after-freeze', True),
        'independent-rename': ('sealed-after-freeze', 'accepted-after-freeze-rename', True),
        'sealed-plan-b': ('sealed-plan-b', 'accepted-sealed-plan-b', True),
        'negative': ('negative-inputs', 'negative-cli', True),
    }
    groups = {}
    for name, (inputs, outputs, final) in specs.items():
        inputs, outputs = local/inputs, local/outputs
        result = verify_report(inputs, outputs)
        report = json.loads((outputs/'report.json').read_text(encoding='utf-8'))
        if final:
            for path, expected in report['source_sha256'].items():
                if digest(ROOT/path) != expected:
                    raise ValueError('Final evidence used a different runtime: '+path)
        groups[name] = dict(accepted=result['accepted'], completed=result['completed'],
                           input_manifest_sha256=digest(inputs/'manifest.json'), report_sha256=digest(outputs/'report.json'),
                           source_manifest_sha256=hashlib.sha256(json.dumps(report['source_sha256'], sort_keys=True).encode()).hexdigest())
    a = json.loads((local/'accepted-after-freeze/report.json').read_text(encoding='utf-8'))['cases']
    b = json.loads((local/'accepted-after-freeze-rename/report.json').read_text(encoding='utf-8'))['cases']
    if [c['output_sha256'] for c in a] != [c['output_sha256'] for c in b]:
        raise ValueError('Renamed sources changed vectors')
    if any(groups[key]['accepted'] != groups[key]['completed'] for key in ('independent', 'independent-rename', 'sealed-plan-b')):
        raise ValueError('Final synthetic acceptance incomplete')
    if groups['real']['accepted'] != 2 or groups['negative']['accepted'] != 0:
        raise ValueError('Known real/negative outcomes changed')
    return dict(schema='gradient_scene_evaluation_v1', groups=groups, renamed_vectors_byte_identical=True,
                real_family_status='Known development families only; two catalogue variants of one nested-panel topology are not two new real families.',
                source_inputs='Raster pixels and independent descriptions; reference SVG reads forbidden in conversion workers.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', type=Path, default=ROOT/'.tmp/real06')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    result = summarize(args.local)
    if args.verify_only:
        if json.loads(args.output.read_text(encoding='utf-8')) != result:
            raise ValueError('Compact summary differs from verified evidence')
    else:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Verified gradient-scene CLI evidence')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
