"""Retain saved CLI vectors, inputs, logs and independently measured decisions."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_oriented_circle_linework_recheck import evaluate, symbol_semantics


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def variations(source, destination):
    report = read(source / 'report.json')
    assert report['summary']['completed'] == report['summary']['passed'] == 17
    destination.mkdir(exist_ok=True)
    for case in report['cases']:
        name = case['case_id']
        folder = destination / name
        folder.mkdir(exist_ok=True)
        case.pop('command', None)
        case.pop('converter_log_tail', None)
        for original, filename, key in (
            (source / case['output_svg'], 'output.svg', 'output_svg'),
            (source / case['reference_svg'], 'reference.svg', 'reference_svg'),
            (source / name / 'input' / (name + '.png'), 'input.png', 'input_png'),
            (source / name / 'converter.log', 'converter.log', 'converter_log'),
        ):
            shutil.copyfile(original, folder / filename)
            case[key] = (folder / filename).relative_to(destination).as_posix()
        assert symbol_semantics((folder / 'output.svg').read_text(encoding='utf-8'), 'up') == 1
        assert case['blocked_svg_reads'] == []
    report.pop('selection', None)
    save(destination / 'report.json', report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--neutral', type=Path)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--independent', type=Path)
    parser.add_argument('--independent-second', type=Path)
    args = parser.parse_args()
    manifest = read(FOLDER / 'manifest.json')
    for source, destination, catalog in (
        (args.neutral, FOLDER, False),
        (args.catalog, FOLDER / 'catalog_context', True),
    ):
        if source is None:
            continue
        destination.mkdir(exist_ok=True)
        fresh = read(source / 'manifest.json')
        records = fresh if catalog else manifest
        for case, copied, neutral in zip(records['cases'], fresh['cases'], manifest['cases']):
            assert case['source'] == copied['source'] == neutral['source']
            if catalog:
                case['image'] = '../' + neutral['image']
            for mode in ('before', 'after'):
                target = destination / mode / (case['case_id'] + '.svg')
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(source / copied[mode + '_svg'], target)
                case[mode + '_svg'] = target.relative_to(destination).as_posix()
                if catalog and mode == 'after':
                    assert sha(target) == sha(FOLDER / neutral['after_svg'])
        for mode in ('before', 'after'):
            shutil.copyfile(source / (mode + '.log'), destination / (mode + '.log'))
        save(destination / 'manifest.json', records)
        report = evaluate(records, destination)
        report['reference_access'] = read(source / 'report.json')['reference_access']
        assert report['satisfaction_gate']['summary']['satisfactory'] == 9
        save(destination / ('report.json' if catalog else 'acceptance.json'), report)
    for source, name in ((args.independent, 'independent'),
                         (args.independent_second, 'independent_second_seed')):
        if source is not None:
            variations(source, FOLDER / name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
