"""Compare production CLI outputs and recover a real fit after blocked finalization."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked_final_render(connection, payload):
    """Fault injection: block the next render after a genuinely checked model."""
    from src import imageCompositeConverter as app
    from src.iCCModules.imageCompositeConverterDeadline import conversion_worker
    render = app.Action.renderSvgToNumpy
    checked = False

    class Channel:
        def send(self, message):
            nonlocal checked
            connection.send(message)
            if message[0] == 'checkpoint':
                checked = True

    def render_or_block(*args, **kwargs):
        if checked:
            time.sleep(60)
        return render(*args, **kwargs)

    app.Action.renderSvgToNumpy = staticmethod(render_or_block)
    conversion_worker(Channel(), payload)


def verify(output):
    import cv2
    from tools.run_plan_b_variations import measure_quality, render
    from tools.evaluate_primitive_scene import check_objects
    from tools.evaluate_motor_valve_recheck import symbol_semantics as motor_semantics
    from tools.evaluate_labeled_disk_recheck import symbol_semantics as letter_semantics
    from tools.evaluate_short_label_search import symbol_semantics as label_semantics

    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    for case in report['cases']:
        assert digest(output/case['image']) == case['input_sha256']
        image = cv2.imread(str(output/case['image']))
        for mode in ('direct', 'supervised'):
            record = case[mode]
            path = output/record['svg']
            assert digest(path) == record['svg_sha256']
            svg = path.read_text(encoding='utf-8')
            quality = measure_quality(image, svg)
            assert quality['satisfactory'], (case['case_id'], mode, quality)
            semantic = (motor_semantics(svg) if case['kind'] == 'motor' else
                        letter_semantics(svg, 'Q', bottom_stem=True) if case['kind'] == 'letter' else
                        label_semantics(svg, case['label']) if case['kind'] == 'label' else
                        float(check_objects(render(svg, image.shape[1], image.shape[0]), case['expected_objects'])['passed']))
            assert semantic == 1., (case['case_id'], semantic)
        assert case['direct']['svg_sha256'] == case['supervised']['svg_sha256']
    recovery = report['recovery']
    svg = (output/recovery['svg']).read_text(encoding='utf-8')
    source = cv2.imread(str(output/report['cases'][1]['image']))
    assert measure_quality(source, svg)['satisfactory'] and motor_semantics(svg) == 1.
    assert recovery['row']['search_control']['stop_reason'] == 'time_limit'
    assert recovery['row']['search_satisfactory'] and not recovery['failures']
    return dict(cases=len(report['cases']), byte_identical=True, strict_pixels_and_semantics=True,
                actual_blocked_final_render_recovered=True)


def run(output):
    import cv2
    from tools.run_plan_b_variations import render, measure_quality
    from tools.evaluate_primitive_scene import make_cases
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import SearchPolicy
    from src.iCCModules.imageCompositeConverterDeadline import ImageDeadline
    from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, settings

    output.mkdir(parents=True)
    sources = output/'sources'
    sources.mkdir()
    table = ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml')
    cases = []
    for variant, kind, label in [('AC0232_L', 'motor', 'M'), ('AC0232_M', 'motor', 'M'),
                                 ('AC0232_S', 'motor', 'M'), ('AC0921_M', 'letter', 'Q'),
                                 ('AC0840_M', 'label', 'rF'), ('AC0910_S', 'label', 'Lux')]:
        source = ROOT/'artifacts/images_to_convert'/(variant+'.jpg')
        entry = next(e for e in table.iter('entry') if source.name in [p.text for p in e.findall('bilder/bild')])
        name = f'neutral_{len(cases):02}'
        image = sources/(name+'.jpg')
        shutil.copyfile(source, image)
        cases.append(dict(case_id=name, image=image.relative_to(output).as_posix(), input_sha256=digest(image),
                          kind=kind, label=label, description=entry.findtext('beschreibung')))
    for case in make_cases(43123, 9)[-2:]:
        name = f'neutral_{len(cases):02}'
        image = sources/(name+'.png')
        cv2.imwrite(str(image), render(case['svg'], case['width'], case['height']))
        cases.append(dict(case_id=name, image=image.relative_to(output).as_posix(), input_sha256=digest(image),
                          kind='primitives', expected_objects=case['expected_objects'], description=case['description']))
    catalog = ET.Element('root')
    for case in cases:
        entry = ET.SubElement(catalog, 'entry', key=case['case_id'], kind='wurzelform')
        ET.SubElement(entry, 'beschreibung').text = case['description']
        ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = Path(case['image']).name
    descriptions = output/'descriptions.xml'
    ET.ElementTree(catalog).write(descriptions, encoding='utf-8', xml_declaration=True)
    env = dict(os.environ, IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', TINY_ICC_OUTPUT_VARIATION='0',
               PYTHONHASHSEED='0', PYTHONIOENCODING='utf-8')
    for mode in ('direct', 'supervised'):
        conversion = output/mode
        command = [sys.executable, '-m', 'tools.run_labeled_disk_recheck', '--_worker', mode, str(conversion), str(sources),
                   '--descriptions-path', str(descriptions), '--output-dir', str(conversion), '--start', cases[0]['case_id'],
                   '--end', cases[-1]['case_id'], '--execution-mode', 'semantic-only', '--deterministic-order',
                   '--search-seed', '20261018']
        if mode == 'direct':
            command.append('--no-isolate-conversion')
        with (output/(mode+'.log')).open('w', encoding='utf-8') as log:
            subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=360)
        rows = json.loads((conversion/'reports/conversion_result_map.json').read_text(encoding='utf-8'))
        access = json.loads((output/'reference_access.json').read_text(encoding='utf-8'))
        assert not access['blocked_svg_reads']
        for case in cases:
            path = conversion/'converted_svgs'/(case['case_id']+'.svg')
            row = rows[Path(case['image']).name]
            assert not row.get('reference_access', {}).get('blocked_svg_reads')
            quality = measure_quality(cv2.imread(str(output/case['image'])), path.read_text(encoding='utf-8'))
            case[mode] = dict(svg=path.relative_to(output).as_posix(), svg_sha256=digest(path),
                              quality=quality, elapsed_seconds=row['elapsed_seconds'], search_control=row.get('search_control'))
        print(mode, 'completed', flush=True)
    recovery_dir = output/'recovery'
    spec = dict(filename=Path(cases[1]['image']).name, folder_path=str(sources), csv_path=str(descriptions),
                iteration_budget=64, badge_rounds=8, debug_ac0811_dir=None, debug_element_diff_dir=None)
    for key in ('svg_out_dir', 'diff_out_dir', 'png_out_dir', 'reports_out_dir'):
        spec[key] = str(recovery_dir/key)
        Path(spec[key]).mkdir(parents=True)
    events = []
    with search_configuration(mode='portfolio', seed=20261018, adaptive=True, directory=recovery_dir/'search', seconds=4., max_seconds=4.):
        deadline = ImageDeadline(SearchPolicy(seconds=4., max_seconds=4.), emit=lambda **v: events.append(v))
        (row, failed), failures = deadline.run(spec, config=settings(), action={}, worker=blocked_final_render)
    assert not failed and row and row['search_satisfactory'], failures
    report = dict(cases=cases, recovery=dict(row=row, failures=failures, events=events,
                  svg=(Path(spec['svg_out_dir'])/(cases[1]['case_id']+'.svg')).relative_to(output).as_posix()))
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(verify(output))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if args.verify_only:
        print(verify(output))
    else:
        run(output)


if __name__ == '__main__':
    main()
