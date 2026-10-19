"""Runtime switches, honest causal decisions and independently checked outputs."""
import json

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterComponents import BOT_NAMES, registry, snapshot
from src.iCCModules.imageCompositeConverterSearchBots import Bot
from src.iCCModules.imageCompositeConverterSearchPortfolio import (
    configured_image_search, explore_parameters, search_configuration, settings,
)
from src.iCCModules.imageCompositeConverterCli import parseArgsImpl
from tools import run_component_value as value
from tools import run_anytime_benchmark as anytime
from tools.anytime_observer import summarize as render_summary


def run_search(disabled=(), observed=True):
    def measure(p):
        loss = float(np.sum((p-1)**2))
        return loss,loss,str(tuple(p)),np.zeros((2,2,3))
    with search_configuration(mode='portfolio',adaptive=True,budget=32,seed=17,
                              disabled_bots=disabled,component_observation=observed):
        with configured_image_search('one') as session:
            p,best,report = explore_parameters(np.zeros(4),2,measure,
                (10.,10.,'initial',np.zeros((2,2,3))),source='model',image=np.zeros((2,2,3)))
            return p,best,report,snapshot(session,settings())


@pytest.mark.parametrize('disabled', [[n] for n in BOT_NAMES]+[list(BOT_NAMES)])
def test_disabled_bots_never_propose(monkeypatch,disabled):
    propose = Bot.proposal
    initialize = Bot.__init__
    called = set()
    def guarded_init(bot,name,*args):
        assert name not in disabled
        return initialize(bot,name,*args)
    def guarded(bot,*args):
        assert bot.name not in disabled
        called.add(bot.name)
        return propose(bot,*args)
    monkeypatch.setattr(Bot,'proposal',guarded)
    monkeypatch.setattr(Bot,'__init__',guarded_init)
    _,_,report,observed = run_search(disabled)
    assert all(observed['bots'][n]['proposals']==0 for n in disabled)
    assert {a['strategy'] for a in report['attempts']}==set(BOT_NAMES)-set(disabled)
    assert called==set(BOT_NAMES)-set(disabled)


def test_observation_changes_neither_candidates_nor_measurement_budget():
    on,off = run_search(),run_search(observed=False)
    assert np.array_equal(on[0],off[0]) and on[1][:3]==off[1][:3]
    assert on[2]['additional_evaluations']==off[2]['additional_evaluations']
    assert sum(b['generated'] for b in on[3]['bots'].values())>0
    assert sum(b['generated'] for b in off[3]['bots'].values())==0
    for bot in on[3]['bots'].values():
        assert bot['proposals']==bot['valid']+bot['rejected']
        assert bot['active_seconds']>=0


@pytest.mark.parametrize('args', [['--disable-search-bot','missing'],
    ['--disable-search-bot','color_pair','--search-policy','fixed'],
    ['--disable-search-bot','color_pair','--search-mode','legacy']])
def test_cli_rejects_unknown_or_ineffective_switches(args):
    with pytest.raises(SystemExit):
        parseArgsImpl(argv=['images',*args],ac08_regression_set_name='r',
                      ac08_regression_variants=(),svg_render_subprocess_timeout_sec=5.)


def test_registry_cannot_disable_quality_gates():
    with pytest.raises(ValueError):
        registry(['pixel_gate'])
    with pytest.raises(ValueError):
        with search_configuration(mode='legacy',disabled_bots=['color_pair']):
            pass


def test_repeated_seeds_do_not_turn_one_family_into_equivalence():
    rows = []
    for seed in range(60):
        for mode in ('full','none'):
            rows.append(dict(case_id='same',seed=seed,mode=mode,split='holdout',family='rare',
                             satisfactory=True,image_seconds=1.,quality=None))
    result = value.compare(rows)[1]
    assert result['pairs']==60 and result['families']==1
    assert result['classification']=='unclear'
    assert result['family_interval_95']==[-1.,1.]


@pytest.fixture
def evidence(tmp_path,monkeypatch):
    import cv2
    from tools.run_plan_b_variations import render,measure_quality
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
           '<rect width="100" height="100" fill="white"/>'
           '<circle cx="50" cy="50" r="25" stroke="black" stroke-width="2" fill="none"/></svg>')
    raster = render(svg,100,100)
    cv2.imwrite(str(tmp_path/'case.png'),raster)
    (tmp_path/'out.svg').write_text(svg,encoding='utf-8')
    case = dict(case_id='case',image='case.png',input_sha256=anytime.digest(tmp_path/'case.png'),
                kind='objects',split='holdout',family='circle',expected_objects=[dict(kind='circle',bbox=[24,24,52,52])])
    anytime.write_json(tmp_path/'manifest.json',dict(cases=[case]))
    rows,arms = [],[dict(id='full',disabled=[],case_ids=['case']),dict(id='none',disabled=list(BOT_NAMES),case_ids=['case'])]
    for arm in arms:
        directory = tmp_path/'telemetry'/(arm['id']+'-5s-17')
        directory.mkdir(parents=True)
        log = directory/'case_components.jsonl'
        observed = run_search(arm['disabled'])[3]
        events = [dict(event='configured',**observed),dict(event='finished',**observed)]
        log.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf-8')
        telemetry_path = directory/'case-001.jsonl'
        telemetry_path.write_text(json.dumps(dict(event='worker_observed',source_sha256={'src/fixture.py':'hash'}))+'\n',encoding='utf-8')
        rows.append(dict(case_id='case',mode=arm['id'],seed=17,budget_seconds=5.,split='holdout',family='circle',
            image_seconds=1.,search_control=dict(isolated=True,max_seconds=5.),
            satisfactory=True,status='satisfactory',svg='out.svg',svg_sha256=anytime.digest(tmp_path/'out.svg'),
            quality=measure_quality(raster,svg),structure=anytime.structure(case,svg,raster),
            components=dict(path=log.relative_to(tmp_path).as_posix(),sha256=anytime.digest(log),events=events),
            telemetry=render_summary([telemetry_path])))
    archive = dict(cases=377)
    monkeypatch.setattr(anytime,'archive_snapshot',lambda:archive)
    report = dict(smoke=True,criteria=value.CRITERIA,variants=arms,seeds=[17],budget_seconds=5.,
        manifest_sha256=anytime.digest(tmp_path/'manifest.json'),source_sha256={'src/fixture.py':'hash'},records=rows,
        summary=value.summary(rows),comparisons=value.compare(rows),archive_before=archive,archive_after=archive)
    anytime.write_json(tmp_path/'report.json',report)
    return tmp_path,report


def test_verification_remeasures_actual_vectors(evidence):
    path,_ = evidence
    assert value.verify(path)['independent_passes']==2


def test_rotated_arm_before_baseline_is_unpaired_until_baseline_arrives(evidence):
    path,report = evidence
    report['records'] = report['records'][1:]
    report.pop('archive_after')
    report['summary'] = value.summary(report['records'])
    report['comparisons'] = value.compare(report['records'])
    assert all(c['pairs']==0 and c['classification']=='unclear' for c in report['comparisons'])
    anytime.write_json(path/'report.json',report)
    assert value.verify(path,complete=False)['attempts']==1
    with pytest.raises(ValueError,match='matrix'):
        value.verify(path)


def test_resume_rejects_changed_runtime_before_starting_more_conversions(evidence,monkeypatch):
    path,report = evidence
    report['suite']='study'
    anytime.write_json(path/'report.json',report)
    monkeypatch.setattr(anytime,'run_cell',lambda *a,**k:pytest.fail('conversion started before provenance check'))
    with pytest.raises(ValueError,match='Runtime changed'):
        value.run(path,path/'unused-work',5.,[17],smoke=True,resume=True)


def test_startup_timeout_without_observation_stays_a_failure_in_the_denominator(evidence):
    path,report=evidence
    row=report['records'][-1]
    row.update(components=dict(path=None,sha256=None,events=[]),observation_censored=True,
               satisfactory=False,svg=None,quality=None,structure=None,image_seconds=5.,status='timeout_no_valid_output')
    row['search_control']['stop_reason']='time_limit'
    report['summary'],report['comparisons']=value.summary(report['records']),value.compare(report['records'])
    anytime.write_json(path/'report.json',report)
    checks=value.verify(path)
    assert checks['attempts']==2 and checks['independent_passes']==1
    assert checks['unobserved_configuration_attempts']==1
    group=next(g for g in report['summary'] if g['variant']=='none')
    assert group['missing_outputs']==1 and group['incomplete_observations']==1
    assert group['max_worker_peak_memory_bytes'] is None
    row['satisfactory']=True
    anytime.write_json(path/'report.json',report)
    with pytest.raises(ValueError,match='censored'):
        value.verify(path)


@pytest.mark.parametrize('mutation', ['duplicate','missing','disabled_ran','switch_ignored','output','input','budget','forged_gate','source','counts','disabled_winner'])
def test_verification_rejects_invalid_or_tampered_evidence(evidence,mutation):
    path,report = evidence
    row = report['records'][-1]
    if mutation=='duplicate':
        report['records'].append(row)
    elif mutation=='missing':
        report['records'].pop()
    elif mutation in {'disabled_ran','switch_ignored'}:
        events = row['components']['events']
        if mutation=='disabled_ran':
            events[-1]['bots']['color_pair']['proposals'] = 1
        else:
            events[-1]['registry'][0]['enabled'] = True
        log = path/row['components']['path']
        log.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf-8')
        row['components']['sha256'] = anytime.digest(log)
    elif mutation in {'output','input'}:
        with (path/('out.svg' if mutation=='output' else 'case.png')).open('ab') as handle:
            handle.write(b'changed')
    elif mutation=='budget':
        row['search_control']['max_seconds'] = 6.
    elif mutation=='forged_gate':
        row['satisfactory'] = False
    elif mutation=='source':
        report['source_sha256']['src/fixture.py'] = 'different'
    elif mutation=='counts':
        row['telemetry']['render_started'] = 50
    elif mutation=='disabled_winner':
        row['result_provenance'] = dict(registrations=dict(fit=dict(search=dict(winning_strategy='color_pair'))))
    anytime.write_json(path/'report.json',report)
    with pytest.raises(ValueError):
        value.verify(path)
