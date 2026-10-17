"""Copy actual saved CLI evidence to stable, portable paths and remeasure it."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_short_label_search import evaluate


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--variations',type=Path,action='append',default=[])
    args = parser.parse_args()
    original = read(FOLDER/'manifest.json')
    for context in ('neutral','catalog'):
        source = args.run_dir/context
        target = FOLDER if context == 'neutral' else FOLDER/'catalog_context'
        target.mkdir(exist_ok=True)
        fresh = read(source/'manifest.json')
        for case,neutral in zip(fresh['cases'],original['cases']):
            case['image'] = ('' if context == 'neutral' else '../')+neutral['image']
            for mode in ('before','after'):
                svg = target/mode/(case['case_id']+'.svg')
                svg.parent.mkdir(exist_ok=True)
                shutil.copyfile(source/case[mode+'_svg'],svg)
                case[mode+'_svg'] = svg.relative_to(target).as_posix()
        save(target/'manifest.json',fresh)
        report = evaluate(target)
        report['reference_access'] = read(source/'acceptance.json')['reference_access']
        save(target/'acceptance.json',report)
        for mode in ('before','after'):
            shutil.copyfile(source/(mode+'.log'),target/(mode+'.log'))
            if context == 'catalog':
                shutil.copyfile(source/('inputs_'+mode)/'descriptions.xml',target/(mode+'.xml'))
    for i,source in enumerate(args.variations):
        target = FOLDER/('independent' if i == 0 else 'independent_second_seed')
        target.mkdir(exist_ok=True)
        report = read(source/'report.json')
        assert report['summary']['passed'] == report['summary']['completed'] == 17
        for case in report['cases']:
            folder = target/case['case_id']
            folder.mkdir(exist_ok=True)
            for origin,name,key in (
                (source/case['output_svg'],'output.svg','output_svg'),
                (source/case['reference_svg'],'reference.svg','reference_svg'),
                (source/case['case_id']/'input'/(case['case_id']+'.png'),'input.png','input_png'),
                (source/case['case_id']/'converter.log','converter.log','converter_log')):
                shutil.copyfile(origin,folder/name)
                case[key] = (folder/name).relative_to(target).as_posix()
            case.pop('command',None)
            case.pop('converter_log_tail',None)
        report.pop('selection',None)
        save(target/'report.json',report)
    save(FOLDER/'source_sha256.json', {p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'src').rglob('*.py')})


if __name__ == '__main__':
    main()
