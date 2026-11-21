"""Freeze and replay a small, grouped catalogue cohort before model changes.

This measures the analytic fitter path, not catalogue-wide success or unseen
generalisation. Inputs, effective descriptions and baseline code are hash bound.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import cv2

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'artifacts/evaluation/adaptive_form_models_v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def freeze(directory):
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
    mapping = loadDescriptionMappingImpl(str(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'),
                                        get_base_name_from_file_fn=getBaseNameFromFileImpl)
    reflection = Reflection(mapping)
    groups = [
        ('disk_arrow', 'development', ['GE0022', 'GE0037_S', 'GE0037_M', 'GE0037_L',
                                        'GE0039_S', 'GE0039_M', 'GE0039_L']),
        ('plain_disk', 'control', ['AC0800_S', 'AC0800_M']),
        ('hollow_cross_panel', 'control', ['AC0140_L']),
        ('component_composition', 'control', ['AC0152_L']),
    ]
    cases = []
    for family, split, names in groups:
        for name in names:
            path = Path('artifacts/images_to_convert') / (name+'.jpg')
            description, _ = reflection.parseDescription(name.split('_')[0], name+'.jpg')
            cases.append(dict(name=name, family=family, split=split, image=path.as_posix(),
                              image_sha256=digest((ROOT/path).read_bytes()), description=description,
                              description_sha256=digest(description.encode('utf-8'))))
    sources = {p.as_posix(): digest((ROOT/p).read_bytes()) for p in (
        Path('src/iCCModules/imageCompositeConverterDiskArrow.py'),
        Path('src/iCCModules/imageCompositeConverterFilledSymbols.py'),
        Path('src/iCCModules/imageCompositeConverterDescriptionLanguage.py'))}
    manifest = dict(schema_version=1, scope='analytic fitter comparison; known regression cohort, no unseen claim',
                    seconds=3., render_budget=448, seed=42, groups=groups, cases=cases, baseline_sources=sources)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'manifest.json').open('x', encoding='utf-8') as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)


def evaluate(directory, label):
    import numpy as np
    from src.iCCModules.imageCompositeConverterDiskArrow import fit_disk_arrow
    from src.iCCModules.imageCompositeConverterPlainDisk import fit_plain_disk
    from src.iCCModules.imageCompositeConverterHollowCrossPanel import fit_hollow_cross_panel
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
    from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search
    from tools.run_plan_b_variations import render, measure_quality
    manifest_path = directory/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    destination = directory/('summary.json' if label == 'comparison' else label+'.json')
    if destination.exists():
        raise FileExistsError('Keep previous evidence; choose a new --label: '+str(destination))
    if label == 'baseline':
        for path, expected in manifest['baseline_sources'].items():
            if digest((ROOT/path).read_bytes()) != expected:
                raise ValueError('Baseline source changed: '+path)
    fitters = dict(disk_arrow=fit_disk_arrow, plain_disk=fit_plain_disk,
                   hollow_cross_panel=fit_hollow_cross_panel)
    records = []
    for case in manifest['cases']:
        data = (ROOT/case['image']).read_bytes()
        if digest(data) != case['image_sha256'] or digest(case['description'].encode('utf-8')) != case['description_sha256']:
            raise ValueError('Frozen input changed: '+case['name'])
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        h, w = image.shape[:2]
        calls = 0
        def counted(svg, width, height):
            nonlocal calls
            calls += 1
            return render(svg, width, height)
        start = time.monotonic()
        with search_configuration(mode='portfolio', seed=manifest['seed'], adaptive=True,
                budget=manifest['render_budget'], seconds=manifest['seconds'], max_seconds=manifest['seconds']):
            with configured_image_search('anonymous'):
                fitter = fitters.get(case['family'])
                result = (fitter(w, h, description=case['description'], image=image,
                    render_fn=counted, error_fn=lambda a, b: float(np.square(a.astype(float)-b.astype(float)).mean()/255**2))
                    if fitter is not None else None)
        elapsed = time.monotonic()-start
        semantics = False
        quality = None
        reason = 'unsupported_description_or_evidence' if fitter else 'outside_analytic_fitter_scope'
        if result is not None:
            try:
                validate_svg_assertions(result['svg'], description_assertions(case['description']))
                semantics = True
            except ValueError as exc:
                reason = str(exc)
            quality = measure_quality(image, result['svg'])
            if semantics:
                reason = 'passed' if quality['satisfactory'] else 'pixel_gate'
            output = directory/label/(case['name']+'.svg')
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result['svg'], encoding='utf-8')
        records.append(dict(name=case['name'], family=case['family'], split=case['split'],
            passed=bool(semantics and quality and quality['satisfactory']), reason=reason,
            seconds=elapsed, renderings=calls, error=result['error'] if result else None,
            quality=quality, svg_sha256=digest(result['svg'].encode('utf-8')) if result else None,
            comparison=result.get('model_comparison') if result else None))
        print(case['name'], reason, calls, round(elapsed, 3), flush=True)
    report = dict(manifest_sha256=digest(manifest_path.read_bytes()), label=label, cases=records,
                  passed=sum(c['passed'] for c in records), count=len(records),
                  seconds=sum(c['seconds'] for c in records), renderings=sum(c['renderings'] for c in records))
    with destination.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({k:v for k,v in report.items() if k != 'cases'}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DEFAULT)
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--label', default='comparison')
    args = parser.parse_args()
    if args.freeze:
        freeze(args.directory)
    evaluate(args.directory, args.label)


if __name__ == '__main__':
    main()
