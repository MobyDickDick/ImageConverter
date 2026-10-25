"""Replay frozen Plan-B issue inputs with hash checks and unchanged CLI gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.run_plan_b_variations import run_battery

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT/'artifacts/evaluation/issue_backlog_v1/replays.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--issues', type=int, nargs='+')
    parser.add_argument('--seed', type=int, help='Override only for an independent holdout run')
    args = parser.parse_args(argv)
    entries = json.loads(args.manifest.read_text(encoding='utf-8'))['replays']
    if args.issues:
        missing = set(args.issues)-{entry['issue'] for entry in entries}
        if missing:
            parser.error(f'Unknown issue numbers: {sorted(missing)}')
        entries = [entry for entry in entries if entry['issue'] in args.issues]
    # Validate every input before starting the first conversion.
    for entry in entries:
        source = ROOT/entry['source_svg']
        if hashlib.sha256(source.read_bytes()).hexdigest() != entry['source_svg_sha256']:
            raise ValueError(f'SVG hash differs for issue {entry["issue"]}')
        if hashlib.sha256(entry['source_description'].encode()).hexdigest() != entry['source_description_sha256']:
            raise ValueError(f'Description hash differs for issue {entry["issue"]}')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    results = []
    for entry in entries:
        report = run_battery(ROOT/entry['source_svg'], entry['source_description'],
                             args.output_dir/str(entry['issue']),
                             seed=entry['seed'] if args.seed is None else args.seed,
                             timeout=entry['timeout_seconds'], iterations=entry['iterations'],
                             keep_debug_artifacts=True)
        results.append({'issue': entry['issue'], 'summary': report['summary'],
                        'report': f'{entry["issue"]}/report.json'})
        (args.output_dir/'summary.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    return 0 if all(result['summary']['satisfactory'] for result in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
