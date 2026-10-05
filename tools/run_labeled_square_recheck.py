"""Reproduce the labeled-square CLI ablation and evaluate its saved SVGs."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_labeled_square_recheck import evaluate


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == '--_worker':
        from src.iCCModules import imageCompositeConverterCli as cli
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        if sys.argv[2] == 'before':
            from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
            runtime.fit_labeled_square = lambda *args, **kwargs: None
            from src.iCCModules.imageCompositeConverterGeometryIr import runtime as geometry
            build = geometry.buildGeometryIrFromDescriptionImpl
            def unlabeled(description):
                ir = build(description)
                for element in ir:
                    if element.get('kind') == 'UprightSquareKelleGlyph':
                        element.pop('label', None)
                return ir
            geometry.buildGeometryIrFromDescriptionImpl = unlabeled
        random.seed(0)
        np.random.seed(0)
        return cli.main(sys.argv[3:])

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    output = args.output_dir.resolve()
    if any((output/mode).exists() for mode in ('before', 'after')):
        raise ValueError('Use a fresh output directory: previous CLI artifacts must not seed a recheck')
    inputs = output / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    description_root = ET.Element('root')
    for case in manifest['cases']:
        name = case['case_id']
        if not name or not all(c.isalnum() or c in '_-' for c in name):
            raise ValueError('case_id must be a safe file stem')
        original = (args.manifest.parent / case['image']).resolve()
        target = inputs / (name + original.suffix)
        shutil.copyfile(original, target)
        entry = ET.SubElement(description_root, 'entry', kind='wurzelform', key=name)
        ET.SubElement(entry, 'beschreibung').text = manifest['description']
        ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = target.name
    description_file = inputs / 'descriptions.xml'
    ET.ElementTree(description_root).write(description_file, encoding='utf-8', xml_declaration=True)
    environment = dict(os.environ, TINY_ICC_OUTPUT_VARIATION='0', PYTHONHASHSEED='0')
    environment['PYTHONPATH'] = os.pathsep.join(sys.path)
    project = Path(__file__).resolve().parents[1]
    # Preserve the toolchain actually imported by the parent. Repository
    # startup hooks may have added an incompatible historical virtualenv.
    worker_paths = [str(Path(np.__file__).resolve().parents[1]), str(project), *sys.path]
    for mode in ('before', 'after'):
        run_dir = output / mode
        with (output / f'{mode}.log').open('w', encoding='utf-8') as log:
            subprocess.run(
                [sys.executable, '-I', '-c',
                 'import sys, runpy; sys.path[:0] = ' + repr(worker_paths)
                 + "; runpy.run_module('tools.run_labeled_square_recheck', run_name='__main__')",
                 '--_worker', mode,
                 str(inputs), '--descriptions-path', str(description_file),
                 '--output-dir', str(run_dir), '--execution-mode', 'semantic-only', '--deterministic-order'],
                cwd=project, env=environment, stdout=log, stderr=subprocess.STDOUT,
                timeout=180, check=True,
            )
        for case in manifest['cases']:
            # CLI's historical global threshold may put a good vector into
            # converted_svg_failed. The two independent gates decide quality.
            matches = [p for directory in ('converted_svgs', 'converted_svg_failed')
                       for p in (run_dir / directory).glob('*.svg')
                       if p.stem.casefold() == case['case_id'].casefold()]
            if len(matches) != 1:
                raise ValueError(f'Expected one final CLI SVG: {case["case_id"]}/{mode}')
            case[f'{mode}_svg'] = str(matches[0].relative_to(output))
    for case in manifest['cases']:
        case['image'] = str((args.manifest.parent / case['image']).resolve())
    report = evaluate(manifest, output)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report['satisfaction_gate']['summary'], sort_keys=True))
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
