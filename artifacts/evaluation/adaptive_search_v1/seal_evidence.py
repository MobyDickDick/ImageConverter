"""Keep portable real CLI evidence; distinguish control simulations and counterexamples."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys
ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import cv2
from tools.run_plan_b_variations import measure_quality,render
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source=FOLDER/'cli'
    report=read(source/'report.json')
    (FOLDER/'sources').mkdir(exist_ok=True)
    for case in report['cases']:
        target=FOLDER/'sources'/case['image']
        shutil.copyfile(source/'sources'/case['image'],target)
        case['image']=target.relative_to(FOLDER).as_posix()
        assert sha(target)==case['source_sha256']
    for policy,data in report['policies'].items():
        target=FOLDER/policy
        target.mkdir(exist_ok=True)
        folder=source/('fixed' if policy=='fixed' else 'adaptive_release')
        log=(folder/'cli.log').read_text(encoding='utf-8')
        shutil.copyfile(folder/'cli.log',FOLDER/(policy+'.log'))
        save(FOLDER/(policy+'_result_map.json'),read(folder/'conversion/reports/conversion_result_map.json'))
        for case in data['cases']:
            svg=target/(case['case_id']+'.svg')
            shutil.copyfile(source/case['output_svg'],svg)
            case['output_svg']=svg.relative_to(FOLDER).as_posix()
            assert sha(svg)==case['output_sha256']
            times=re.findall(r'^\[INFO\] Konvertiert '+re.escape(case['case_id'])+r'\.(?:jpg|png).*Dauer=([\d.]+)s',log,re.M)
            case['conversion_attempts']=len(times)
            case['sum_reported_conversion_seconds']=round(sum(float(v) for v in times),3)
        assert all(c['conversion_attempts']>=1 for c in data['cases'])
    report['provenance']=dict(parent_commit='09ec51af9',seed=20261018,executes_converter=True,
        measures_raster_quality=True,evidence_kind='production_cli_fixed_vs_adaptive',
        timing_scope='reported per-conversion durations excluding process startup; selected-fit counts are separate')
    save(FOLDER/'benchmark.json',report)
    # Preserve the actual false early pass found while implementing the gate.
    bad=source/'adaptive/conversion/reports/conversion_result_map.json'
    row=read(bad)['anonymous_05.jpg']
    matches=[p for d in ('converted_svgs','converted_svg_failed')
        for p in (source/'adaptive/conversion'/d).glob('*.svg') if p.stem=='anonymous_05']
    assert len(matches)==1
    target=FOLDER/'counterexample.svg'
    shutil.copyfile(matches[0],target)
    image=cv2.imread(str(FOLDER/'sources/anonymous_05.jpg'))
    gate=measure_quality(image,target.read_text(encoding='utf-8'))
    assert row['search_satisfactory'] and not gate['satisfactory']
    save(FOLDER/'counterexample.json',dict(evidence_kind='superseded_real_cli_counterexample',
        source='sources/anonymous_05.jpg',svg=target.name,svg_sha256=sha(target),
        old_declared_satisfactory=True,independent_quality=gate,
        current_pixel_quality=pixel_quality(image,render(target.read_text(encoding='utf-8'),image.shape[1],image.shape[0]))))
    # Independent 17-case battery, already generated through the actual CLI.
    source=ROOT/'.tmp/adaptive-planb'
    target=FOLDER/'holdout'
    target.mkdir(exist_ok=True)
    battery=read(source/'report.json')
    assert battery['summary']['passed']==battery['summary']['completed']==17
    for case in battery['cases']:
        folder=target/case['case_id']
        folder.mkdir(exist_ok=True)
        for origin,name,key in ((source/case['output_svg'],'output.svg','output_svg'),
            (source/case['reference_svg'],'reference.svg','reference_svg'),
            (source/case['case_id']/'input'/(case['case_id']+'.png'),'input.png','input_png'),
            (source/case['case_id']/'converter.log','converter.log','converter_log')):
            shutil.copyfile(origin,folder/name)
            case[key]=(folder/name).relative_to(target).as_posix()
        case.pop('command',None)
        case.pop('converter_log_tail',None)
    battery.pop('selection',None)
    save(target/'report.json',battery)
    for name in ('smokes.log','smokes.xml'):
        shutil.copyfile(FOLDER/'checks'/name,FOLDER/'checks_final'/name)
    save(FOLDER/'source_snapshot.json',{p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'src').rglob('*.py')})
    print({policy:dict(attempts=sum(c['conversion_attempts'] for c in data['cases']),
        seconds=sum(c['sum_reported_conversion_seconds'] for c in data['cases'])) for policy,data in report['policies'].items()})

if __name__=='__main__':
    main()
