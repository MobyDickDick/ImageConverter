"""Repeat the archive acceptance with one semantic family per fresh process."""
from pathlib import Path
import argparse
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.recheck_satisfactory_archive import recheck


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    archive = ROOT/'artifacts/satisfactory_conversions'
    output = args.output_dir.resolve()
    output.mkdir()  # A repeated run must use a fresh directory.
    index = json.loads((archive/'index.json').read_text(encoding='utf-8'))
    families = {}
    for case in index['cases']:
        key = case['variant'].split('_', 1)[0] if case['execution_mode'] == 'semantic-only' else 'compatibility'
        families.setdefault(key, []).append(case)
    results, failures = [], []
    for key, cases in sorted(families.items()):
        snapshot = output/(key+'-archive')
        snapshot.mkdir()
        subset = {**index, 'case_count': len(cases), 'cases': [
            {**c, 'image': str(archive/c['image']), 'svg': str(archive/c['svg'])} for c in cases]}
        (snapshot/'index.json').write_text(json.dumps(subset)+'\n', encoding='utf-8')
        shutil.copyfile(archive/'descriptions.xml', snapshot/'descriptions.xml')
        try:
            report = recheck(snapshot, output/key)
            results.extend(report['cases'])
            print(key, report['passed'], report['case_count'], flush=True)
        except (OSError, ValueError, RuntimeError) as exc:
            failures.append(dict(family=key, error=str(exc), expected=len(cases)))
            print(key, 'FAILED', str(exc), flush=True)
        summary = dict(schema_version='satisfactory_archive_family_recheck_v1', expected=index['case_count'],
            measured=len(results), passed=sum(c['passed'] for c in results), failures=failures, cases=results,
            higher_mean_delta2=[c['variant'] for c in results if c.get('mean_delta2', 0) >
                c.get('baseline_mean_delta2', 0)+max(1e-6, c.get('baseline_mean_delta2', 0)*1e-6)])
        (output/'report.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    expected = sorted(c['variant'] for c in index['cases'])
    actual = sorted(c['variant'] for c in results)
    return 0 if not failures and actual == expected and all(c['passed'] for c in results) else 2


if __name__ == '__main__':
    raise SystemExit(main())
