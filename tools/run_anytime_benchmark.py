"""Paired, budget-capped production CLI quality curves; failures stay in denominators."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import time
from xml.etree import ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUDGETS = (1., 5., 15., 60.)
DEFAULT_SEEDS = (17, 42, 20261018)
PARENT_MODULES = ('AdaptiveSearch','FilledSymbols','SearchBots','ShortLabelDisk')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_provenance(row):
    params = row.get('params') or {}
    return dict(mode=params.get('mode'),
                registrations={name:{key:value[key] for key in
                    ('source','error','evaluations','model_attempts','search') if key in value}
                    for name,value in params.items() if name.endswith('_registration') and isinstance(value,dict)},
                checkpoint_proof=row.get('checkpoint_proof'))


def write_json(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    os.replace(temporary, path)


def percentile(values, fraction):
    """Linear interpolation, including censored times in all-attempt summaries."""
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered)-1)*fraction
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower]+(ordered[upper]-ordered[lower])*(position-lower)


def summarize(records):
    groups = []
    for mode, budget, split in sorted({(r['mode'], r['budget_seconds'], s)
                                     for r in records for s in ('all', r['split'])}):
        rows = [r for r in records if r['mode'] == mode and r['budget_seconds'] == budget
                and (split == 'all' or r['split'] == split)]
        successful = [r for r in rows if r['satisfactory']]
        elapsed = [r['image_seconds'] for r in rows if r['image_seconds'] is not None]
        groups.append(dict(mode=mode, budget_seconds=budget, split=split, attempts=len(rows),
            satisfactory=len(successful), success_rate=len(successful)/len(rows),
            statuses=dict(Counter(r['status'] for r in rows)),
            median_image_seconds=statistics.median(elapsed) if elapsed else None,
            p95_image_seconds=percentile(elapsed, .95),
            timed_attempts=len(elapsed),
            median_success_seconds=percentile([r['image_seconds'] for r in successful
                                              if r['image_seconds'] is not None], .5),
            median_render_calls=percentile([r['telemetry']['render_started'] for r in rows], .5),
            p95_render_calls=percentile([r['telemetry']['render_started'] for r in rows], .95),
            missing_outputs=sum(not r.get('svg') for r in rows),
            object_failures=sum((r.get('structure') or {}).get('passed') is False for r in rows),
            # Never present a mean over surviving SVGs as an unconditional quality score.
            quality_observations=sum(r.get('quality') is not None for r in rows),
            median_output_mse=percentile([r['quality']['metrics']['normalized_mse'] for r in rows
                                          if r.get('quality') and 'normalized_mse' in r['quality']['metrics']], .5)))
    pairs = {}
    for r in records:
        pairs.setdefault((r['case_id'], r['seed'], r['budget_seconds']), {})[r['mode']] = r
    comparisons = []
    for budget in sorted({r['budget_seconds'] for r in records}):
        paired = [p for (_, _, b), p in pairs.items() if b == budget and len(p) == 2]
        comparisons.append(dict(budget_seconds=budget, pairs=len(paired),
            gained=sum(p['after']['satisfactory'] and not p['before']['satisfactory'] for p in paired),
            lost=sum(p['before']['satisfactory'] and not p['after']['satisfactory'] for p in paired),
            both_pass=sum(p['before']['satisfactory'] and p['after']['satisfactory'] for p in paired)))
    return dict(curves=groups, paired=comparisons)


def prepare_cases(output):
    import cv2
    from tools.run_plan_b_variations import render
    from tools.evaluate_primitive_scene import make_cases, rotate_cases
    sources = output/'sources'
    sources.mkdir()
    prior = ROOT/'artifacts/evaluation/scheduler_search_v1'
    previous = json.loads((prior/'report.json').read_text(encoding='utf-8'))['cases']
    cases = []
    # Real JPEGs with two independent topologies, three sizes/palettes across the suite.
    for index in (1, 4):
        case = previous[index]
        path = sources/f'case_{len(cases):02d}.jpg'
        shutil.copyfile(prior/case['image'], path)
        cases.append(dict(case_id=path.stem, image=path.relative_to(output).as_posix(),
            kind=case['kind'], label=case.get('label'), description=case['description'],
            split='known', family=case['kind'], provenance='scheduler_search_v1/'+case['case_id']))

    def add(svg, width, height, **metadata):
        path = sources/f'case_{len(cases):02d}.png'
        if not cv2.imwrite(str(path), render(svg, width, height)):
            raise ValueError('Could not freeze source raster')
        cases.append(dict(case_id=path.stem, image=path.relative_to(output).as_posix(), **metadata))

    # New independent renderer inputs, including a matched description paraphrase.
    size = 88
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="88" height="88">'
           '<rect width="88" height="88" fill="white"/>'
           '<circle cx="44" cy="44" r="33" stroke="#38634f" stroke-width="2" fill="#d7eadc"/>'
           '<text x="44" y="55" font-family="Arial" font-size="28" font-weight="700" '
           'text-anchor="middle" fill="#25352d">Hz</text></svg>')
    for description in ('Eine einfarbige Kreisscheibe mit dunkler Randkontur. Serifenlose Beschriftung "Hz". Keine Anschlüsse.',
                        'Auf weißem Grund liegt eine gefüllte runde Scheibe mit dunklem Umriss und der fetten serifenlosen Beschriftung "Hz". Ohne Griff oder weitere Objekte.'):
        add(svg, size, size, kind='label', label='Hz', split='holdout', family='label',
            description=description, paraphrase_group='hz')
    for scene in (make_cases(918273, 8)[-1], rotate_cases(make_cases(581321, 9))[-1]):
        add(scene['svg'], scene['width'], scene['height'], kind='objects', split='holdout', family='primitives',
            description=scene['description'], expected_objects=scene['expected_objects'])
    # Entire shape families absent from the scheduler evidence, with explicit oracles.
    for family, shape, bbox, description in (
        ('ellipse', '<ellipse cx="90" cy="55" rx="55" ry="24" fill="none" stroke="#4b3a8c" stroke-width="3"/>',
         [33.5,29.5,113,51], 'Eine einzelne waagerecht längliche Ellipse mit violetter Kontur, weißem Inneren und weißem Hintergrund. Kein Kreis, keine Beschriftung.'),
        ('triangle', '<polygon points="90,20 145,90 35,90" fill="none" stroke="#20654a" stroke-width="3" stroke-linejoin="round"/>',
         [33.5,18.5,113,73], 'Ein einzelnes nach oben gerichtetes gleichschenkliges Dreieck mit grüner Kontur und weißem Inneren auf weißem Grund. Keine Kreisscheibe und keine Beschriftung.')):
        add('<svg xmlns="http://www.w3.org/2000/svg" width="180" height="110"><rect width="180" height="110" fill="white"/>'+shape+'</svg>',
            180, 110, kind='objects', split='unseen_family', family=family, description=description,
            expected_objects=[dict(kind=family, bbox=bbox)])
    for case in cases:
        case['input_sha256'] = digest(output/case['image'])
    write_json(output/'manifest.json', dict(generator_seed=[918273,581321], cases=cases))
    return cases


def structure(case, svg, image):
    if case['kind'] == 'regions':
        from tools.run_real_neural_elements import check_regions
        return check_regions(case, svg, image)
    if case['kind'] == 'label':
        from tools.evaluate_short_label_search import symbol_semantics
        return dict(passed=symbol_semantics(svg, case['label']) == 1., expected_text=case['label'])
    if case['kind'] == 'motor':
        from tools.evaluate_motor_valve_recheck import symbol_semantics
        return dict(passed=symbol_semantics(svg) == 1., expected_topology='three_way_valve_and_M_disk')
    import cv2
    import numpy as np
    from tools.evaluate_primitive_scene import check_objects
    from tools.run_plan_b_variations import render
    raster = render(svg, image.shape[1], image.shape[0])
    result = check_objects(raster, case['expected_objects'])
    # Check the rendered shape as well as its box; equivalent SVG paths are valid.
    border = np.concatenate([raster[0],raster[-1],raster[:,0],raster[:,-1]])
    mask = (np.max(abs(raster.astype(float)-np.median(border,axis=0)),axis=2)>25).astype(np.uint8)
    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    contours = [c for c in contours if cv2.contourArea(c)>=4]
    classes = []
    for obj in case['expected_objects']:
        if not contours:
            classes.append(False)
            continue
        index = min(range(len(contours)),key=lambda i:sum(abs(a-b) for a,b in zip(cv2.boundingRect(contours[i]),obj['bbox'])))
        contour = contours.pop(index)
        kind = obj['kind']
        polygon = cv2.approxPolyDP(contour,.025*cv2.arcLength(contour,True),True)
        if kind in {'circle','ellipse'} and len(contour)>=5:
            (x,y),(width,height),angle = cv2.fitEllipse(contour)
            points = contour[:,0,:].astype(float)-[x,y]
            radians = np.deg2rad(angle)
            u = points[:,0]*np.cos(radians)+points[:,1]*np.sin(radians)
            v = -points[:,0]*np.sin(radians)+points[:,1]*np.cos(radians)
            radius = np.sqrt((2*u/width)**2+(2*v/height)**2)
            classes.append(bool(np.sqrt(np.mean((radius-1)**2))<.08 and
                                (kind=='ellipse' or min(width,height)/max(width,height)>.9)))
        else:
            classes.append(len(polygon)=={'triangle':3,'rectangle':4}.get(kind,0))
    result['shape_class_passed'] = all(classes) and not contours
    result['passed'] = result['passed'] and result['shape_class_passed']
    return result


def archive_snapshot():
    root = ROOT/'artifacts/satisfactory_conversions'
    index = json.loads((root/'index.json').read_text(encoding='utf-8'))
    for case in index['cases']:
        for key in ('image','svg'):
            if digest(root/case[key]) != case[key+'_sha256']:
                raise ValueError('Archive hash changed: '+case[key])
    return dict(cases=len(index['cases']), index_sha256=digest(root/'index.json'),
                files={case[key]:case[key+'_sha256'] for case in index['cases'] for key in ('image','svg')})


def freeze_parent(work, ref):
    commit = subprocess.check_output(['git','rev-parse',ref], cwd=ROOT, text=True).strip()
    archive = subprocess.check_output(['git','archive','--format=zip',commit,'src'], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        source.extractall(work/'parent')
    hashes = {p.relative_to(work/'parent').as_posix():digest(p) for p in (work/'parent/src').rglob('*.py')}
    overlay = work/'parent_modules'
    overlay.mkdir()
    replaced = {'src/iCCModules/imageCompositeConverter'+suffix+'.py' for suffix in PARENT_MODULES}
    # Keep unchanged resource/dependency modules at their original repository
    # paths. Refuse other source differences instead of silently mixing versions.
    for name, value in hashes.items():
        if name not in replaced and digest(ROOT/name) != value:
            raise ValueError('Unsupported baseline difference outside scheduler modules: '+name)
    for name in replaced:
        shutil.copyfile(work/'parent'/name,overlay/Path(name).name)
    return commit, hashes


def run_cell(output, work, cases, mode, budget, seed, *, cli_args=(), env_overrides=None, bootstrap_hook='', recover=False):
    from tools.anytime_observer import summarize as render_summary
    import cv2
    from tools.run_plan_b_variations import measure_quality
    cell_id = f'{mode}-{budget:g}s-{seed}'
    cell = work/cell_id
    if recover and cell.exists():
        metadata_path=cell/'cli_execution.json'
        metadata=json.loads(metadata_path.read_text(encoding='utf-8')) if metadata_path.exists() else dict(cli_seconds=None,cli_returncode=None)
        return collect_cell(output,work,cases,mode,budget,seed,**metadata,
                            component_evaluation=bool(env_overrides and env_overrides.get('ICC_COMPONENT_EVALUATION')))
    inputs, conversion, telemetry, bootstrap = (cell/n for n in ('inputs','conversion','telemetry','bootstrap'))
    inputs.mkdir(parents=True)
    bootstrap.mkdir()
    table = ET.Element('root')
    for case in cases:
        shutil.copyfile(output/case['image'], inputs/Path(case['image']).name)
        entry = ET.SubElement(table, 'entry', kind='wurzelform', key=case['case_id'])
        ET.SubElement(entry,'beschreibung').text = case['description']
        ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text = Path(case['image']).name
    descriptions = cell/'descriptions.xml'
    ET.ElementTree(table).write(descriptions, encoding='utf-8', xml_declaration=True)
    # Applies identically in the CLI process and every Windows spawn child.
    (bootstrap/'sitecustomize.py').write_text(
        'import src.iCCModules\n'+ ('src.iCCModules.__path__ = ['+repr(str(work/'parent_modules'))+'] + list(src.iCCModules.__path__)\n' if mode == 'before' else '')+
        'from tools.anytime_observer import install\ninstall()\n'+bootstrap_hook, encoding='utf-8')
    env = dict(os.environ, IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', TINY_ICC_OUTPUT_VARIATION='0',
               PYTHONHASHSEED='0', PYTHONIOENCODING='utf-8', ICC_ANYTIME_TELEMETRY=str(telemetry),
               PYTHONPATH=str(bootstrap)+os.pathsep+str(ROOT))
    # Do not allow an inherited external cap or profiling setting to skew one arm.
    env.pop('ICC_CONVERSION_TIMEOUT_SEC', None)
    env.update(env_overrides or {})
    # Python only prints sitecustomize errors and otherwise continues. Fail closed
    # if that bootstrap failed, rather than comparing the current code to itself.
    launcher = ('from src.iCCModules.imageCompositeConverterDeadline import ImageDeadline; '
                'from tools.anytime_observer import observed_worker; '
                'assert ImageDeadline.run.__kwdefaults__["worker"] is observed_worker, "Observer bootstrap failed"; '
                'from tools.run_labeled_disk_recheck import main; raise SystemExit(main())')
    command = [sys.executable, '-c', launcher, '--_worker', cell_id, str(conversion), str(inputs),
        '--descriptions-path', str(descriptions), '--output-dir', str(conversion), '--start', cases[0]['case_id'],
        '--end', cases[-1]['case_id'], '--execution-mode', 'semantic-only', '--deterministic-order',
        '--search-seed', str(seed), '--search-seconds', str(budget), '--search-max-seconds', str(budget)]
    command.extend(cli_args)
    started = time.monotonic()
    with (cell/'cli.log').open('w', encoding='utf-8') as log:
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   timeout=len(cases)*(budget+12)+60)
    cli_seconds = time.monotonic()-started
    write_json(cell/'cli_execution.json',dict(cli_seconds=cli_seconds,cli_returncode=completed.returncode))
    return collect_cell(output,work,cases,mode,budget,seed,cli_seconds=cli_seconds,
                        cli_returncode=completed.returncode,
                        component_evaluation=bool(env_overrides and env_overrides.get('ICC_COMPONENT_EVALUATION')))


def collect_cell(output,work,cases,mode,budget,seed,*,cli_seconds,cli_returncode,component_evaluation=False):
    """Recollect completed native artifacts without rerunning measured conversions."""
    import cv2
    from tools.run_plan_b_variations import measure_quality
    from tools.anytime_observer import summarize as render_summary
    cell_id=f'{mode}-{budget:g}s-{seed}'
    cell=work/cell_id
    conversion,telemetry=cell/'conversion',cell/'telemetry'
    reports = conversion/'reports'
    rows_path = reports/'conversion_result_map.json'
    if not rows_path.exists():
        raise RuntimeError(f'CLI infrastructure failure: {cell}/cli.log (exit {cli_returncode})')
    rows = json.loads(rows_path.read_text(encoding='utf-8'))
    access = json.loads((cell/'reference_access.json').read_text(encoding='utf-8'))
    if access['blocked_svg_reads']:
        raise ValueError('Forbidden reference SVG read')
    saved_telemetry = output/'telemetry'/cell_id
    if telemetry.exists():
        shutil.copytree(telemetry, saved_telemetry,dirs_exist_ok=True)
    records = []
    for case in cases:
        name = case['case_id']
        row = rows.get(Path(case['image']).name, {})
        deadline_path = reports/(name+'_deadline.json')
        control = row.get('search_control') or (json.loads(deadline_path.read_text(encoding='utf-8'))
                                               if deadline_path.exists() else {})
        worker_access = reports/(name+'_reference_access.json')
        if not worker_access.exists():
            raise ValueError('Missing supervised worker audit: '+name)
        if json.loads(worker_access.read_text(encoding='utf-8'))['blocked_svg_reads']:
            raise ValueError('Forbidden worker SVG read')
        record = dict(case_id=name, split=case['split'], family=case['family'], mode=mode, seed=seed,
            budget_seconds=budget, cli_returncode=cli_returncode, cli_batch_seconds=cli_seconds,
            cli_metadata_complete=cli_seconds is not None and cli_returncode is not None,
            image_seconds=control.get('elapsed_seconds', row.get('elapsed_seconds')),
            search_control=control, runtime_satisfactory=bool(row.get('search_satisfactory')),
            telemetry=render_summary(sorted(saved_telemetry.glob(name+'-*.jsonl'))),
            satisfactory=False, status='missing_output', quality=None, structure=None)
        if component_evaluation:
            record['result_provenance'] = result_provenance(row)
            component_path = reports/(name+'_components.jsonl')
            if not component_path.exists() and control.get('stop_reason')!='time_limit':
                raise ValueError('Missing runtime component switches: '+name)
            if component_path.exists():
                saved = output/'telemetry'/cell_id/component_path.name
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(component_path, saved)
                events = [json.loads(line) for line in saved.read_text(encoding='utf-8').splitlines()]
                record['components'] = dict(path=saved.relative_to(output).as_posix(),
                                           sha256=digest(saved), events=events)
            else:
                record['components'] = dict(path=None,sha256=None,events=[])
                record['observation_censored'] = True
            observed_events = [json.loads(line) for p in sorted(saved_telemetry.glob(name+'-*.jsonl'))
                               for line in p.read_text(encoding='utf-8').splitlines() if line.startswith('{')
                               and line.endswith('}')]
            record['observed_controls'] = [e.get('applied_controls') for e in observed_events
                                          if e['event']=='worker_observed']
        paths = [p for folder in ('converted_svgs','converted_svg_failed') for p in (conversion/folder).glob(name+'.svg')]
        if len(paths) > 1:
            raise ValueError('Ambiguous output: '+name)
        if paths:
            destination = output/'outputs'/(cell_id+'-'+name+'.svg')
            shutil.copyfile(paths[0], destination)
            svg = destination.read_text(encoding='utf-8')
            image = cv2.imread(str(output/case['image']))
            quality = measure_quality(image, svg)
            objects = structure(case, svg, image)
            satisfactory = bool(quality['satisfactory'] and objects['passed'])
            record.update(svg=destination.relative_to(output).as_posix(), svg_sha256=digest(destination),
                          quality=quality, structure=objects, satisfactory=satisfactory,
                          status='satisfactory' if satisfactory else 'output_failed_independent_gate')
        elif control.get('stop_reason') == 'time_limit':
            record['status'] = 'timeout_no_valid_output'
        elif control.get('stop_reason') == 'worker_error':
            record['status'] = 'execution_error'
        if not control.get('isolated') or control.get('max_seconds') != budget:
            raise ValueError('Fixed production image budget was not applied: '+name)
        source_root = work/'parent' if mode == 'before' else ROOT
        if any(digest(source_root/p) != h for p,h in record['telemetry']['source_sha256'].items()):
            raise ValueError('Worker did not load the frozen implementation')
        records.append(record)
    return records


def verify(output):
    import cv2
    from tools.run_plan_b_variations import measure_quality
    from tools.anytime_observer import summarize as render_summary
    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    manifest = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    if digest(output/'manifest.json') != report['manifest_sha256']:
        raise ValueError('Manifest changed')
    cases = {c['case_id']:c for c in manifest['cases']}
    expected = {(mode,budget,seed,name) for mode in ('before','after') for budget in report['budgets_seconds']
                for seed in report['seeds'] for name in cases}
    actual = [(r['mode'],r['budget_seconds'],r['seed'],r['case_id']) for r in report['records']]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError('Benchmark matrix incomplete or duplicated')
    for case in cases.values():
        if digest(output/case['image']) != case['input_sha256']:
            raise ValueError('Input changed')
    for record in report['records']:
        cell_id = f'{record["mode"]}-{record["budget_seconds"]:g}s-{record["seed"]}'
        telemetry = render_summary(sorted((output/'telemetry'/cell_id).glob(record['case_id']+'-*.jsonl')))
        if telemetry != record['telemetry']:
            raise ValueError('Render telemetry changed')
        hashes = report['baseline_source_sha256'] if record['mode'] == 'before' else report['current_source_sha256']
        if any(hashes.get(p) != h for p,h in telemetry['source_sha256'].items()):
            raise ValueError('Wrong worker source')
        satisfactory = False
        if record.get('svg'):
            path = output/record['svg']
            if digest(path) != record['svg_sha256']:
                raise ValueError('Output changed')
            svg = path.read_text(encoding='utf-8')
            case = cases[record['case_id']]
            image = cv2.imread(str(output/case['image']))
            quality, objects = measure_quality(image,svg), structure(case,svg,image)
            if quality != record['quality'] or objects != record['structure']:
                raise ValueError('Independent measurements changed')
            satisfactory = quality['satisfactory'] and objects['passed']
        if bool(satisfactory) != record['satisfactory']:
            raise ValueError('False acceptance')
    if summarize(report['records']) != report['summary']:
        raise ValueError('Summary changed')
    if archive_snapshot() != report['archive_before'] or report['archive_before'] != report['archive_after']:
        raise ValueError('Archive changed')
    return dict(attempts=len(actual), outputs=sum(bool(r.get('svg')) for r in report['records']),
                independent_passes=sum(r['satisfactory'] for r in report['records']),
                archive_pairs_unchanged=report['archive_after']['cases'])


def run(output, work, baseline_ref, budgets, seeds):
    output.mkdir(parents=True, exist_ok=False)
    work.mkdir(parents=True, exist_ok=False)
    (output/'outputs').mkdir()
    cases = prepare_cases(output)
    commit, baseline_hashes = freeze_parent(work, baseline_ref)
    report = dict(schema='anytime_cli_v1', baseline_commit=commit,
        current_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        baseline_source_sha256=baseline_hashes,
        current_source_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in (ROOT/'src').rglob('*.py')},
        harness_sha256={p.name:digest(p) for p in (Path(__file__),ROOT/'tools/anytime_observer.py')},
        python=sys.version, platform=platform.platform(), budgets_seconds=budgets, seeds=seeds,
        manifest_sha256=digest(output/'manifest.json'), archive_before=archive_snapshot(), records=[],
        protocol='Independent fresh CLI runs per cap; max equals cap, no extensions. Alternating paired order; serial execution. Image time includes worker startup; batch overhead is separate. Renderer counters include finalization, exclude offline evaluation, and are observed calls, not proposal counts.')
    for budget_index, budget in enumerate(budgets):
        for seed_index, seed in enumerate(seeds):
            order = ('before','after') if (budget_index+seed_index)%2 == 0 else ('after','before')
            for mode in order:
                records = run_cell(output,work,cases,mode,budget,seed)
                report['records'].extend(records)
                report['summary'] = summarize(report['records'])
                write_json(output/'report.json', report)
                print(f'{mode} {budget:g}s seed={seed}: {sum(r["satisfactory"] for r in records)}/{len(records)} pass', flush=True)
    report['archive_after'] = archive_snapshot()
    write_json(output/'report.json',report)
    checks = verify(output)
    write_json(output/'checks.json',checks)
    print(checks,flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--work-dir',type=Path)
    parser.add_argument('--baseline-ref',default='00d48fe5c')
    parser.add_argument('--budgets',type=float,nargs='+',default=DEFAULT_BUDGETS)
    parser.add_argument('--seeds',type=int,nargs='+',default=DEFAULT_SEEDS)
    parser.add_argument('--verify-only',action='store_true')
    args = parser.parse_args()
    if (not args.budgets or any(not math.isfinite(b) or b<=0 for b in args.budgets)
            or len(set(args.budgets)) != len(args.budgets) or len(set(args.seeds)) != len(args.seeds)):
        parser.error('Budgets must be unique finite positive seconds; seeds must be unique')
    output = args.output_dir.resolve()
    if args.verify_only:
        print(verify(output))
    else:
        run(output, (args.work_dir or ROOT/'.tmp/anytime-benchmark').resolve(),args.baseline_ref,
            args.budgets,args.seeds)


if __name__ == '__main__':
    main()
