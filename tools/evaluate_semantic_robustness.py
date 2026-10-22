"""Frozen real rasters, explicit wording variants and independent saved-SVG checks.

Annotations are evaluation inputs only. The converter receives a neutral PNG
and one description; neither reference SVGs nor this manifest enter its input.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.prepare_practical_benchmark import ROOT, contained, digest, write_json

DEFAULT_SELECTION = ROOT / 'config/semantic_robustness_families.json'


def source_hashes(root: Path = ROOT) -> dict:
    # New modules/configuration count even before the branch is committed.
    return {p.relative_to(root).as_posix(): digest(p) for folder in ('src', 'config')
            for p in sorted((root/folder).rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def export_baseline(output: Path, ref: str) -> dict:
    import io
    import shutil
    import subprocess
    import zipfile
    revision = subprocess.check_output(['git','rev-parse',ref+'^{commit}'], cwd=ROOT, text=True).strip()
    archive = subprocess.check_output(['git','archive','--format=zip',revision,'src','config'],cwd=ROOT)
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        source.extractall(output)
    shutil.copytree(ROOT/'tools',output/'tools',ignore=shutil.ignore_patterns('__pycache__'))
    # The dependency loader requires a repo-local candidate directory. Actual
    # binary packages come from the same explicit dependency paths in both arms.
    (output/'.venv/Lib/site-packages').mkdir(parents=True)
    proof = dict(revision=revision, runtime_sha256=source_hashes(output),
                 tools_sha256={p.relative_to(output).as_posix():digest(p) for p in (output/'tools').rglob('*.py')})
    write_json(output/'export.json',proof)
    return proof


def prepare(output: Path, selection: Path = DEFAULT_SELECTION) -> dict:
    import cv2
    archive = ROOT / 'artifacts/satisfactory_conversions'
    index = {c['variant']: c for c in json.loads((archive/'index.json').read_text(encoding='utf-8'))['cases']}
    config = json.loads(selection.read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=False)
    (output/'rasters').mkdir()
    cases = []
    for number, family in enumerate(config['families']):
        source = index[family['variant']]
        path = contained(archive, source['image'])
        if digest(path) != source['image_sha256']:
            raise ValueError('Original raster changed')
        pixels = cv2.imread(str(path))
        image = output/'rasters'/f'image_{number:02d}.png'
        if pixels is None or not cv2.imwrite(str(image), pixels):
            raise ValueError('Cannot decode original raster')
        formulations = [(f'p{i}', 'positive', text) for i, text in enumerate(family['descriptions'])]
        formulations += [(f'n{i}', n['kind'], n['description']) for i, n in enumerate(family['negatives'])]
        for suffix, kind, text in formulations:
            cases.append(dict(case_id=f'item{number:02d}{suffix}', family=family['family'], kind=kind,
                description=text, image=image.relative_to(output).as_posix(), input_sha256=digest(image),
                source_sha256=source['image_sha256'], width=pixels.shape[1], height=pixels.shape[0],
                expected_text=family['expected_text'], regions=family['regions'],
                expected_circles=family['expected_circles']))
    manifest = dict(schema='semantic_robustness_inputs_v1', selection_sha256=digest(selection),
                    annotation_origin=config['annotation_origin'], scope=config['scope'],
                    region_limits=config['region_limits'], cases=cases)
    write_json(output/'manifest.json', manifest)
    write_json(output/'freeze.json', {p.relative_to(output).as_posix(): digest(p)
                                    for p in output.rglob('*') if p.is_file()})
    return verify_inputs(output)


def verify_inputs(prepared: Path) -> dict:
    frozen = json.loads((prepared/'freeze.json').read_text(encoding='utf-8'))
    if 'manifest.json' not in frozen:
        raise ValueError('Missing frozen manifest')
    for name, expected in frozen.items():
        if digest(contained(prepared, name)) != expected:
            raise ValueError('Frozen input changed: '+name)
    manifest = json.loads((prepared/'manifest.json').read_text(encoding='utf-8'))
    ids = [c['case_id'] for c in manifest['cases']]
    if not ids or len(set(ids)) != len(ids) or any(not i.isalnum() for i in ids):
        raise ValueError('Empty, duplicate or unsafe case IDs')
    for case in manifest['cases']:
        if digest(contained(prepared, case['image'])) != case['input_sha256']:
            raise ValueError('Raster hash mismatch')
    return manifest


def check_output(case: dict, pixels, svg: str, limits: dict) -> dict:
    import cv2
    import numpy as np
    from tools.run_plan_b_variations import measure_quality, render
    quality = measure_quality(pixels, svg)
    raster = render(svg, case['width'], case['height'])
    regions = []
    for region in case['regions']:
        x, y, w, h = region['box']
        left, top = int(x*case['width']), int(y*case['height'])
        right, bottom = math.ceil((x+w)*case['width']), math.ceil((y+h)*case['height'])
        a, b = pixels[top:bottom, left:right], raster[top:bottom, left:right]
        mse = float(np.square(a.astype(float)-b.astype(float)).mean()/255**2)
        ea, eb = cv2.Canny(a, 50, 140)>0, cv2.Canny(b, 50, 140)>0
        if ea.any() and eb.any():
            da = cv2.distanceTransform((~eb).astype(np.uint8), cv2.DIST_L2, 3)
            db = cv2.distanceTransform((~ea).astype(np.uint8), cv2.DIST_L2, 3)
            edge = float((np.exp(-da[ea]).mean()+np.exp(-db[eb]).mean())/2)
        else:
            edge = float(not ea.any() and not eb.any())
        regions.append(dict(name=region['name'], normalized_mse=mse, edge_score=edge,
            passed=mse <= limits['normalized_mse'] and edge >= limits['edge_score']))
    root = ET.fromstring(svg)
    # Native primitives are required by this bounded regression contract.
    # A correct alternative representation needs a new independent annotation.
    circles = sum(e.tag.rsplit('}', 1)[-1] == 'circle' for e in root.iter())
    labels = ''.join(''.join(e.itertext()) for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'text')
    text_ok = labels == case['expected_text'] if case['expected_text'] != '!' else not labels or labels == '!'
    structure = dict(circles=circles, text=labels,
                     passed=circles == case['expected_circles'] and text_ok)
    return dict(quality=quality, regions=regions, structure=structure,
                passed=quality['satisfactory'] and all(r['passed'] for r in regions) and structure['passed'])


def observe(case: dict, prepared: Path, output: Path, raw: dict, limits: dict, budget: float) -> dict:
    import cv2
    folder = output/case['case_id']
    audit = folder/'reference_access.json'
    if not audit.exists() or json.loads(audit.read_text(encoding='utf-8'))['blocked_svg_reads']:
        raise ValueError('Missing or failed reference-access guard')
    # The production CLI moves classified failures into its quarantine folder.
    candidates = [folder/'input'/name/(case['case_id']+'.png') for name in
                  ('', 'nonconvertable', 'succesessfulConvertedImages')]
    present = [p for p in candidates if p.exists()]
    if len(present) != 1:
        raise ValueError('Missing or ambiguous CLI source raster')
    image = present[0]
    if digest(image) != case['input_sha256']:
        raise ValueError('CLI raster changed')
    desc = ET.parse(folder/'input/descriptions.xml').findtext('.//beschreibung')
    if desc != case['description']:
        raise ValueError('CLI description changed')
    log = folder/'conversion/reports'/(case['case_id']+'_element_validation.log')
    log_text = log.read_text(encoding='utf-8') if log.exists() else ''
    statuses = [line[7:] for line in log_text.splitlines() if line.startswith('status=')]
    result_map = folder/'conversion/reports/conversion_result_map.json'
    rows = json.loads(result_map.read_text(encoding='utf-8')) if result_map.exists() else {}
    row = rows.get(case['case_id']+'.png') or {}
    claimed = bool(row.get('search_satisfactory'))
    control_path = folder/'conversion/reports'/(case['case_id']+'_deadline.json')
    control = json.loads(control_path.read_text(encoding='utf-8')) if control_path.exists() else {}
    if not control.get('isolated') or control.get('limit_seconds') != budget or control.get('max_seconds') != budget:
        raise ValueError('Missing supervised fixed image budget')
    check = None
    if raw.get('output_svg'):
        vector = contained(output, raw['output_svg'])
        if digest(vector) != raw['output_sha256']:
            raise ValueError('Output SVG changed')
        check = check_output(case, cv2.imread(str(image)), vector.read_text(encoding='utf-8'), limits)
    return dict(case_id=case['case_id'], family=case['family'], kind=case['kind'],
                statuses=statuses, claimed_success=claimed, check=check,
                passed=bool(check and check['passed'] and claimed) if case['kind']=='positive' else
                       bool(not claimed and any('description_rejected' in s for s in statuses)),
                raw=raw, audit_sha256=digest(audit),
                evidence_sha256={p.relative_to(output).as_posix(): digest(p) for p in
                    (log, result_map, control_path) if p.exists()})


def summarize(records: list[dict]) -> dict:
    families = []
    for family in sorted({r['family'] for r in records}):
        rows = [r for r in records if r['family']==family]
        positives = [r for r in rows if r['kind']=='positive']
        negatives = [r for r in rows if r['kind']!='positive']
        families.append(dict(family=family, positive_passes=sum(r['passed'] for r in positives),
            positives=len(positives), safe_rejections=sum(r['passed'] for r in negatives), negatives=len(negatives),
            silent_negative_successes=sum(r['claimed_success'] for r in negatives),
            passed=all(r['passed'] for r in rows)))
    return dict(attempts=len(records), positive_passes=sum(r['passed'] for r in records if r['kind']=='positive'),
        positives=sum(r['kind']=='positive' for r in records),
        safe_rejections=sum(r['passed'] for r in records if r['kind']!='positive'),
        negatives=sum(r['kind']!='positive' for r in records),
        accepted_families=sum(r['passed'] for r in families), families=families)


def run(prepared: Path, output: Path, budget: float = 5., only: list[str] | None = None,
        baseline: Path | None = None) -> dict:
    import shutil
    from tools.run_plan_b_variations import run_case
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError('Budget must be positive and finite')
    manifest = verify_inputs(prepared)
    cases = manifest['cases']
    if only:
        cases = [c for c in cases if c['family'] in only]
        if set(only) != {c['family'] for c in cases}:
            raise ValueError('Unknown family')
    prepared, output = prepared.resolve(), output.resolve()
    runtime = (baseline or ROOT).resolve()
    hashes = source_hashes(runtime)
    export = json.loads((runtime/'export.json').read_text(encoding='utf-8')) if baseline else None
    if export and export['runtime_sha256'] != hashes:
        raise ValueError('Exported baseline changed')
    output.mkdir(parents=True, exist_ok=False)
    report = dict(schema='semantic_robustness_run_v1', freeze_sha256=digest(prepared/'freeze.json'),
                  runtime_sha256=hashes, baseline_revision=export['revision'] if export else None,
                  budget_seconds=budget, case_ids=[c['case_id'] for c in cases], records=[])
    for case in cases:
        inputs = output/case['case_id']/'input'
        inputs.mkdir(parents=True)
        shutil.copyfile(contained(prepared, case['image']), inputs/(case['case_id']+'.png'))
        root = ET.Element('root')
        entry = ET.SubElement(root, 'entry')
        ET.SubElement(entry, 'beschreibung').text = case['description']
        ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = case['case_id']+'.png'
        ET.ElementTree(root).write(inputs/'descriptions.xml', encoding='utf-8', xml_declaration=True)
        raw = run_case(case, output, timeout=budget+30, iterations=64,
                       extra_cli_args=('--search-seconds', str(budget), '--search-max-seconds', str(budget), '--search-seed', '17'),
                       runtime_root=runtime)
        record = observe(case, prepared, output, raw, manifest['region_limits'], budget)
        report['records'].append(record)
        report['summary'] = summarize(report['records'])
        write_json(output/'report.json', report)
        print(case['case_id'], case['family'], case['kind'], record['passed'], flush=True)
    if hashes != source_hashes(runtime):
        raise ValueError('Runtime changed during measurement')
    return verify(prepared, output)


def verify(prepared: Path, output: Path) -> dict:
    manifest = verify_inputs(prepared)
    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    if digest(prepared/'freeze.json') != report['freeze_sha256']:
        raise ValueError('Input provenance mismatch')
    by_id = {c['case_id']: c for c in manifest['cases']}
    ids = report['case_ids']
    if not ids or len(set(ids)) != len(ids) or not set(ids) <= by_id.keys() or ids != [r['case_id'] for r in report['records']]:
        raise ValueError('Incomplete or duplicate attempt inventory')
    families = {by_id[i]['family'] for i in ids}
    if ids != [c['case_id'] for c in manifest['cases'] if c['family'] in families]:
        raise ValueError('A family must retain all of its frozen attempts')
    records = []
    for saved in report['records']:
        for name, expected in saved['evidence_sha256'].items():
            if digest(contained(output, name)) != expected:
                raise ValueError('CLI evidence changed')
        record = observe(by_id[saved['case_id']], prepared, output, saved['raw'],
                         manifest['region_limits'], report['budget_seconds'])
        if record != saved:
            raise ValueError('Saved decisions differ from independent verification')
        records.append(record)
    summary = summarize(records)
    if summary != report['summary']:
        raise ValueError('Summary differs from attempt inventory')
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', type=Path)
    action.add_argument('--run', type=Path)
    action.add_argument('--verify', type=Path)
    action.add_argument('--export-baseline', type=Path)
    parser.add_argument('--ref', default='7ed646e5f', help='Commit to export for the paired baseline')
    parser.add_argument('--baseline', type=Path, help='Unmodified export from --export-baseline')
    parser.add_argument('--selection', type=Path, default=DEFAULT_SELECTION)
    parser.add_argument('--prepared', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--budget', type=float, default=5.)
    parser.add_argument('--families', nargs='+')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    if args.export_baseline:
        print(json.dumps(export_baseline(args.export_baseline, args.ref),indent=2))
        return 0
    if args.prepare:
        manifest = prepare(args.prepare, args.selection)
        print('Frozen', len(manifest['cases']), 'cases')
        return 0
    if (args.run and not args.output) or (args.verify and not args.prepared):
        parser.error('--run needs --output; --verify needs --prepared')
    result = run(args.run, args.output, args.budget, args.families, args.baseline) if args.run else verify(args.prepared, args.verify)
    print(json.dumps(result, indent=2))
    return int(args.require_all and result['accepted_families'] != len(result['families']))


if __name__ == '__main__':
    raise SystemExit(main())
