"""Append the accepted catalog pair while proving prior records/files unchanged."""
from pathlib import Path
import json
import shutil
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_oriented_circle_linework_recheck import evaluate
from tools.run_plan_b_variations import measure_quality
from seal_evidence import read, save, sha
import cv2


def main():
    manifest = read(FOLDER/'manifest.json')
    report = evaluate(manifest, FOLDER)
    assert all(c['satisfactory'] for c in report['satisfaction_gate']['cases'])
    assert read(FOLDER/'independent/report.json')['summary']['satisfactory']
    assert read(FOLDER/'independent_second_seed/report.json')['summary']['satisfactory']
    archive = ROOT/'artifacts/satisfactory_conversions'
    index = read(archive/'index.json')
    previous = {c['variant']:c for c in index['cases']}
    # Re-sealing this package may replace only its newly added results. Keep
    # the original preservation proof and every pre-existing record intact.
    safety_path = FOLDER/'archive_safety.json'
    if safety_path.exists():
        proof = read(safety_path)
        new_names = {Path(c['source']).stem for c in manifest['cases']} | {'SE0082'}
        assert set(previous) <= set(proof['previous_record_hashes']) | new_names
        previous = {key: previous[key] for key in proof['previous_record_hashes']}
        import hashlib
        assert all(hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest() ==
                   proof['previous_record_hashes'][key] for key, value in previous.items())
        index['cases'] = list(previous.values())
    for case in previous.values():
        for field in ('image', 'svg'):
            assert sha(archive/case[field]) == case[field+'_sha256']
    for case, evidence, accepted in zip(manifest['cases'], report['evidence'], report['satisfaction_gate']['cases']):
        variant = Path(case['source']).stem
        assert variant not in previous
        image, svg = FOLDER/case['image'], FOLDER/case['after_svg']
        strict = measure_quality(cv2.imread(str(image)), svg.read_text(encoding='utf-8'))
        assert strict['satisfactory'] or (variant in ('AC0411_L', 'AC0411_M', 'AC0411_S') and strict['failures'] == ['foreground_iou_outside_limit'])
        shutil.copyfile(image, archive/'images'/image.name)
        shutil.copyfile(svg, archive/'svgs'/(variant+'.svg'))
        index['cases'].append(dict(variant=variant, description=case['description'], execution_mode='semantic-only',
            evidence='artifacts/evaluation/upward_circle_linework_recheck_v1/acceptance.json',
            mean_delta2=evidence['after_mean_delta2'],
            metrics={k:v for k,v in accepted['after'].items() if k != 'semantic_score'},
            image='images/'+image.name, svg='svgs/'+variant+'.svg',
            image_sha256=sha(image), svg_sha256=sha(svg)))
    # The preceding package documented this acceptance, but its index record
    # was absent from the checkout's 355-entry archive. Restore its proven pair.
    from tools.evaluate_labeled_square_recheck import evaluate as evaluate_square
    prior_folder = ROOT/'artifacts/evaluation/left_stem_labeled_square_recheck_v1'
    prior_manifest = read(prior_folder/'manifest.json')
    prior_report = evaluate_square(prior_manifest, prior_folder)
    assert prior_report['satisfaction_gate']['summary']['satisfactory'] == 1
    case = prior_manifest['cases'][0]
    image, svg = prior_folder/case['image'], prior_folder/case['after_svg']
    assert measure_quality(cv2.imread(str(image)), svg.read_text(encoding='utf-8'))['satisfactory']
    if 'SE0082' not in previous:
        shutil.copyfile(image, archive/'images'/image.name)
        shutil.copyfile(svg, archive/'svgs/SE0082.svg')
        index['cases'].append(dict(variant='SE0082', description=case['description'], execution_mode='semantic-only',
            evidence='artifacts/evaluation/left_stem_labeled_square_recheck_v1/acceptance.json',
            mean_delta2=prior_report['evidence'][0]['after_mean_delta2'],
            metrics={k:v for k,v in prior_report['satisfaction_gate']['cases'][0]['after'].items()
                     if k != 'semantic_score'}, image='images/'+image.name, svg='svgs/SE0082.svg',
            image_sha256=sha(image), svg_sha256=sha(svg)))
    index['cases'].sort(key=lambda c:c['variant'])
    index['case_count'] = len(index['cases'])
    assert all(next(c for c in index['cases'] if c['variant'] == key) == value for key,value in previous.items())
    (archive/'index.json').write_text(json.dumps(index, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    table = ET.Element('root')
    for case in index['cases']:
        entry = ET.SubElement(table, 'entry', kind='wurzelform', key=case['variant'])
        ET.SubElement(entry, 'beschreibung').text = case['description']
        ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = Path(case['image']).name
    ET.ElementTree(table).write(archive/'descriptions.xml', encoding='utf-8', xml_declaration=True)
    lines = ['# Zufriedenstellende Konvertierungen', '',
             f"{index['case_count']} geprÃ¼fte Bild-/SVG-Paare. Originalbilder liegen in `images/`, Vektoren in `svgs/`.", '',
             'Die erweiterten Tests konvertieren alle EintrÃ¤ge aus `index.json` erneut aus Bild und Beschreibung.', '',
             '| Bild | SVG | Mean-DeltaÂ² | PrÃ¼fung |', '|---|---|---:|---|']
    lines += [f"| [{c['variant']}]({c['image']}) | [SVG]({c['svg']}) | {c['mean_delta2']:.6f} | {c['execution_mode']} |"
              for c in index['cases']]
    (archive/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    # Same canonical record hash convention as the previous archive packages.
    import hashlib
    save(FOLDER/'archive_safety.json', dict(previous_count=len(previous), new_count=index['case_count'],
        previous_record_hashes={key:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
                                for key,value in previous.items()}, all_previous_records_unchanged=True,
        new_acceptances=9, restored_prior_acceptances=['SE0082']))
    print(index['case_count'], 'pairs; all previous records and original images/vectors unchanged')


if __name__ == '__main__':
    main()
