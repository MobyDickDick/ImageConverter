"""Verify frozen input/vector hashes and the two independent acceptance runs."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.evaluate_striped_panel_disk_recheck import evaluate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = Path(__file__).resolve().parent
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    saved = json.loads((folder/'report.json').read_text(encoding='utf-8'))
    current = evaluate(manifest, folder)
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in current['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in current['strict_pixel_gates'].values())
    assert current['evidence'] == saved['evidence']
    for item in json.loads((folder/'source_inventory.json').read_text(encoding='utf-8')):
        assert digest(ROOT/'artifacts/images_to_convert'/item['source']) == item['sha256']
    fields = ('case_id','input_sha256','output_sha256','metrics','complexity','satisfactory','failures','blocked_svg_reads')
    results = []
    for index in (1, 2):
        run = folder/'plan_b'/f'run_{index}'
        report = json.loads((run/'report.json').read_text(encoding='utf-8'))
        assert report['summary'] == dict(completed=17, failed=0, passed=17, required=17, satisfactory=True)
        assert digest(run/'source.png') == report['source_image_sha256']
        for case in report['cases']:
            assert not case['blocked_svg_reads'] and case['satisfactory']
            assert digest(run/case['output_svg']) == case['output_sha256']
            assert digest(run/case['reference_svg']) == case['reference_svg_sha256']
        results.append([{k:case[k] for k in fields} for case in report['cases']])
    assert results[0] == results[1]
    print('Saved gates, four source hashes, and two identical 17-case CLI runs verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
