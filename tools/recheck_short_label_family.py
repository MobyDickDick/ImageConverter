"""Replay a disk-label family under neutral filenames and independent SVG rendering."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import cv2

from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
from tools.evaluate_svg_text_baseline import render_librsvg
from tools.evaluate_short_label_search import symbol_semantics
from tools.run_catalog_conversion import conversion_environment
from tools.run_plan_b_variations import measure_quality


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', required=True)
    parser.add_argument('--input-dir', type=Path, default=Path('artifacts/images_to_convert'))
    parser.add_argument('--descriptions', type=Path, default=Path('artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'))
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--seed', type=int, action='append')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    mapping = loadDescriptionMappingImpl(str(args.descriptions), get_base_name_from_file_fn=getBaseNameFromFileImpl)
    inputs = output / 'inputs'
    inputs.mkdir()
    cases = []
    for size in ('L', 'M', 'S'):
        original = args.input_dir / f'{args.family}_{size}.jpg'
        neutral = f'PROBE_{size}'
        target = inputs / f'{neutral}.jpg'
        shutil.copyfile(original, target)
        cases.append(dict(variant=original.stem, neutral=neutral,
                          source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                          description=mapping.get(original.stem) or mapping[args.family]))
    table = output / 'descriptions.csv'
    with table.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Wurzelform', 'Beschreibung'])
        writer.writerows((case['neutral'], case['description']) for case in cases)
    records = []
    env = conversion_environment()
    env['ICC_MAX_QUALITY_PASSES'] = '0'
    for index, seed in enumerate(args.seed or [42, 314159]):
        run = output / f'run-{index}-{seed}'
        command = [sys.executable, '-m', 'src.imageCompositeConverter', str(inputs),
                   '--descriptions-path', str(table), '--output-dir', str(run),
                   '--start', 'PROBE_L', '--end', 'PROBE_S', '--execution-mode', 'semantic-only',
                   '--deterministic-order', '--search-seed', str(seed), '--fail-on-batch-failures',
                   '--log-file', str(output / f'run-{index}.local.log')]
        with (output / f'run-{index}.log').open('w', encoding='utf-8') as log:
            result = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=env,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=420, check=False)
        for case in cases:
            path = run / 'converted_svgs' / f"{case['neutral']}.svg"
            record = dict(variant=case['variant'], seed=seed, run=index, cli_exit=result.returncode,
                          source_sha256=case['source_sha256'], svg=str(path.relative_to(output)))
            if path.is_file():
                svg = path.read_text(encoding='utf-8')
                image = cv2.imread(str(inputs / f"{case['neutral']}.jpg"))
                labels = re.findall(r'["„]([A-Za-z0-9]{2,4})["“]', case['description'])
                semantics = len(labels) == 1 and symbol_semantics(svg, labels[0]) == 1
                audit = run/'reports'/f"{case['neutral']}_reference_access.json"
                blocked = json.loads(audit.read_text(encoding='utf-8'))['blocked_svg_reads']
                record.update(svg_sha256=hashlib.sha256(svg.encode()).hexdigest(),
                              semantics=semantics, blocked_svg_reads=blocked,
                              internal=measure_quality(image, svg),
                              independent=measure_quality(image, svg, render_fn=render_librsvg))
            records.append(record)
        print(f"seed={seed} cli_exit={result.returncode}", flush=True)
    passed = all(r.get('internal', {}).get('satisfactory') and
                 r.get('independent', {}).get('satisfactory') and r.get('semantics')
                 and not r.get('blocked_svg_reads') and r['cli_exit'] == 0 for r in records)
    summary = dict(family=args.family, cases=cases, records=records, passed=passed,
                   scope='Fresh semantic-only CLI, neutral filenames, original descriptions; MuPDF and librsvg pixel gates')
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f'passed={passed} outputs={len(records)}', flush=True)
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
