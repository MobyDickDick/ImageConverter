"""Append the accepted catalog pair while proving prior records/files unchanged."""
from pathlib import Path
import json
import shutil
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_labeled_square_recheck import evaluate
from tools.run_plan_b_variations import measure_quality
from seal_evidence import read, save, sha
import cv2


def main():
    if (FOLDER/'archive_safety.json').exists():
        raise ValueError('Already archived; verify instead of replacing the preservation proof')
    manifest = read(FOLDER/'manifest.json')
    report = evaluate(manifest, FOLDER)
    assert all(c['satisfactory'] for c in report['satisfaction_gate']['cases'])
    assert read(FOLDER/'independent/report.json')['summary']['satisfactory']
    assert read(FOLDER/'independent_second_seed/report.json')['summary']['satisfactory']
    archive = ROOT/'artifacts/satisfactory_conversions'
    index = read(archive/'index.json')
    previous = {c['variant']:c for c in index['cases']}
    for case in previous.values():
        for field in ('image', 'svg'):
            assert sha(archive/case[field]) == case[field+'_sha256']
    for case, evidence, accepted in zip(manifest['cases'], report['evidence'], report['satisfaction_gate']['cases']):
        variant = Path(case['source']).stem
        assert variant not in previous
        image, svg = FOLDER/case['image'], FOLDER/case['after_svg']
        assert measure_quality(cv2.imread(str(image)), svg.read_text(encoding='utf-8'))['satisfactory']
        shutil.copyfile(image, archive/'images'/image.name)
        shutil.copyfile(svg, archive/'svgs'/(variant+'.svg'))
        index['cases'].append(dict(variant=variant, description=case['description'], execution_mode='semantic-only',
            evidence='artifacts/evaluation/left_stem_labeled_square_recheck_v1/acceptance.json',
            mean_delta2=evidence['after_mean_delta2'],
            metrics={k:v for k,v in accepted['after'].items() if k != 'semantic_score'},
            image='images/'+image.name, svg='svgs/'+variant+'.svg',
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
             f"{index['case_count']} geprüfte Bild-/SVG-Paare. Originalbilder liegen in `images/`, Vektoren in `svgs/`.", '',
             'Die erweiterten Tests konvertieren alle Einträge aus `index.json` erneut aus Bild und Beschreibung.', '',
             '| Bild | SVG | Mean-Delta² | Prüfung |', '|---|---|---:|---|']
    lines += [f"| [{c['variant']}]({c['image']}) | [SVG]({c['svg']}) | {c['mean_delta2']:.6f} | {c['execution_mode']} |"
              for c in index['cases']]
    (archive/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    # Same canonical record hash convention as the previous archive packages.
    import hashlib
    save(FOLDER/'archive_safety.json', dict(previous_count=len(previous), new_count=index['case_count'],
        previous_record_hashes={key:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
                                for key,value in previous.items()}, all_previous_records_unchanged=True))
    print(index['case_count'], 'pairs; all previous records and original images/vectors unchanged')


if __name__ == '__main__':
    main()
