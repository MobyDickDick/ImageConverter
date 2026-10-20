"""Freeze, train and independently check an optional CNN in the production CLI."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import platform
import shutil
import sys
import time

import cv2
import numpy as np

from src.iCCModules import imageCompositeConverterNeuralElements as neural
from tools import run_anytime_benchmark as anytime
from tools import train_neural_elements as training

ROOT = anytime.ROOT
CRITERIA = dict(min_independent_real_families=8,confidence=.95,
                quality_equivalence_margin=.05,relevant_time_saving=.10,
                detection_iou=.5,confidence_threshold=.8)
# Human box annotations, frozen before evaluating any model on the real set.
# Text regions are not OCR labels. All real families are absent from training.
REAL = (
    ('AC0840_M','rF', [('circle',[0,0,20,20]),('text',[3,5,14,10])]),
    ('AC0910_L','Lux',[('circle',[0,0,25,25]),('text',[4,10,17,9])]),
    ('AC1000_M','M', [('circle',[0,0,20,20]),('text',[5,4,11,12])]),
    ('AC0920_M','Q', [('circle',[0,0,20,20]),('text',[5,4,11,13])]),
    ('AC0850_L','P', [('circle',[0,0,25,25]),('text',[7,6,12,14])]),
    ('AC0232_M','M',[('circle',[24,5,20,20]),('text',[29,10,11,12]),
                     ('triangle',[0,9,17,20]),('triangle',[8,0,17,15]),('triangle',[8,15,17,15])]),
)


def prepare(output, smoke=False):
    from tools.evaluate_primitive_scene import make_cases, rotate_cases
    from tools.run_plan_b_variations import render
    (output/'sources').mkdir()
    cases=[]
    scenes = make_cases(713291,3)+list(rotate_cases(make_cases(924713,3)))
    for i,case in enumerate(scenes):
        target=output/f'sources/case_{i:02d}.png'
        cv2.imwrite(str(target),render(case['svg'],case['width'],case['height']))
        cases.append(dict(case_id=target.stem,image=target.relative_to(output).as_posix(),
            description=case['description'],kind='objects',split='synthetic',family=f'outline_layout_{i}',
            expected_objects=case['expected_objects'],elements=case['expected_objects']))
    archive=ROOT/'artifacts/satisfactory_conversions'
    index=json.loads((archive/'index.json').read_text(encoding='utf-8'))['cases']
    for variant,label,boxes in REAL:
        old=next(c for c in index if c['variant']==variant)
        target=output/f'sources/case_{len(cases):02d}.jpg'
        shutil.copyfile(archive/old['image'],target)
        cases.append(dict(case_id=target.stem,image=target.relative_to(output).as_posix(),
            description=old['description'],kind='motor' if variant.startswith('AC0232') else 'label',
            label=label,split='real_holdout',family=variant.split('_')[0],provenance=old['image'],
            elements=[dict(kind=k,bbox=b) for k,b in boxes]))
    for kind,shape,box,description in (
        ('ellipse','<ellipse cx="90" cy="55" rx="55" ry="24"/>',[33.5,29.5,113,51],
         'Eine einzelne waagerechte Ellipse mit dunkler Kontur, weißem Inneren und weißem Hintergrund. Kein Kreis, keine Beschriftung.'),
        ('triangle','<polygon points="90,20 145,90 35,90"/>',[33.5,18.5,113,73],
         'Ein einzelnes nach oben gerichtetes Dreieck mit dunkler Kontur und weißem Inneren auf weißem Grund. Keine Kreisscheibe und keine Beschriftung.')):
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="180" height="110"><rect width="180" height="110" fill="white"/><g fill="none" stroke="#20654a" stroke-width="3">'+shape+'</g></svg>'
        target=output/f'sources/case_{len(cases):02d}.png'
        cv2.imwrite(str(target),render(svg,180,110))
        cases.append(dict(case_id=target.stem,image=target.relative_to(output).as_posix(),
            description=description,kind='objects',split='unsupported_scene',family=kind,
            expected_objects=[dict(kind=kind,bbox=box)],elements=[dict(kind='unknown' if kind=='ellipse' else kind,bbox=box)]))
    for case in cases:
        case['input_sha256']=anytime.digest(output/case['image'])
    if smoke:
        cases=[cases[i] for i in (2,6,12)]
    anytime.write_json(output/'manifest.json',dict(schema='neural_elements_inputs_v1',cases=cases,
        criteria=CRITERIA,annotation='Real boxes manually marked on original raster contact sheet before model evaluation; IoU >= .5. Synthetic boxes from the independent generator, no fitter calls.'))
    return cases


def detection_check(predictions, expected):
    available=list(predictions)
    matches=[]
    for target in sorted(expected,key=lambda e:e['bbox'][2]*e['bbox'][3]):
        found=[(neural.box_iou(p['bbox'],target['bbox']),i) for i,p in enumerate(available)
               if p['kind']==target['kind'] and p['confidence']>=.8]
        score,i=max(found,default=(0,None))
        matched=score>=.5
        if matched:
            available.pop(i)
        matches.append(dict(kind=target['kind'],bbox=target['bbox'],matched=matched,iou=score,
                            small=min(target['bbox'][2:])<=12))
    wrong_high=sum(p['confidence']>=.8 and not any(
        p['kind']==e['kind'] and neural.box_iou(p['bbox'],e['bbox'])>=.5 for e in expected) for p in available)
    return dict(expected=len(expected),matched=sum(m['matched'] for m in matches),
                missing=sum(not m['matched'] for m in matches),
                small_expected=sum(m['small'] for m in matches),
                small_matched=sum(m['small'] and m['matched'] for m in matches),
                unmatched_high_confidence=wrong_high,matches=matches)


def detector_study(output,cases,models):
    rows=[]
    for model in models:
        started=time.perf_counter()
        weights,sha=neural.load_model(output/'models'/model['model'])
        initialization=time.perf_counter()-started
        for case in cases:
            image=cv2.imread(str(output/case['image']))
            started=time.perf_counter()
            predictions=neural.detect(image,weights)
            elapsed=time.perf_counter()-started
            # Reuse the initialized model; this is detector-only warm operation,
            # not a claim that production per-image spawn workers share weights.
            warm=[]
            for _ in range(10):
                started=time.perf_counter()
                neural.detect(image,weights)
                warm.append(time.perf_counter()-started)
            rows.append(dict(case_id=case['case_id'],split=case['split'],training_seed=model['seed'],
                model_sha256=sha,initialization_seconds=initialization,inference_seconds=elapsed,
                warm_median_seconds=anytime.percentile(warm,.5),predictions=predictions,
                check=detection_check(predictions,case['elements'])))
    return rows


def summarize(records):
    summaries=[]
    for mode,split in sorted({(r['mode'],r['split']) for r in records}):
        rows=[r for r in records if (r['mode'],r['split'])==(mode,split)]
        summaries.append(dict(mode=mode,split=split,attempts=len(rows),
            accepted=sum(r['satisfactory'] for r in rows),missing_outputs=sum(not r.get('svg') for r in rows),
            median_image_seconds=anytime.percentile([r['image_seconds'] for r in rows if r['image_seconds'] is not None],.5),
            p95_image_seconds=anytime.percentile([r['image_seconds'] for r in rows if r['image_seconds'] is not None],.95),
            renders=sum(r['telemetry']['render_started'] for r in rows),
            peak_worker_bytes=max((e['worker_peak_memory_bytes'] or 0 for r in rows for e in r['components']['events']),default=0)))
    return summaries


def decision(records, cases):
    pairs={}
    for row in records:
        if row['split']=='real_holdout':
            pairs.setdefault((row['case_id'],row['seed']),{})[row['mode']]=row
    families={}
    gained=lost=identical=0
    for (name,_),pair in pairs.items():
        if set(pair)!={'analytic','neural'}:
            raise ValueError('Missing paired real outcome')
        a,b=pair['analytic'],pair['neural']
        gained+=bool(b['satisfactory'] and not a['satisfactory'])
        lost+=bool(a['satisfactory'] and not b['satisfactory'])
        identical+=bool(a.get('svg_sha256') and a.get('svg_sha256')==b.get('svg_sha256'))
        family=next(c['family'] for c in cases if c['case_id']==name)
        families.setdefault(family,[]).append(int(b['satisfactory'])-int(a['satisfactory']))
    count=len(families)
    mean=float(np.mean([np.mean(v) for v in families.values()])) if families else 0.
    half=math.sqrt(2*math.log(2/(1-CRITERIA['confidence']))/max(1,count))
    demonstrated=count>=CRITERIA['min_independent_real_families'] and mean-half>0
    # Only the quality-improvement branch is assessed here. No equivalence or
    # speed promotion is inferred from a small study or non-significant result.
    return dict(promote_to_default=demonstrated,real_families=count,paired_real_trials=len(pairs),
        gained=gained,lost=lost,byte_identical_outputs=identical,acceptance_difference=mean,
        acceptance_95_half_width=half,quality_benefit_demonstrated=demonstrated,
        time_equivalence_established=False,
        outcome='Quality improvement demonstrated.' if demonstrated else
            'No demonstrated independent real end-to-end benefit; retain analytic default.')


def censored_startup(record):
    """No startup evidence is never evidence of a zero-cost disabled model."""
    return bool(record.get('observation_censored') is True
        and record.get('search_control', {}).get('stop_reason') == 'time_limit'
        and record.get('search_control', {}).get('isolated') is True
        and record.get('image_seconds', -1) >= record.get('budget_seconds', float('inf'))
        and record.get('components') == dict(path=None, sha256=None, events=[])
        and record.get('observed_controls') == []
        and not record.get('svg') and not record.get('svg_sha256')
        and record.get('quality') is None and record.get('structure') is None
        and record.get('satisfactory') is False and record.get('runtime_satisfactory') is False)


def verify(output, *, allow_unobserved_timeouts=False):
    from tools.run_plan_b_variations import measure_quality
    from tools.anytime_observer import summarize as render_summary
    report=json.loads((output/'report.json').read_text(encoding='utf-8'))
    manifest=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    if anytime.digest(output/'manifest.json')!=report['manifest_sha256'] or manifest['criteria']!=CRITERIA:
        raise ValueError('Changed frozen protocol/inputs')
    cases={c['case_id']:c for c in manifest['cases']}
    if len(cases)!=len(manifest['cases']):
        raise ValueError('Duplicate case')
    for case in cases.values():
        if anytime.digest(output/case['image'])!=case['input_sha256']:
            raise ValueError('Changed source')
    for name,sha in report['model_files'].items():
        if anytime.digest(output/'models'/name)!=sha:
            raise ValueError('Changed model/training protocol')
    expected={(mode,seed,c) for mode in ('analytic','neural') for seed in report['seeds'] for c in cases}
    actual=[(r['mode'],r['seed'],r['case_id']) for r in report['records']]
    if set(actual)!=expected or len(set(actual))!=len(actual):
        raise ValueError('Incomplete/duplicated paired matrix')
    observed=unobserved=0
    for r in report['records']:
        if (r['budget_seconds']!=report['budget_seconds'] or not r['search_control'].get('isolated')
                or r['search_control'].get('max_seconds')!=report['budget_seconds']):
            raise ValueError('Unequal/unobserved deadline')
        case=cases[r['case_id']]
        if (r['split'],r['family'])!=(case['split'],case['family']):
            raise ValueError('Changed partition')
        events=r['components']['events']
        component_path=r['components']['path']
        censored = allow_unobserved_timeouts and censored_startup(r)
        unobserved += bool(censored)
        if not censored and (not component_path or anytime.digest(output/component_path)!=r['components']['sha256']):
            raise ValueError('Missing/changed worker configuration')
        if not censored and [json.loads(l) for l in (output/component_path).read_text(encoding='utf-8').splitlines()]!=events:
            raise ValueError('Changed worker observations')
        for event in events:
            if event['neural_elements']['enabled']!=(r['mode']=='neural'):
                raise ValueError('Model switch did not reach worker')
            for observation in event['neural_elements']['observations']:
                if observation.get('error') or observation['model_sha256']!=report['model_files'][f'model-{r["seed"]}.json']:
                    raise ValueError('Model not executed/incorrect')
                observed+=1
            if (event['event']=='finished' and r['mode']=='neural'
                    and not event['neural_elements']['observations']):
                raise ValueError('Enabled model was never executed')
            if r['mode']=='analytic' and event['neural_elements']['observations']:
                raise ValueError('Analytic baseline executed the model')
        # Missing completion after a hard deadline is censored, not zero work.
        telemetry=render_summary(sorted((output/'telemetry'/f'{r["mode"]}-{r["budget_seconds"]:g}s-{r["seed"]}').glob(r['case_id']+'-*.jsonl')))
        if (telemetry!=r['telemetry'] or (not censored and not telemetry['workers_observed'])
                or (censored and (telemetry['workers_observed'] or telemetry['render_started'])) or any(
                report['source_sha256'].get(p)!=h for p,h in telemetry['source_sha256'].items())
            ):
            raise ValueError('Changed worker implementation/telemetry')
        passed=False
        if r.get('svg'):
            path=output/r['svg']
            if anytime.digest(path)!=r['svg_sha256']:
                raise ValueError('Changed output')
            svg=path.read_text(encoding='utf-8')
            image=cv2.imread(str(output/case['image']))
            quality,structure=measure_quality(image,svg),anytime.structure(case,svg,image)
            if quality!=r['quality'] or structure!=r['structure']:
                raise ValueError('Changed independent gates')
            passed=quality['satisfactory'] and structure['passed']
        if bool(passed)!=r['satisfactory']:
            raise ValueError('False acceptance')
    for row in report['detector_records']:
        weights,_=neural.load_model(output/'models'/f'model-{row["training_seed"]}.json')
        case=cases[row['case_id']]
        predictions=neural.detect(cv2.imread(str(output/case['image'])),weights)
        if predictions!=row['predictions'] or detection_check(predictions,case['elements'])!=row['check']:
            raise ValueError('Changed detector measurements')
    if (summarize(report['records'])!=report['summary'] or decision(report['records'],list(cases.values()))!=report['decision']
            or anytime.archive_snapshot()!=report['archive_before']):
        raise ValueError('Changed summary/archive')
    result = dict(attempts=len(actual),outputs=sum(bool(r.get('svg')) for r in report['records']),
        accepted=sum(r['satisfactory'] for r in report['records']),neural_observations=observed,
        archive_pairs_unchanged=report['archive_before']['cases'])
    if allow_unobserved_timeouts:
        result['unobserved_startup_timeouts'] = unobserved
    return result


def run(output,work,seeds,budget,smoke):
    output.mkdir(parents=True,exist_ok=False)
    work.mkdir(parents=True,exist_ok=False)
    (output/'outputs').mkdir()
    cases=prepare(output,smoke)
    # Freeze real inputs, labels and the decision rule before training/evaluation.
    models=training.train(output/'models',seeds)
    report=dict(schema='neural_elements_cli_v1',manifest_sha256=anytime.digest(output/'manifest.json'),
        seeds=list(seeds),budget_seconds=budget,smoke=smoke,criteria=CRITERIA,
        python=sys.version,platform=platform.platform(),
        source_sha256={p.relative_to(ROOT).as_posix():anytime.digest(p) for p in (ROOT/'src').rglob('*.py')},
        harness_sha256={p.name:anytime.digest(p) for p in (Path(__file__),Path(training.__file__),ROOT/'tools/anytime_observer.py')},
        model_files={p.name:anytime.digest(p) for p in (output/'models').glob('*.json')},
        archive_before=anytime.archive_snapshot(),training=models,
        detector_records=detector_study(output,cases,models),records=[])
    anytime.write_json(output/'report.json',report)
    for index,seed in enumerate(seeds):
        for mode in (('analytic','neural') if index%2==0 else ('neural','analytic')):
            args=['--neural-elements-model',str(output/'models'/f'model-{seed}.json')] if mode=='neural' else []
            rows=anytime.run_cell(output,work,cases,mode,budget,seed,cli_args=args,
                env_overrides=dict(ICC_COMPONENT_EVALUATION='1',ICC_NEURAL_EVALUATION='1',OPENBLAS_NUM_THREADS='1'))
            report['records'].extend(rows)
            report['summary']=summarize(report['records'])
            anytime.write_json(output/'report.json',report)
            print(f'{mode} seed={seed}: {sum(r["satisfactory"] for r in rows)}/{len(rows)} accepted',flush=True)
    # A small study cannot establish general equivalence or justify deployment.
    report['decision']=decision(report['records'],cases)
    anytime.write_json(output/'report.json',report)
    checks=verify(output)
    anytime.write_json(output/'checks.json',checks)
    compact={k:report[k] for k in ('schema','manifest_sha256','criteria','seeds','budget_seconds','summary','decision','model_files','harness_sha256','training')}
    compact.update(checks=checks,report_sha256=anytime.digest(output/'report.json'),
        detector_summary=[dict(split=split,expected=sum(r['check']['expected'] for r in report['detector_records'] if r['split']==split),
            matched=sum(r['check']['matched'] for r in report['detector_records'] if r['split']==split),
            unmatched_high_confidence=sum(r['check']['unmatched_high_confidence'] for r in report['detector_records'] if r['split']==split))
            for split in sorted({r['split'] for r in report['detector_records']})])
    anytime.write_json(output/'summary.json',compact)
    print(checks,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--work-dir',type=Path)
    parser.add_argument('--seeds',type=int,nargs='+',default=[17,42,101])
    parser.add_argument('--budget',type=float,default=5.)
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    if not math.isfinite(args.budget) or args.budget<=0 or not args.seeds or len(set(args.seeds))!=len(args.seeds):
        parser.error('Finite positive budget and unique seeds required')
    output=args.output_dir.resolve()
    if args.verify_only:
        print(verify(output))
    else:
        run(output,(args.work_dir or output.with_name(output.name+'-work')).resolve(),args.seeds,args.budget,args.smoke)


if __name__=='__main__':
    main()
