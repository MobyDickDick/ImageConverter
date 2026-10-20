"""Family-separated real-region CNN experiment with independent CLI gates.

The holdout is evaluated once after all three models are fixed. A negative
result is a completed experiment, never permission to activate the detector.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import shutil
import sys

import cv2
import numpy as np

from src.iCCModules import imageCompositeConverterNeuralElements as neural
from tools import run_anytime_benchmark as anytime
from tools import run_neural_elements as first
from tools import train_neural_elements as training

ROOT = anytime.ROOT
ANNOTATIONS = ROOT/'config/neural_real_regions.json'
SEEDS = (17, 42, 101)
OLD_FAMILIES = {v for v, _, _ in first.REAL}
OLD_PREFIXES = {v.split('_')[0] for v in OLD_FAMILIES}


def validate_cases(cases):
    """Reject leakage before augmentation or inference, including duplicate bytes."""
    groups, sources, identities = {}, {}, set()
    for c in cases:
        split = c['split']
        if split not in ('train', 'development', 'real_holdout'):
            raise ValueError('Unknown partition')
        if c['variant'] in identities:
            raise ValueError('Duplicate source identity')
        identities.add(c['variant'])
        for lookup, key in ((groups, c['family']), (sources, c['input_sha256'])):
            if key in lookup and lookup[key] != split:
                raise ValueError('Family/source leakage across partitions')
            lookup[key] = split
        if c['variant'].split('_')[0] in OLD_PREFIXES and split != 'development':
            raise ValueError('Previously inspected family must remain development')
        if not c['elements'] or any(e['kind'] not in neural.CLASSES or len(e['bbox']) != 4
                or not all(math.isfinite(v) for v in e['bbox']) or min(e['bbox'][2:]) <= 0
                for e in c['elements']):
            raise ValueError('Invalid region annotation')
    if len({c['family'] for c in cases if c['split'] == 'real_holdout'}) < 8:
        raise ValueError('At least eight new independent real holdout families required')


def prepare(output):
    manifest = json.loads(ANNOTATIONS.read_text(encoding='utf-8'))
    validate_cases(manifest['cases'])
    (output/'sources').mkdir()
    archive = ROOT/'artifacts/satisfactory_conversions'
    for i, c in enumerate(manifest['cases']):
        source = archive/c['image']
        if anytime.digest(source) != c['input_sha256']:
            raise ValueError('Changed annotated input')
        c['provenance'] = c['image']
        target = output/f'sources/case_{i:02d}{source.suffix}'
        shutil.copyfile(source, target)
        c.update(image=target.relative_to(output).as_posix(), case_id=target.stem, kind='regions')
        image = cv2.imread(str(target))
        h, w = image.shape[:2]
        for e in c['elements']:
            x, y, bw, bh = e['bbox']
            if x < 0 or y < 0 or x+bw > w or y+bh > h:
                raise ValueError('Annotation outside original raster')
    manifest.update(criteria=first.CRITERIA, seeds=list(SEEDS), budget_seconds=5., epochs=35,
        evaluation='Full Cartesian product of three fixed training seeds and three search seeds; balanced arm order. No holdout-based tuning.',
        annotation_sha256=anytime.digest(ANNOTATIONS))
    anytime.write_json(output/'manifest.json', manifest)
    return manifest


def real_training_data(output, cases):
    """The trainer opens ONLY train rasters; holdout never enters augmentation."""
    base = training.dataset()['train']
    images, labels = list(base['images']), list(base['labels'])
    families = list(base['families'])
    rng = np.random.default_rng(2026101902)
    for c in cases:
        if c['split'] != 'train':
            continue
        image = cv2.imread(str(output/c['image']))
        for e in c['elements']:
            x, y, w, h = e['bbox']
            crop = image[y:y+h, x:x+w]
            for variant in range(16):
                size = int(rng.integers(20, 80))
                scale = size/max(w, h)
                resized = cv2.resize(crop, (max(1, round(w*scale)), max(1, round(h*scale))))
                if variant % 2:
                    encoded = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(60, 98))])[1]
                    resized = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
                images.append(neural.chip(resized))
                labels.append(neural.CLASSES.index(e['kind']))
                families.append(c['family'])
    # Fill variations use only the original synthetic training families.
    for kind in ('circle', 'rectangle', 'triangle'):
        for family in range(80):
            image = training.family_image(kind, family)
            mask = (np.max(255-image.astype(float), axis=2) > 25).astype(np.uint8)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(image, contours, -1, tuple(int(v) for v in rng.integers(35, 225, 3)), -1)
            x, y, w, h = cv2.boundingRect(mask)
            images.append(neural.chip(image[y:y+h, x:x+w]))
            labels.append(neural.CLASSES.index(kind))
            families.append(f'{kind}-{family:03d}')
    return dict(train=dict(images=np.stack(images), labels=np.array(labels), families=families))


def train_models(output, manifest):
    models = output/'models'
    models.mkdir()
    cases = manifest['cases']
    data = real_training_data(output, cases)
    protocol = dict(schema='real_cnn_training_v2', manifest_sha256=anytime.digest(output/'manifest.json'),
        train_sources={c['case_id']:c['input_sha256'] for c in cases if c['split'] == 'train'},
        real_train_families=sorted({c['family'] for c in cases if c['split'] == 'train'}),
        synthetic_train_families=training.dataset()['train']['families'][::2],
        samples=len(data['train']['labels']), epochs=manifest['epochs'], seeds=manifest['seeds'],
        augmentation='16 fixed size/JPEG crops per manually annotated train region; synthetic train only plus filled train variants; no development/holdout reads.',
        model='Same 1830-parameter CNN; v2 multilevel nested region generator; fixed 0.8 confidence; no validation selection.')
    anytime.write_json(models/'training_protocol.json', protocol)
    records = []
    for seed in manifest['seeds']:
        weights, seconds = training.fit(data, seed, epochs=manifest['epochs'])
        model = models/f'model-{seed}.json'
        anytime.write_json(model, dict(schema='tiny_elements_cnn_v2', classes=list(neural.CLASSES),
            weights={k:v.tolist() for k, v in weights.items()}, training_seed=seed,
            protocol_sha256=anytime.digest(models/'training_protocol.json')))
        records.append(dict(seed=seed, seconds=seconds, sha256=anytime.digest(model),
                            train=training.classification(weights, data['train'])))
        print(f'Real CNN {seed}: {seconds:.1f}s', flush=True)
    anytime.write_json(models/'training.json', records)
    return records


def proposal_audit(image, elements, generator):
    boxes = generator(image)
    rows = [dict(kind=e['kind'], bbox=e['bbox'], small=min(e['bbox'][2:]) <= 12,
                 best_iou=max((neural.box_iou(e['bbox'], b) for b in boxes), default=0.)) for e in elements]
    return dict(proposals=len(boxes), expected=len(rows), covered=sum(e['best_iou'] >= .5 for e in rows), regions=rows)


def detector_inventory(output, manifest):
    """Frozen classifiers on unaugmented originals, one row per train seed.

    Keep missed small/nested instances and duplicate confident proposals visible;
    classification accuracy on the supplied training crops is not detection.
    """
    rows = first.detector_study(output, manifest['cases'], [dict(seed=s, model=f'model-{s}.json') for s in SEEDS])
    for r in rows:
        check = r['check']
        high = sum(p['confidence'] >= .8 for p in r['predictions'])
        check['duplicate_high_confidence'] = high-check['matched']-check['unmatched_high_confidence']
    return rows


def detector_summary(rows):
    return {s:{k:sum(r['check'][k] for r in rows if r['split']==s) for k in (
        'expected','matched','small_expected','small_matched','unmatched_high_confidence','duplicate_high_confidence')}
        for s in ('train','development','real_holdout')}


def check_regions(case, svg, image):
    """Independent raster-local fidelity; never calls either region generator.

    The fixed outline scene gates are applied inside EVERY marked region in
    addition to the unchanged global pixel/complexity gate. This is a region
    fidelity check, not a claim of general OCR or semantic segmentation.
    """
    from tools.run_plan_b_variations import render
    raster = render(svg, image.shape[1], image.shape[0])
    checks = []
    for element in case['elements']:
        x, y, w, h = element['bbox']
        # Include context for one-pixel lines and boundary objects.
        x0, y0 = max(0, x-2), max(0, y-2)
        x1, y1 = min(image.shape[1], x+w+2), min(image.shape[0], y+h+2)
        a, b = image[y0:y1, x0:x1], raster[y0:y1, x0:x1]
        error = np.mean((a.astype(float)-b.astype(float))**2, axis=2)/255**2
        am, bm = np.max(255-a.astype(float), axis=2) > 25, np.max(255-b.astype(float), axis=2) > 25
        union = am | bm
        iou = float(np.count_nonzero(am & bm)/max(1, np.count_nonzero(union)))
        foreground = float(error[union].mean()) if union.any() else 0.
        ae, be = cv2.Canny(a, 50, 140)>0, cv2.Canny(b, 50, 140)>0
        edge = 1. if not ae.any() and not be.any() else 0.
        if ae.any() and be.any():
            da = cv2.distanceTransform((~ae).astype(np.uint8), cv2.DIST_L2, 3)
            db = cv2.distanceTransform((~be).astype(np.uint8), cv2.DIST_L2, 3)
            edge = float((np.exp(-db[ae]).mean()+np.exp(-da[be]).mean())/2)
        passed = bool(error.mean() <= .01 and foreground <= .04 and iou >= .85 and edge >= .72)
        checks.append(dict(kind=element['kind'], bbox=element['bbox'], normalized_mse=float(error.mean()),
            foreground_mse=foreground, foreground_iou=iou, edge_alignment=edge, passed=passed))
    return dict(passed=all(c['passed'] for c in checks), regions=checks,
                contract='Independent local raster fidelity, not OCR or arbitrary instance segmentation')


def run_trial(output, work, parent, manifest, model_seed, smoke):
    output.mkdir()
    work.mkdir(parents=True)
    (output/'outputs').mkdir()
    (output/'sources').mkdir()
    (output/'models').mkdir()
    cases = [dict(c) for c in manifest['cases'] if c['split'] == 'real_holdout']
    if smoke:
        cases = cases[:2]
    for c in cases:
        shutil.copyfile(parent/c['image'], output/c['image'])
    # The existing strict CLI verifier keys model aliases by SEARCH seed. Each
    # trial deliberately aliases ONE fixed training seed for all search seeds.
    seeds = [17] if smoke else list(SEEDS)
    for search_seed in seeds:
        shutil.copyfile(parent/'models'/f'model-{model_seed}.json', output/'models'/f'model-{search_seed}.json')
    anytime.write_json(output/'manifest.json', dict(cases=cases, criteria=first.CRITERIA))
    model_files = {p.name:anytime.digest(p) for p in (output/'models').glob('*.json')}
    model_records = [dict(seed=s, model=f'model-{s}.json') for s in seeds]
    report = dict(schema='real_neural_cli_trial_v2', manifest_sha256=anytime.digest(output/'manifest.json'),
        training_seed=model_seed, seeds=seeds, budget_seconds=manifest['budget_seconds'], smoke=smoke,
        criteria=first.CRITERIA, python=sys.version, platform=platform.platform(),
        source_sha256={p.relative_to(ROOT).as_posix():anytime.digest(p) for p in (ROOT/'src').rglob('*.py')},
        model_files=model_files, archive_before=anytime.archive_snapshot(),
        detector_records=first.detector_study(output, cases, model_records), records=[])
    for i, seed in enumerate(seeds):
        for mode in (('analytic', 'neural') if (i+SEEDS.index(model_seed)) % 2 == 0 else ('neural', 'analytic')):
            args = ['--neural-elements-model', str(output/'models'/f'model-{seed}.json')] if mode == 'neural' else []
            rows = anytime.run_cell(output, work, cases, mode, manifest['budget_seconds'], seed,
                cli_args=args, env_overrides=dict(ICC_COMPONENT_EVALUATION='1', ICC_NEURAL_EVALUATION='1', OPENBLAS_NUM_THREADS='1'))
            report['records'].extend(rows)
            report['summary'] = first.summarize(report['records'])
            anytime.write_json(output/'report.json', report)
            print(f'Train {model_seed}, search {seed}, {mode}: {sum(r["satisfactory"] for r in rows)}/{len(rows)}', flush=True)
    report['decision'] = first.decision(report['records'], cases)
    anytime.write_json(output/'report.json', report)
    anytime.write_json(output/'checks.json', first.verify(output, allow_unobserved_timeouts=True))
    return report


def decision(records, cases):
    result = first.decision(records, cases)
    unobserved = sum(bool(r.get('observation_censored')) for r in records)
    result['unobserved_startup_timeouts'] = unobserved
    if unobserved:
        result['promote_to_default'] = False
        result['quality_benefit_demonstrated'] = False
        result['outcome'] = ('Unobserved startup interruption retained as failure; '
            'comparison cannot justify promotion. Retain analytic default.')
    return result


def aggregate(reports):
    rows = [dict(r, seed=(report['training_seed'], r['seed'])) for report in reports for r in report['records']]
    cases = {c['case_id']:c for report in reports for c in json.loads(
        (Path(report['_path'])/'manifest.json').read_text(encoding='utf-8'))['cases']}
    result = dict(summary=first.summarize(rows), decision=decision(rows, list(cases.values())))
    result['by_family'] = [dict(family=f, **{m:dict(attempts=sum(r['family']==f and r['mode']==m for r in rows),
        accepted=sum(r['family']==f and r['mode']==m and r['satisfactory'] for r in rows)) for m in ('analytic','neural')})
        for f in sorted({r['family'] for r in rows})]
    return result


def verify(output):
    manifest = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    summary = json.loads((output/'summary.json').read_text(encoding='utf-8'))
    validate_cases(manifest['cases'])
    if anytime.digest(output/'manifest.json') != summary['manifest_sha256']:
        raise ValueError('Changed frozen annotations/protocol')
    for c in manifest['cases']:
        if anytime.digest(output/c['image']) != c['input_sha256']:
            raise ValueError('Changed source')
    for name, sha in summary['model_files'].items():
        if anytime.digest(output/'models'/name) != sha:
            raise ValueError('Changed training/model')
    protocol = json.loads((output/'models/training_protocol.json').read_text(encoding='utf-8'))
    if protocol['manifest_sha256'] != summary['manifest_sha256'] or protocol['train_sources'] != {
            c['case_id']:c['input_sha256'] for c in manifest['cases'] if c['split']=='train'}:
        raise ValueError('Changed training partition')
    for name, sha in summary['harness_sha256'].items():
        if anytime.digest(ROOT/name) != sha:
            raise ValueError('Changed evaluation implementation')
    audit = []
    for c in manifest['cases']:
        image = cv2.imread(str(output/c['image']))
        audit.append(dict(case_id=c['case_id'], split=c['split'], family=c['family'],
            original=proposal_audit(image,c['elements'],neural.region_boxes),
            multilevel=proposal_audit(image,c['elements'],neural.region_boxes_v2)))
    if audit != json.loads((output/'region_audit.json').read_text(encoding='utf-8')):
        raise ValueError('Changed independent proposal inventory')
    if anytime.digest(output/'detector_records.json') != summary['detector_records_sha256']:
        raise ValueError('Changed detector observations')
    detector_rows = json.loads((output/'detector_records.json').read_text(encoding='utf-8'))
    expected = {(s, c['case_id']) for s in SEEDS for c in manifest['cases']}
    actual = [(r['training_seed'],r['case_id']) for r in detector_rows]
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError('Missing/duplicated detector measurement')
    cases = {c['case_id']:c for c in manifest['cases']}
    for row in detector_rows:
        c = cases[row['case_id']]
        weights, sha = neural.load_model(output/'models'/f'model-{row["training_seed"]}.json')
        predictions = neural.detect(cv2.imread(str(output/c['image'])), weights)
        check = first.detection_check(predictions,c['elements'])
        check['duplicate_high_confidence'] = sum(p['confidence']>=.8 for p in predictions)-check['matched']-check['unmatched_high_confidence']
        if (predictions != row['predictions'] or check != row['check'] or sha != row['model_sha256']
                or row['split'] != c['split']):
            raise ValueError('Changed independent instance measurements')
    if detector_summary(detector_rows) != summary['detector_summary']:
        raise ValueError('Changed detector summary')
    reports, checks = [], []
    for seed in ([17] if summary['smoke'] else SEEDS):
        trial = output/f'training-{seed}'
        if anytime.digest(trial/'report.json') != summary['trials'][str(seed)]:
            raise ValueError('Changed trial report')
        checks.append(first.verify(trial, allow_unobserved_timeouts=True))
        report = json.loads((trial/'report.json').read_text(encoding='utf-8'))
        wanted = [c for c in manifest['cases'] if c['split']=='real_holdout']
        if summary['smoke']:
            wanted = wanted[:2]
        child = json.loads((trial/'manifest.json').read_text(encoding='utf-8'))
        if child['cases'] != wanted or report['training_seed'] != seed or report['seeds'] != ([17] if summary['smoke'] else list(SEEDS)):
            raise ValueError('Changed Cartesian matrix/holdout')
        if any(h != anytime.digest(output/'models'/f'model-{seed}.json') for h in report['model_files'].values()):
            raise ValueError('Wrong training seed in CLI worker')
        report['_path'] = str(trial)
        reports.append(report)
    if aggregate(reports) != summary['results']:
        raise ValueError('Changed combined decision')
    return dict(attempts=sum(c['attempts'] for c in checks), outputs=sum(c['outputs'] for c in checks),
        accepted=sum(c['accepted'] for c in checks), archive_pairs_unchanged=checks[0]['archive_pairs_unchanged'],
        unobserved_startup_timeouts=sum(c['unobserved_startup_timeouts'] for c in checks))


def run(output, work, smoke=False, resume=False):
    output.mkdir(parents=True, exist_ok=resume)
    work.mkdir(parents=True, exist_ok=resume)
    if resume:
        manifest = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
        if manifest['annotation_sha256'] != anytime.digest(ANNOTATIONS):
            raise ValueError('Cannot resume with changed annotations')
        validate_cases(manifest['cases'])
        for c in manifest['cases']:
            if anytime.digest(output/c['image']) != c['input_sha256']:
                raise ValueError('Cannot resume changed inputs')
    else:
        manifest = prepare(output)  # Freeze all labels, groups and criteria first.
    audit = []
    for c in manifest['cases']:
        image = cv2.imread(str(output/c['image']))
        audit.append(dict(case_id=c['case_id'], split=c['split'], family=c['family'],
            original=proposal_audit(image,c['elements'],neural.region_boxes),
            multilevel=proposal_audit(image,c['elements'],neural.region_boxes_v2)))
    anytime.write_json(output/'region_audit.json', audit)
    # All model choices are fixed before even the first holdout inference.
    if not resume:
        train_models(output, manifest)
    else:
        protocol = json.loads((output/'models/training_protocol.json').read_text(encoding='utf-8'))
        if protocol['manifest_sha256'] != anytime.digest(output/'manifest.json'):
            raise ValueError('Cannot resume changed training protocol')
        records = json.loads((output/'models/training.json').read_text(encoding='utf-8'))
        if [r['seed'] for r in records] != list(SEEDS) or any(
                anytime.digest(output/'models'/f'model-{r["seed"]}.json') != r['sha256'] for r in records):
            raise ValueError('Cannot resume changed models')
    detector_rows = detector_inventory(output, manifest)
    anytime.write_json(output/'detector_records.json', detector_rows)
    reports = []
    for seed in ([17] if smoke else SEEDS):
        trial = output/f'training-{seed}'
        if resume and (trial/'report.json').exists():
            first.verify(trial, allow_unobserved_timeouts=True)
            report = json.loads((trial/'report.json').read_text(encoding='utf-8'))
            if any(anytime.digest(ROOT/p) != sha for p,sha in report['source_sha256'].items()):
                raise ValueError('Cannot reuse measurements from changed runtime')
        else:
            report = run_trial(trial, work/f'training-{seed}', output, manifest, seed, smoke)
        report['_path'] = str(trial)
        reports.append(report)
    summary = dict(schema='real_neural_elements_v2', smoke=smoke, manifest_sha256=anytime.digest(output/'manifest.json'),
        model_files={p.name:anytime.digest(p) for p in (output/'models').glob('*.json')},
        harness_sha256={p.relative_to(ROOT).as_posix():anytime.digest(p) for p in (
            Path(__file__), Path(first.__file__), Path(training.__file__), Path(anytime.__file__), ROOT/'tools/anytime_observer.py')},
        trials={str(r['training_seed']):anytime.digest(Path(r['_path'])/'report.json') for r in reports},
        detector_records_sha256=anytime.digest(output/'detector_records.json'),
        detector_summary=detector_summary(detector_rows),
        partition_counts={s:dict(sources=sum(c['split']==s for c in manifest['cases']),
            families=len({c['family'] for c in manifest['cases'] if c['split']==s})) for s in ('train','development','real_holdout')},
        proposal_summary={s:{g:dict(expected=sum(r[g]['expected'] for r in audit if r['split']==s),
            covered=sum(r[g]['covered'] for r in audit if r['split']==s)) for g in ('original','multilevel')}
            for s in ('train','development','real_holdout')}, results=aggregate(reports))
    anytime.write_json(output/'summary.json', summary)
    checks = verify(output)
    anytime.write_json(output/'checks.json', checks)
    print(checks, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--resume', action='store_true', help='Reuse only complete independently verified trials with identical inputs, models and runtime.')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if args.verify_only:
        print(verify(output))
    else:
        run(output, (args.work_dir or output.with_name(output.name+'-work')).resolve(), args.smoke, args.resume)


if __name__ == '__main__':
    main()
