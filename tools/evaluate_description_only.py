"""Run isolated fresh CLI probes; retain every output, command and diagnosis."""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def evaluate(output):
    from src.imageConverterGui import catalog_descriptions
    from src.imageConverterSample import render_svg
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
    output.mkdir(parents=True, exist_ok=True)
    circle = ('<svg xmlns="http://www.w3.org/2000/svg" width="80" height="64">'
              '<circle cx="37" cy="29" r="20" fill="#bbbbbb" stroke="#666666" stroke-width="2"/></svg>')
    cases = [
        ('independent_circle', Image.fromarray(render_svg(circle,80,64)), 'Ein grauer Kreis mit dunklem Rand.'),
        ('supported_circle', Image.fromarray(render_svg(circle,80,64)), 'Ein grauer Kreis mit dunkelgrauem Rand.'),
        ('reported_source_current_description', Image.open(ROOT/'artifacts/images_to_convert/AC0201_M.jpg').convert('RGB'),
         catalog_descriptions()['AC0201_M']),
        ('reported_source_explicit_inventory', Image.open(ROOT/'artifacts/images_to_convert/AC0201_M.jpg').convert('RGB'),
         'Ein grauer Kreis, eine senkrechte Linie und zwei graue Dreiecke. Der Kreis liegt oben. Die Dreiecke liegen darunter links und rechts.'),
    ]
    records = []
    for name, image, description in cases:
        for seed in (17, 18):
            folder = output/f'{name}_seed_{seed}'
            inputs, results = folder/'input', folder/'output'
            inputs.mkdir(parents=True, exist_ok=True)
            image.save(inputs/'neutral.png')
            table = folder/'description.csv'
            with table.open('w',encoding='utf-8',newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['Wurzelform','Beschreibung'])
                writer.writerow(['NEUTRAL',description])
            command = [sys.executable,'-u','-m','src.imageCompositeConverter',str(inputs.resolve()),
                '--descriptions-path',str(table.resolve()),'--output-dir',str(results.resolve()),
                '--start','neutral','--end','neutral','--execution-mode','semantic-only',
                '--search-seconds','2','--search-max-seconds','3','--search-min-seconds','0',
                '--search-seed',str(seed),'--fail-on-batch-failures',
                '--log-file',str((folder/'converter.log').resolve())]
            environment = dict(os.environ, PYTHONIOENCODING='utf-8', ICC_MAX_QUALITY_PASSES='0',
                IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_CONVERSION_TIMEOUT_SEC='10')
            try:
                completed = subprocess.run(command,cwd=ROOT,env=environment,stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,timeout=30)
                console = completed.stdout.decode('utf-8', errors='replace')
                (folder/'console.log').write_text(console,encoding='utf-8')
                row = dict(case=name, seed=seed, description=description, command=command,
                    returncode=completed.returncode, svgs=[],
                    second_stage_events=console.count('native_svg_search')+console.count('elementweise iterative Annäherung'))
                for svg in results.rglob('*.svg'):
                    error = ''
                    try:
                        validate_svg_assertions(svg.read_text(encoding='utf-8'),description_assertions(description))
                    except ValueError as exc:
                        error = str(exc)
                    row['svgs'].append(dict(path=str(svg.resolve()), inventory_error=error))
            except subprocess.TimeoutExpired:
                row = dict(case=name,seed=seed,error='probe_timeout')
            records.append(row)
            print(json.dumps({k:v for k,v in row.items() if k != 'command'},ensure_ascii=False),flush=True)
    (output/'results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    evaluate(parser.parse_args().output)
