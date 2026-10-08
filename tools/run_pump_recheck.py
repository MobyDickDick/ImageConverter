"""Reproduce the circle/triangle pump CLI ablation and evaluate its saved SVGs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_pump_recheck import evaluate


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == '--_worker':
        from tools.run_plan_b_variations import converter_worker
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        if sys.argv[2] == 'before':
            from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
            runtime.fit_pump_geometry = lambda *args, **kwargs: None
            runtime.SEMANTIC_GEOMETRY_IR_KINDS.discard('PumpTriangleGlyph')
        elif sys.argv[2].startswith('baseline:'):
            revision = sys.argv[2].split(':', 1)[1]
            if not re.fullmatch(r'[0-9a-f]{40}', revision):
                raise ValueError('baseline fitter revision must be a full commit hash')
            source = subprocess.check_output([
                'git', 'show', revision + ':src/iCCModules/imageCompositeConverterPump.py'
            ], text=True, encoding='utf-8')
            namespace = {'__name__': 'frozen_pump_baseline'}
            exec(compile(source, '<frozen pump baseline>', 'exec'), namespace)
            from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
            runtime.fit_pump_geometry = namespace['fit_pump_geometry']
        random.seed(0)
        np.random.seed(0)
        return converter_worker(sys.argv[3:])

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    output = args.output_dir.resolve()
    if output.exists():
        raise ValueError('Use a fresh output directory: previous CLI artifacts must not seed a recheck')
    inputs = output / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    if not manifest['cases']:
        raise ValueError('At least one case is required')
    names = [case['case_id'] for case in manifest['cases']]
    if len(set(name.casefold() for name in names)) != len(names):
        raise ValueError('case_id must be unique')
    for case in manifest['cases']:
        name = case['case_id']
        if not name or not all(c.isalnum() or c in '_-' for c in name):
            raise ValueError('case_id must be a safe file stem')
        original = (args.manifest.parent / case['image']).resolve()
        if 'source_sha256' in case and hashlib.sha256(original.read_bytes()).hexdigest() != case['source_sha256']:
            raise ValueError(f'Source hash mismatch: {name}')
        target = inputs / (name + original.suffix)
        shutil.copyfile(original, target)
        case['image'] = str(target.relative_to(output))
    environment = dict(os.environ, TINY_ICC_OUTPUT_VARIATION='0', PYTHONHASHSEED='0')
    environment['PYTHONPATH'] = os.pathsep.join(sys.path)
    project = Path(__file__).resolve().parents[1]
    # Preserve the toolchain actually imported by the parent. Repository
    # startup hooks may have added an incompatible historical virtualenv.
    worker_paths = [str(Path(np.__file__).resolve().parents[1]), str(project), *sys.path]
    reference_access = {}
    for mode in ('before', 'after'):
        run_dir = output / mode
        # Each CLI may move inputs into success/nonconvertable directories.
        # Keep immutable measurement inputs and fresh copies for both sides.
        mode_inputs = output / ('inputs_' + mode)
        mode_inputs.mkdir()
        description_root = ET.Element('root')
        for case in manifest['cases']:
            target = mode_inputs / Path(case['image']).name
            shutil.copyfile(output / case['image'], target)
            entry = ET.SubElement(description_root, 'entry', kind='wurzelform', key=case['case_id'])
            description = (manifest['baseline_description'] if mode == 'before' and 'baseline_description' in manifest
                           else case.get('description', manifest['description']))
            ET.SubElement(entry, 'beschreibung').text = description
            ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = target.name
        description_file = mode_inputs / 'descriptions.xml'
        ET.ElementTree(description_root).write(description_file, encoding='utf-8', xml_declaration=True)
        worker_mode = mode
        if mode == 'before' and 'baseline_description' in manifest:
            worker_mode = 'baseline'
            if 'baseline_fitter_revision' in manifest:
                worker_mode += ':' + manifest['baseline_fitter_revision']
        with (output / f'{mode}.log').open('w', encoding='utf-8') as log:
            subprocess.run(
                [sys.executable, '-I', '-c',
                 'import sys, runpy; sys.path[:0] = ' + repr(worker_paths)
                 + "; runpy.run_module('tools.run_pump_recheck', run_name='__main__')",
                 '--_worker', worker_mode,
                 str(run_dir), str(mode_inputs), '--descriptions-path', str(description_file),
                 '--start', min(c['case_id'] for c in manifest['cases']),
                 '--end', max(c['case_id'] for c in manifest['cases']),
                 '--output-dir', str(run_dir), '--execution-mode', 'semantic-only', '--deterministic-order'],
                cwd=project, env=environment, stdout=log, stderr=subprocess.STDOUT,
                timeout=180, check=True,
            )
        blocked = json.loads((output / 'reference_access.json').read_text(encoding='utf-8'))['blocked_svg_reads']
        reference_access[mode] = {'blocked_svg_reads': blocked}
        if blocked:
            raise ValueError('The converter attempted a forbidden reference SVG read')
        for case in manifest['cases']:
            # CLI's historical global threshold may put a good vector into
            # converted_svg_failed. The two independent gates decide quality.
            matches = [p for directory in ('converted_svgs', 'converted_svg_failed')
                       for p in (run_dir / directory).glob('*.svg')
                       if p.stem.casefold() == case['case_id'].casefold()]
            if len(matches) != 1:
                raise ValueError(f'Expected one final CLI SVG: {case["case_id"]}/{mode}')
            case[f'{mode}_svg'] = str(matches[0].relative_to(output))
    report = evaluate(manifest, output)
    report['reference_access'] = reference_access
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report['satisfaction_gate']['summary'], sort_keys=True))
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
