"""Paired component ablations using real supervised CLI outputs and fixed gates."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from src.iCCModules.imageCompositeConverterComponents import BOT_NAMES, registry
from tools import run_anytime_benchmark as anytime
from tools.anytime_observer import summarize as render_summary

ROOT = anytime.ROOT
DEFAULT_SEEDS = (17, 42, 20261018)
# Predeclared coverage/precision requirements. Seeds do not create new families.
CRITERIA = dict(min_families=8, acceptance_equivalence_margin=.05,
                relative_time_margin=.10, relative_output_mse_margin=.01,
                confidence=.95)


def variants(suite='study'):
    result = [dict(id='full', disabled=[])]
    result += [dict(id='without_'+name, disabled=[name]) for name in BOT_NAMES]
    result += [dict(id='without_joint_geometry', disabled=['joint_restart','geometry_pair']),
               dict(id='none', disabled=list(BOT_NAMES)),
               dict(id='geometry_only', disabled=[n for n in BOT_NAMES if n != 'geometry_pair']),
               dict(id='geometry_joint', disabled=[n for n in BOT_NAMES if n not in {'geometry_pair','joint_restart'}]),
               dict(id='unobserved', disabled=[], observation=False)]
    result += [dict(id='control_full',disabled=[],controls=['provider_a','provider_b']),
               dict(id='control_b',disabled=[],controls=['provider_b']),
               dict(id='control_none',disabled=[],controls=[]),
               dict(id='control_overhead',disabled=[],controls=['provider_a','provider_b','overhead'])]
    for arm in result:
        if 'controls' in arm:
            arm.update(search_policy='fixed',search_budget=32,budget_seconds=15.)
    return [v for v in result if v['id'] in {'full','without_fine_coordinates','none'}] if suite=='retention' else result


def prepare_cases(output):
    cases = anytime.prepare_cases(output)
    # These are evaluation partitions, never optimizer-training data. Freeze
    # before running the first arm; no thresholds or scheduler tuning follows.
    for i, case in enumerate(cases):
        case['split'] = 'development' if i in (0,1,4) else 'holdout'
        case['family'] = {'case_02':'hz_text', 'case_03':'hz_text'}.get(case['case_id'],case['family'])
    # Real small Lux source forces the additional bots beyond early successes.
    prior = ROOT/'artifacts/evaluation/bot_search_v1'
    old = json.loads((prior/'report.json').read_text(encoding='utf-8'))['cases'][5]
    path = output/'sources/case_08.jpg'
    shutil.copyfile(prior/old['image'],path)
    cases.append(dict(case_id='case_08',image=path.relative_to(output).as_posix(),
        input_sha256=anytime.digest(path),kind='label',label='Lux',family='lux_text',
        split='development',description=old['description'],provenance='bot_search_v1/anonymous_05'))
    anytime.write_json(output/'manifest.json',dict(cases=cases))
    return cases


def prepare_retention(output):
    """New sources frozen after choosing retention; never used to tune the bots."""
    import cv2
    from tools.run_plan_b_variations import render
    (output/'sources').mkdir()
    cases = []
    for i,(label,size,font,spacing,fill) in enumerate((
        ('kWh',44,14.,9.,'#d7e9e6'),('mPa',52,17.,10.5,'#e5e0ed'),('dB',38,13.,9.,'#f0e5d6'))):
        glyphs = ''.join(f'<text x="{size/2+(j-(len(label)-1)/2)*spacing}" y="{size*.64}" '
                        f'font-family="Arial" font-size="{font}" font-weight="700" text-anchor="middle" '
                        f'fill="#273746">{char}</text>' for j,char in enumerate(label))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
               f'<rect width="{size}" height="{size}" fill="white"/>'
               f'<circle cx="{size/2}" cy="{size/2}" r="{size*.39}" stroke="#34495e" '
               f'stroke-width="1.4" fill="{fill}"/>'+glyphs+'</svg>')
        path = output/f'sources/retention_{i:02}.png'
        if not cv2.imwrite(str(path),render(svg,size,size)):
            raise ValueError('Could not freeze retention source')
        cases.append(dict(case_id=path.stem,image=path.relative_to(output).as_posix(),
            input_sha256=anytime.digest(path),kind='label',label=label,family=label+'_symbol',split='holdout',
            description=f'Eine einfarbige Kreisscheibe mit dunkler Randkontur. Dunkle serifenlose Beschriftung "{label}". Keine Anschlüsse. Weißer Hintergrund.'))
    anytime.write_json(output/'manifest.json',dict(cases=cases))
    return cases


def compare(records):
    """Conservative family-level intervals, with missing outputs in the denominator."""
    base = {(r['case_id'],r['seed']):r for r in records if r['mode']=='full'}
    results = []
    for mode in sorted({r['mode'] for r in records if not r['mode'].startswith('control_')}-{'full'}):
        for split in ('development','holdout'):
            rows = [r for r in records if r['mode']==mode and r['split']==split
                    and (r['case_id'],r['seed']) in base]
            pairs = [(base[(r['case_id'],r['seed'])],r) for r in rows]
            families = sorted({r['family'] for r in rows})
            effects = [sum(int(b['satisfactory'])-int(a['satisfactory']) for a,b in pairs if b['family']==f)
                       /sum(b['family']==f for a,b in pairs) for f in families]
            effect = sum(effects)/len(effects) if effects else 0.
            # Hoeffding bound for independent family effects in [-1,1]; broad
            # on purpose. Multiple seeds or paraphrases cannot inflate n.
            radius = math.sqrt(2*math.log(2/(1-CRITERIA['confidence']))/len(families)) if families else 2.
            interval = [max(-1.,effect-radius), min(1.,effect+radius)]
            costs = [(b['image_seconds']-a['image_seconds'])/max(.001,a['image_seconds'])
                     for a,b in pairs if a['image_seconds'] is not None and b['image_seconds'] is not None]
            mse = [(b['quality']['metrics']['normalized_mse']-a['quality']['metrics']['normalized_mse'])
                   /max(1e-9,a['quality']['metrics']['normalized_mse']) for a,b in pairs if a['quality'] and b['quality']]
            sufficient = len(families)>=CRITERIA['min_families']
            status = 'unclear'
            if sufficient and interval[0]>0:
                status = 'harmful_component'  # its removal improves acceptance
            elif sufficient and interval[1]<0:
                status = 'useful_component'
            elif (sufficient and max(abs(v) for v in interval)<=CRITERIA['acceptance_equivalence_margin']
                  and len(costs)==len(pairs) and all(abs(v)<=CRITERIA['relative_time_margin'] for v in costs)
                  and len(mse)==len(pairs) and all(abs(v)<=CRITERIA['relative_output_mse_margin'] for v in mse)):
                status = 'equivalent_in_tested_scope'
            results.append(dict(variant=mode,split=split,pairs=len(pairs),families=len(families),
                acceptance_effect_of_removal=effect, family_interval_95=interval,
                gained=sum(b['satisfactory'] and not a['satisfactory'] for a,b in pairs),
                lost=sum(a['satisfactory'] and not b['satisfactory'] for a,b in pairs),
                median_relative_seconds=anytime.percentile(costs,.5),
                p95_relative_seconds=anytime.percentile(costs,.95),
                output_quality_pairs=len(mse), max_relative_output_mse_change=max(mse,default=None),
                classification=status))
    return results


def component_end(record):
    events=record['components']['events']
    return events[-1] if events else dict(event='unobserved',bots={},worker_peak_memory_bytes=None,observation_seconds=0.)


def observation_complete(record):
    return component_end(record)['event']=='finished' and record['search_control'].get('stop_reason')!='time_limit'


def summary(records):
    result = []
    for mode,split in sorted({(r['mode'],r['split']) for r in records}):
        rows = [r for r in records if (r['mode'],r['split'])==(mode,split)]
        result.append(dict(variant=mode,split=split,attempts=len(rows),
            satisfactory=sum(r['satisfactory'] for r in rows),
            missing_outputs=sum(not r.get('svg') for r in rows),
            status_counts=dict(Counter(r['status'] for r in rows)),
            median_image_seconds=anytime.percentile([r['image_seconds'] for r in rows if r['image_seconds'] is not None],.5),
            p95_image_seconds=anytime.percentile([r['image_seconds'] for r in rows if r['image_seconds'] is not None],.95),
            render_calls=sum(r['telemetry']['render_started'] for r in rows),
            max_worker_peak_memory_bytes=max((component_end(r)['worker_peak_memory_bytes'] for r in rows
                if component_end(r)['worker_peak_memory_bytes'] is not None),default=None),
            bot_proposals=sum(sum(v['proposals'] for v in component_end(r)['bots'].values()) for r in rows),
            complete_observations=sum(observation_complete(r) for r in rows),
            incomplete_observations=sum(not observation_complete(r) for r in rows),
            observation_seconds=sum(component_end(r)['observation_seconds'] for r in rows)))
    return result


def verify(output, *, complete=True):
    import cv2
    from tools.run_plan_b_variations import measure_quality
    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    manifest = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    if anytime.digest(output/'manifest.json') != report['manifest_sha256']:
        raise ValueError('Manifest changed')
    cases = {c['case_id']:c for c in manifest['cases']}
    if len(cases)!=len(manifest['cases']):
        raise ValueError('Duplicate manifest cases')
    arms = {v['id']:v for v in report['variants']}
    expected = {(v,s,c) for v,a in arms.items() for s in report['seeds']
                for c in a['case_ids']}
    if report['criteria']!=CRITERIA:
        raise ValueError('Decision criteria changed')
    if not report['smoke'] and {v['id']:v for v in variants(report.get('suite','study'))}!={
            v:{k:x for k,x in a.items() if k!='case_ids'} for v,a in arms.items()}:
        raise ValueError('Missing declared component variants')
    for arm in arms.values():
        declared_cases = [c for c in cases if 'controls' not in arm or c in {'case_00','case_02'}]
        if arm['case_ids']!=declared_cases:
            raise ValueError('Variant case coverage changed')
    actual = [(r['mode'],r['seed'],r['case_id']) for r in report['records']]
    if (not set(actual)<=expected or (complete and set(actual)!=expected)
            or len(set(actual))!=len(actual)):
        raise ValueError('Component matrix incomplete or duplicated')
    for c in cases.values():
        if anytime.digest(output/c['image']) != c['input_sha256']:
            raise ValueError('Input changed')
    for r in report['records']:
        arm = arms[r['mode']]
        if (r['budget_seconds']!=arm.get('budget_seconds',report['budget_seconds']) or not r['search_control'].get('isolated')
                or r['search_control'].get('max_seconds')!=r['budget_seconds']):
            raise ValueError('Unequal image budget')
        component = r['components']
        censored = r.get('observation_censored',False)
        if censored:
            if (component!=dict(path=None,sha256=None,events=[]) or r.get('svg') or r['satisfactory']
                    or r['search_control'].get('stop_reason')!='time_limit'
                    or r['image_seconds'] is None or r['image_seconds']<r['budget_seconds']-.01):
                raise ValueError('Invalid censored observation')
            events=[]
        else:
            if not component.get('path'):
                raise ValueError('Missing observed configuration')
            if anytime.digest(output/component['path'])!=component['sha256']:
                raise ValueError('Component telemetry changed')
            events = [json.loads(line) for line in (output/component['path']).read_text(encoding='utf-8').splitlines()]
            if events!=component['events'] or not events or events[0]['event']!='configured':
                raise ValueError('Missing observed configuration')
        for e in events:
            if e['registry']!=registry(arm['disabled']) or e['observation_enabled']!=arm.get('observation',True):
                raise ValueError('Runtime switch not applied')
            if any(e['bots'][n]['proposals'] for n in arm['disabled']):
                raise ValueError('Disabled bot executed')
        for registration in (r.get('result_provenance') or {}).get('registrations',{}).values():
            winner = (registration.get('search') or {}).get('winning_strategy')
            if winner in arm['disabled']:
                raise ValueError('Disabled bot claimed output provenance')
        cell_id = f'{r["mode"]}-{r["budget_seconds"]:g}s-{r["seed"]}'
        telemetry = render_summary(sorted((output/'telemetry'/cell_id).glob(r['case_id']+'-*.jsonl')))
        if telemetry!=r['telemetry'] or (not telemetry['workers_observed'] and not censored) or any(
                report['source_sha256'].get(p)!=h for p,h in telemetry['source_sha256'].items()):
            raise ValueError('Worker provenance or render counts changed')
        observed = [json.loads(line).get('applied_controls')
                    for path in sorted((output/'telemetry'/cell_id).glob(r['case_id']+'-*.jsonl'))
                    for line in path.read_text(encoding='utf-8').splitlines()
                    if line.startswith('{') and line.endswith('}') and json.loads(line)['event']=='worker_observed']
        if observed!=r.get('observed_controls',observed) or observed!=[arm.get('controls')]*telemetry['workers_observed']:
            raise ValueError('Attribution controls were not applied in workers')
        case = cases[r['case_id']]
        if (r['split'],r['family'])!=(case['split'],case['family']):
            raise ValueError('Partition changed')
        passed = False
        if r.get('svg'):
            path = output/r['svg']
            if anytime.digest(path)!=r['svg_sha256']:
                raise ValueError('Output changed')
            svg, image = path.read_text(encoding='utf-8'), cv2.imread(str(output/case['image']))
            quality, objects = measure_quality(image,svg),anytime.structure(case,svg,image)
            if quality!=r['quality'] or objects!=r['structure']:
                raise ValueError('Independent measurements changed')
            passed = bool(quality['satisfactory'] and objects['passed'])
        if passed!=r['satisfactory']:
            raise ValueError('False acceptance')
    if summary(report['records'])!=report['summary'] or compare(report['records'])!=report['comparisons']:
        raise ValueError('Decision measurements changed')
    if 'controls' in report and control_summary(report['records'])!=report['controls']:
        raise ValueError('Control summary changed')
    if complete and not report['smoke'] and report.get('suite','study')=='study':
        control = report['controls']
        if not all(control.get(k) for k in ('complete','helpful_capability_detected','substitutes_detected','pure_overhead_same_quality')) or control['median_added_seconds']<=0:
            raise ValueError('Attribution controls did not demonstrate the declared effects')
    if anytime.archive_snapshot()!=report['archive_before'] or report['archive_before']!=report.get('archive_after',report['archive_before']):
        raise ValueError('Archive changed')
    return dict(attempts=len(actual), outputs=sum(bool(r.get('svg')) for r in report['records']),
                independent_passes=sum(r['satisfactory'] for r in report['records']),
                disabled_bot_proposals_observed=0,
                unobserved_configuration_attempts=sum(bool(r.get('observation_censored')) for r in report['records']),
                archive_pairs_unchanged=report['archive_before']['cases'])


def control_summary(records):
    groups = {mode:{(r['case_id'],r['seed']):r for r in records if r['mode']==mode}
              for mode in ('control_full','control_b','control_none','control_overhead')}
    if not groups['control_full']:
        return dict(complete=False)
    keys = set(groups['control_full'])
    if any(set(rows)!=keys for rows in groups.values()):
        return dict(complete=False)
    observed=all(not r.get('observation_censored') and r['telemetry']['workers_observed']>0
                 for rows in groups.values() for r in rows.values())
    return dict(complete=True, pairs=len(keys),
        helpful_capability_detected=observed and all(groups['control_full'][k]['satisfactory'] and not
                                       groups['control_none'][k]['satisfactory'] and
                                       groups['control_none'][k]['telemetry']['render_invalid']>0 for k in keys),
        substitutes_detected=observed and all(groups['control_full'][k]['satisfactory'] and
                                groups['control_b'][k]['satisfactory'] and groups['control_full'][k].get('svg_sha256')==
                                groups['control_b'][k].get('svg_sha256') for k in keys),
        pure_overhead_same_quality=observed and all(groups['control_full'][k]['satisfactory'] and
                                      groups['control_overhead'][k]['satisfactory'] and groups['control_full'][k].get('svg_sha256')==
                                      groups['control_overhead'][k].get('svg_sha256') for k in keys),
        median_added_seconds=anytime.percentile([
            groups['control_overhead'][k]['image_seconds']-groups['control_full'][k]['image_seconds']
            for k in sorted(keys)],.5))


def run(output,work,budget,seeds,smoke=False,suite='study',resume=False):
    if resume:
        report = json.loads((output/'report.json').read_text(encoding='utf-8'))
        if (report['budget_seconds'],report['seeds'],report['smoke'],report['suite'])!=(budget,seeds,smoke,suite):
            raise ValueError('Resume settings changed')
        verify(output,complete=False)
        if report['source_sha256']!={p.relative_to(ROOT).as_posix():anytime.digest(p) for p in (ROOT/'src').rglob('*.py')}:
            raise ValueError('Runtime changed since the interrupted measurement')
        for name in ('tools/component_controls.py','tools/anytime_observer.py'):
            if report['harness_sha256'][name]!=anytime.digest(ROOT/name):
                raise ValueError('Measured instrumentation changed since the interrupted run')
        cases = json.loads((output/'manifest.json').read_text(encoding='utf-8'))['cases']
        arms = report['variants']
    else:
        output.mkdir(parents=True,exist_ok=False)
        work.mkdir(parents=True,exist_ok=False)
        initialize(output,work,budget,seeds,smoke,suite)
        report = json.loads((output/'report.json').read_text(encoding='utf-8'))
        cases = json.loads((output/'manifest.json').read_text(encoding='utf-8'))['cases']
        arms = report['variants']
    for i,seed in enumerate(seeds):
        order = arms[i%len(arms):]+arms[:i%len(arms)]
        if i%2:
            order = list(reversed(order))
        for arm in order:
            existing = [r for r in report['records'] if r['mode']==arm['id'] and r['seed']==seed]
            if existing:
                if {r['case_id'] for r in existing}!=set(arm['case_ids']):
                    raise ValueError('Cannot skip an incomplete cell')
                continue
            cli = [part for n in arm['disabled'] for part in ('--disable-search-bot',n)]
            if arm.get('observation') is False:
                cli.append('--no-component-observation')
            if 'search_policy' in arm:
                cli.extend(['--search-policy',arm['search_policy'],'--search-budget',str(arm['search_budget'])])
            selected = [c for c in cases if c['case_id'] in arm['case_ids']]
            env,hook = {'ICC_COMPONENT_EVALUATION':'1'},''
            if 'controls' in arm:
                env['ICC_COMPONENT_CONTROLS'] = ','.join(arm['controls'])
                hook = 'from tools.component_controls import install\ninstall()\n'
            records = anytime.run_cell(output,work,selected,arm['id'],arm.get('budget_seconds',budget),seed,
                cli_args=cli,env_overrides=env,bootstrap_hook=hook,recover=resume)
            report['records'].extend(records)
            report['summary'],report['comparisons'] = summary(report['records']),compare(report['records'])
            report['controls'] = control_summary(report['records'])
            anytime.write_json(output/'report.json',report)
            print(f'{arm["id"]} seed={seed}: {sum(r["satisfactory"] for r in records)}/{len(records)} accepted; '+
                  f'{sum(sum(b["proposals"] for b in component_end(r)["bots"].values()) for r in records)} observed bot proposals',flush=True)
    report['archive_after'] = anytime.archive_snapshot()
    anytime.write_json(output/'report.json',report)
    checks = verify(output)
    anytime.write_json(output/'checks.json',checks)
    print(checks,flush=True)


def initialize(output,work,budget,seeds,smoke,suite):
    (output/'outputs').mkdir()
    cases = prepare_retention(output) if suite=='retention' else prepare_cases(output)
    arms = variants(suite)
    if smoke:
        cases = [c for c in cases if c['case_id'] in {'case_00','case_08'}]
        anytime.write_json(output/'manifest.json',dict(cases=cases))
        arms = [a for a in arms if a['id'] in {'full','none','unobserved'}]
    for arm in arms:
        arm['case_ids'] = [c['case_id'] for c in cases if 'controls' not in arm or c['case_id'] in {'case_00','case_02'}]
    report = dict(schema='component_value_cli_v1', variants=arms, suite=suite,budget_seconds=budget,seeds=seeds,
        criteria=CRITERIA,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256={p.relative_to(ROOT).as_posix():anytime.digest(p) for p in (ROOT/'src').rglob('*.py')},
        harness_sha256={p.relative_to(ROOT).as_posix():anytime.digest(p) for p in
                        (Path(__file__),ROOT/'tools/run_anytime_benchmark.py',ROOT/'tools/anytime_observer.py',ROOT/'tools/component_controls.py')},
        manifest_sha256=anytime.digest(output/'manifest.json'),python=sys.version,platform=platform.platform(),
        archive_before=anytime.archive_snapshot(),records=[],smoke=smoke,
        protocol='Serial cold CLI processes, fresh copies/caches per arm/seed. Rotating/reversing arm order. Fixed maximum equals image budget. No gate switches. Full output-conditioned metrics only; missing outputs stay failures. Families, not seeds, determine evidence coverage.')
    report['summary'],report['comparisons'],report['controls'] = [],[],dict(complete=False)
    anytime.write_json(output/'report.json',report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--work-dir',type=Path)
    parser.add_argument('--budget',type=float,default=5.)
    parser.add_argument('--seeds',type=int,nargs='+',default=DEFAULT_SEEDS)
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--suite',choices=('study','retention'),default='study')
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--resume',action='store_true',help='Recheck and preserve completed cells of an interrupted run')
    args = parser.parse_args()
    if not math.isfinite(args.budget) or args.budget<=0 or len(set(args.seeds))!=len(args.seeds):
        parser.error('Use a positive finite budget and unique seeds')
    if args.verify_only:
        print(verify(args.output_dir.resolve()))
    else:
        if args.smoke and args.suite!='study':
            parser.error('--smoke is only available for the study suite')
        run(args.output_dir.resolve(),(args.work_dir or ROOT/'.tmp/component-value').resolve(),args.budget,args.seeds,args.smoke,args.suite,args.resume)


if __name__=='__main__':
    main()
