"""Seal unrun real-family annotations without importing or running the converter."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'real_composition_holdout_freeze_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def inside(root, name):
    path = Path(name)
    target = (root/path).resolve()
    if path.is_absolute() or PureWindowsPath(name).drive or not target.is_relative_to(root.resolve()):
        raise ValueError('Path must stay inside evidence folder')
    return target


def validate_annotations(data):
    if data.get('schema') != 'real_composition_holdout_families_v1':
        raise ValueError('Unknown annotation schema')
    policy = data.get('evaluation_policy', {})
    if (policy.get('status') != 'sealed_unrun' or policy.get('converter_trials') != 0
            or policy.get('positive_acceptance') is not None):
        raise ValueError('Only unrun families can be frozen')
    cases = data['cases']
    if len(cases) < 2 or len({c['family'] for c in cases}) != len(cases):
        raise ValueError('At least two distinct families required')
    if len({c['file'].casefold() for c in cases}) != len(cases):
        raise ValueError('Duplicate original')
    if len({c['source_sha256'] for c in cases}) != len(cases):
        raise ValueError('Renamed originals are not independent families')
    members = [name.casefold() for case in cases for name in case['family_members']]
    if len(set(members)) != len(members):
        raise ValueError('A descendant cannot belong to multiple families')
    for case in cases:
        width, height = case['size']
        if case['split'] != 'holdout' or not case['family_members'] or case['file'] not in case['family_members']:
            raise ValueError('Original and all known descendants must stay in holdout')
        ids = {obj['id'] for obj in case['expected_objects']}
        if len(ids) != len(case['expected_objects']) or not ids:
            raise ValueError('Unique object IDs required')
        for obj in case['expected_objects']:
            x, y, w, h = obj['visible_bbox']
            if not (all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y, w, h))
                    and 0 <= x < width and 0 <= y < height and w > 0 and h > 0
                    and x+w <= width and y+h <= height):
                raise ValueError('Invalid visible object bounds')
            for px, py in obj.get('polygon', []):
                if not (x <= px <= x+w and y <= py <= y+h):
                    raise ValueError('Polygon leaves visible bounds')
        for relation in case['relations']:
            if not relation['objects'] or not set(relation['objects']) <= ids:
                raise ValueError('Unknown relation object')
        if not case['acceptance_gaps']:
            raise ValueError('Record the limits of the current independent oracle')


def audit_sources(data, revision):
    # POSIX ERE boundaries avoid matching e.g. "guardrails" for "Rail".
    # Explicit letter pairs also make git log -G case insensitive.
    stems = []
    for case in data['cases']:
        stems.append(''.join('['+c.lower()+c.upper()+']' if c.isalpha() else re.escape(c)
                             for c in Path(case['file']).stem))
    tokens = '(^|[^[:alnum:]_])('+'|'.join(stems)+')([^[:alnum:]_]|$)'
    scopes = ['src', 'tests', 'tools', 'config', 'docs']
    commands = [
        ['git', 'grep', '-n', '-I', '-i', '-E', tokens, revision, '--', *scopes],
        ['git', 'log', revision, '--format=%h %s', '-G', tokens, '--', *scopes],
    ]
    results = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                encoding='utf-8', check=False)
        allowed = (0, 1) if command[1] == 'grep' else (0,)
        if result.returncode not in allowed:
            raise ValueError('Source audit failed: '+result.stderr)
        results.append(dict(command=command, exit_code=result.returncode, output=result.stdout))
    return dict(revision=revision, searches=results,
                limitation='Tracked source/history search only; historical catalogue and batch exposure is not excluded. Generic word matches require manual interpretation.')


def freeze(annotations, output):
    data = json.loads(annotations.read_text(encoding='utf-8'))
    validate_annotations(data)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    runtime = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted((ROOT/'src').rglob('*.py'))}
    audit = audit_sources(data, revision)
    # Validate originals before creating an evidence folder.
    for case in data['cases']:
        source = inside(ROOT/'artifacts/images_to_convert', case['file'])
        if digest(source) != case['source_sha256']:
            raise ValueError('Original source changed')
        with Image.open(source) as im:
            if list(im.size) != case['size']:
                raise ValueError('Original size changed')
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(annotations, output/'annotations.json')
    write_json(output/'source_audit.json', audit)
    write_json(output/'runtime.json', runtime)
    for index, case in enumerate(data['cases']):
        folder = output/f'family_{index:02d}'
        folder.mkdir()
        source = inside(ROOT/'artifacts/images_to_convert', case['file'])
        shutil.copyfile(source, folder/'original.jpg')
        with Image.open(source) as im:
            im.convert('RGB').save(folder/'input.png')
        (folder/'description.txt').write_bytes((case['description']+'\n').encode('utf-8'))
    write_json(output/'manifest.json', dict(
        schema=SCHEMA, created_utc=datetime.now(timezone.utc).isoformat(), revision=revision,
        status='sealed_unrun', converter_executed=False, accepted=None,
        files={p.relative_to(output).as_posix(): digest(p)
               for p in sorted(output.rglob('*')) if p.is_file()}))
    return verify(output/'manifest.json', check_current=True)


def verify(manifest_path, check_current=False):
    root = manifest_path.parent.resolve()
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if (manifest.get('schema') != SCHEMA or manifest.get('status') != 'sealed_unrun'
            or manifest.get('converter_executed') is not False or manifest.get('accepted') is not None):
        raise ValueError('A freeze is not a conversion result')
    files = manifest['files']
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and p.relative_to(root).as_posix() not in ('manifest.json', 'README.md')}
    if actual != set(files):
        raise ValueError('Missing or unexpected evidence')
    for name, expected in files.items():
        if digest(inside(root, name)) != expected:
            raise ValueError('Changed evidence: '+name)
    data = json.loads((root/'annotations.json').read_text(encoding='utf-8'))
    validate_annotations(data)
    required = {'annotations.json', 'runtime.json', 'source_audit.json'}
    for index, case in enumerate(data['cases']):
        prefix = f'family_{index:02d}/'
        required.update(prefix+n for n in ('original.jpg', 'input.png', 'description.txt'))
        original, decoded = root/prefix/'original.jpg', root/prefix/'input.png'
        if digest(original) != case['source_sha256']:
            raise ValueError('Wrong original')
        with Image.open(original) as a, Image.open(decoded) as b:
            if list(a.size) != case['size'] or a.size != b.size or a.convert('RGB').tobytes() != b.convert('RGB').tobytes():
                raise ValueError('Decoded pixels changed')
        if (root/prefix/'description.txt').read_text(encoding='utf-8') != case['description']+'\n':
            raise ValueError('Description changed')
    if set(files) != required:
        raise ValueError('Incomplete freeze inventory')
    audit = json.loads((root/'source_audit.json').read_text(encoding='utf-8'))
    if audit['revision'] != manifest['revision']:
        raise ValueError('Audit revision changed')
    runtime = json.loads((root/'runtime.json').read_text(encoding='utf-8'))
    if not runtime or any(not name.startswith('src/') for name in runtime):
        raise ValueError('Missing runtime snapshot')
    if check_current:
        current = {p.relative_to(ROOT).as_posix(): digest(p) for p in (ROOT/'src').rglob('*.py')}
        if current != runtime:
            raise ValueError('Runtime changed since freeze')
    return dict(status='sealed_unrun', families=len(data['cases']), converter_executed=False,
                accepted=None, current_runtime_checked=check_current)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze', type=Path)
    mode.add_argument('--verify', type=Path)
    parser.add_argument('--annotations', type=Path, default=ROOT/'config/real_composition_holdout_families.json')
    parser.add_argument('--check-current-runtime', action='store_true')
    args = parser.parse_args()
    result = freeze(args.annotations, args.freeze) if args.freeze else verify(args.verify, args.check_current_runtime)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
