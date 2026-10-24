"""Replay saved CLI decisions and check runtime/archive integrity from the repo root."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.evaluate_layered_scene import verify_report

os.environ['IMAGE_CONVERTER_ISOLATE_SVG_RENDER'] = '0'
base = Path(__file__).resolve().parent
evaluation = ROOT/'artifacts/evaluation'
cohorts = [
    (base/'inputs', 'before', 0, 12),
    (base/'inputs', 'after', 12, 12),
    (base/'additional', 'additional_cli', 12, 12),
    (base/'plan_b', 'plan_b_cli', 17, 17),
    (evaluation/'overlap_composition_v1/inputs', 'existing_overlap_cli', 12, 12),
    (evaluation/'rounded_outlines_v1/inputs', 'existing_outlines_cli', 12, 12),
    (evaluation/'rounded_composition_v1/development', 'existing_rounded_cli', 12, 12),
    (evaluation/'component_splits_v1/input', 'existing_split_cli', 20, 20),
    (evaluation/'residual_scene_v1/final-input', 'existing_residual_cli', 7, 9),
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

summary = {}
for inputs, output, accepted, count in cohorts:
    result = verify_report(inputs, base/output, write_verification=False)
    assert (result['accepted'], result['completed']) == (accepted, count), output
    report = json.loads((base/output/'report.json').read_text(encoding='utf-8'))
    if output != 'before':
        for name, expected in report['source_sha256'].items():
            assert digest(ROOT/name.replace('\\', '/')) == expected, name
    summary[output] = dict(accepted=accepted, total=count)

archive = ROOT/'artifacts/satisfactory_conversions'
index = json.loads((archive/'index.json').read_text(encoding='utf-8'))
for case in index['cases']:
    for kind in ('image', 'svg'):
        assert digest(archive/case[kind]) == case[kind+'_sha256'], case['variant']
print(json.dumps(dict(cohorts=summary, archive_pairs=len(index['cases'])), indent=2))
