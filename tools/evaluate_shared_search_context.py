"""Exercise real shared-context entry points without publishing catalog results."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SEED = 2**64-1
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 50 50">'
       '<circle cx="25" cy="25" r="15" fill="#aaaaaa" stroke="#555555" stroke-width="1"/></svg>')
DESCRIPTION = 'Grauer Kreis mit grauem Rand und hellgrauem Hintergrund'


def journal(path):
    events = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    finished = [e for e in events if e.get('event') == 'image_search_context_finished']
    renders = [e for e in events if e.get('event') == 'candidate_rendered']
    for event in finished:
        actual = [r for r in renders if r['source'] == event['source']]
        assert len(actual) == event['renderings'] <= event['render_budget']
        assert event['search_seed'] == str(SEED)
    assert finished and renders
    return [dict(source=e['source'], renderings=e['renderings'], render_budget=e['render_budget'],
                 seed=e['search_seed'], stop_reason=e['stop_reason'], satisfactory=e['satisfactory'],
                 sequence=e['render_sequence_sha256']) for e in finished]


def evaluate(work):
    from src import imageConverterGui as gui
    from src.imageConverterSample import render_svg
    from src.imageConverterComponents import convert as convert_components
    from src.iCCModules import imageCompositeConverterSvgComponents as components
    from tools import plan_b_workbench as wb

    work.mkdir(parents=True, exist_ok=False)
    target = Image.new('RGB', (50, 50), 'white')
    ImageDraw.Draw(target).ellipse((10, 10, 39, 39), fill='#aaaaaa', outline='#555555', width=1)
    source = work/'source.png'
    target.save(source)
    result = {}

    inputs = work/'batch-input'
    inputs.mkdir()
    target.save(inputs/'AA0010.png')
    impossible = Image.new('RGB', (50, 50), 'white')
    draw = ImageDraw.Draw(impossible)
    for x, y in ((5, 5), (35, 5), (5, 35), (35, 35)):
        draw.ellipse((x, y, x+9, y+9), fill='#555555')
    impossible.save(inputs/'AA0020.png')
    table = work/'descriptions.csv'
    table.write_text('Wurzelform,Beschreibung\nAA0010,'+DESCRIPTION+'\nAA0020,Ein Rechteck.\n', encoding='utf-8')
    command = [sys.executable, '-m', 'src.imageCompositeConverter', str(inputs),
        '--descriptions-path', str(table), '--output-dir', str(work/'batch'),
        '--start', 'AA0010', '--end', 'AA0020', '--search-seed', str(SEED), '--search-budget', '32',
        '--search-seconds', '10', '--search-max-seconds', '10', '--search-min-seconds', '0',
        '--no-isolate-conversion', '--log-file', str(work/'batch.log')]
    with (work/'batch-console.log').open('wb') as log:
        completed = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, PYTHONIOENCODING='utf-8', IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0'), timeout=40)
    result['cli_batch'] = dict(returncode=completed.returncode, contexts=journal(work/'batch/search/progress.jsonl'))
    assert len(result['cli_batch']['contexts']) == 2

    jobs = gui.Jobs(work/'jobs')
    jobs.project_directory = work/'project'
    try:
        with patch.object(gui, 'catalog_descriptions', return_value={}):
            for name, sample in (('fresh_gui', False), ('template_worker', True), ('catalog_background', False)):
                buffer = io.BytesIO()
                (Image.fromarray(render_svg(SVG, 50, 50)) if sample else target).save(buffer, format='PNG')
                upload = jobs.upload('neutral.png', buffer.getvalue())
                if sample:
                    jobs.attach_sample(upload['id'], 'sample.svg', SVG.encode())
                started = jobs.start(upload['id'], DESCRIPTION, 'quick', seed=str(SEED),
                                     background=name == 'catalog_background', use_current_svg=sample)
                jobs.threads[-1].join(timeout=55)
                job = jobs.snapshot(started['id'])
                assert job['status'] in {'done', 'error'}, job
                output = jobs.folder(started['id'])/'output'
                result[name] = dict(status=job['status'], quality=job.get('quality'),
                    contexts=journal(output/'search/progress.jsonl'))
    finally:
        jobs.close()

    library = work/'artifacts/converted_images/converted_svgs'
    library.mkdir(parents=True)
    (library/'donor.svg').write_text(SVG, encoding='utf-8')
    component_source = work/'component-source.png'
    Image.fromarray(components.render_components(SVG, 50, 50)).save(component_source)
    with patch.object(components, 'ROOT', work):
        report = convert_components(component_source, work/'components/result.svg',
            'SVG-Bauteil: donor.svg bei 0 0 skaliert 1', 10., seed=SEED)
    result['component_worker'] = dict(passed=report['passed'], context=report['search_context'])
    assert 0 < report['search_context']['renderings'] <= report['search_context']['render_budget']
    assert report['passed']

    prepared = wb.prepare(SVG, DESCRIPTION, work/'workbench', seed=SEED)
    executed = wb.execute(work/'workbench', [prepared['cases'][0]['case_id']], iterations=1, timeout=25.)
    paths = list((work/'workbench').glob('attempts/*/*/conversion/search/progress.jsonl'))
    assert len(paths) == 1
    result['workbench_plan_b'] = dict(status=executed['status'], contexts=journal(paths[0]))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    work = args.output.resolve()
    results = evaluate(work)
    (work/'summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
