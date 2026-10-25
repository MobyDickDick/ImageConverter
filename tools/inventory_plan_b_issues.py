"""Group a downloaded GitHub issue snapshot without changing GitHub state."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re


def inventory(issues: list[dict]) -> dict:
    groups = defaultdict(list)
    phases = Counter()
    for issue in issues:
        match = re.search(r'```json\s*\n(.*?)\n```', issue.get('body') or '', re.DOTALL)
        evidence = json.loads(match[1]) if match else {}
        failures = sorted({reason for case in evidence.get('failures', [])
                           for reason in case.get('failures', [])})
        technical = {'converter_error', 'conversion_timeout', 'conversion_or_measurement_error',
                     'missing_or_ambiguous_output', 'reference_svg_access'}
        phase = ('execution' if technical.intersection(failures)
                 or evidence.get('phase') == 'execution' else evidence.get('phase', 'unknown'))
        phases[phase] += 1
        # Same image/description pairs can still have distinct replay seeds.
        # Grouping is an investigation aid, never proof of a duplicate cause.
        source = Path(evidence.get('source_svg', '')).name
        key = (source, evidence.get('source_description_sha256'), phase)
        row = {'issue': issue.get('issue_number', issue.get('number')),
               'url': issue.get('url'), 'seed': evidence.get('seed'),
               'source_svg_sha256': evidence.get('source_svg_sha256'),
               'passed': evidence.get('summary', {}).get('passed'), 'failures': failures}
        groups[key].append(row)
    return {'issue_count': len(issues), 'phase_counts': dict(phases),
            'investigation_group_count': len(groups),
            'grouping_note': 'Same source and description, separated by phase; shared causes require reproduction.',
            'groups': [{'source': source, 'description_sha256': description, 'phase': phase,
                        'issues': rows}
                       for (source, description, phase), rows in sorted(groups.items(), key=lambda pair: str(pair[0]))]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
    result = inventory(snapshot if isinstance(snapshot, list) else snapshot['issues'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({key:value for key,value in result.items() if key != 'groups'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
