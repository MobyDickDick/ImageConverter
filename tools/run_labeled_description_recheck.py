"""Compare fresh original-description and revised-description labeled-square CLI runs."""
from __future__ import annotations

import argparse
import hashlib
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
        from tools.run_plan_b_variations import converter_worker
        random.seed(0)
        np.random.seed(0)
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        return converter_worker(sys.argv[2:])

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--baseline-only', action='store_true')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise ValueError('Use a fresh output directory')
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    inputs = output / 'inputs'
    inputs.mkdir(parents=True)
    names = []
    for case in manifest['cases']:
        name = case['case_id']
        if not name or not all(c.isalnum() or c in '_-' for c in name) or name in names:
            raise ValueError('case_id must be a unique safe file stem')
        names.append(name)
        original = (args.manifest.parent / case['image']).resolve()
        if hashlib.sha256(original.read_bytes()).hexdigest() != case['source_sha256']:
            raise ValueError(f'Source hash mismatch: {name}')
        target = inputs / (name + original.suffix)
        shutil.copyfile(original, target)
        case['image'] = str(target.relative_to(output))

    project = Path(__file__).resolve().parents[1]
    paths = [str(Path(np.__file__).resolve().parents[1]), str(project), *sys.path]
    env = dict(os.environ, TINY_ICC_OUTPUT_VARIATION='0', PYTHONHASHSEED='0',
               IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_FORCE_RECONVERT='1')
    reference_access = {}
    for mode in (('before',) if args.baseline_only else ('before', 'after')):
        mode_inputs = output / ('inputs_' + mode)
        mode_inputs.mkdir()
        table = ET.Element('root')
        for case in manifest['cases']:
            source = output / case['image']
            shutil.copyfile(source, mode_inputs / source.name)
            entry = ET.SubElement(table, 'entry', kind='wurzelform', key=case['case_id'])
            ET.SubElement(entry, 'beschreibung').text = (
                case['baseline_description'] if mode == 'before' else manifest['description']
            )
            ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = source.name
        descriptions = mode_inputs / 'descriptions.xml'
        ET.ElementTree(table).write(descriptions, encoding='utf-8', xml_declaration=True)
        run_dir = output / mode
        with (output / (mode + '.log')).open('w', encoding='utf-8') as log:
            subprocess.run([
                sys.executable, '-I', '-c', 'import sys,runpy; sys.path[:0]=' + repr(paths)
                + "; runpy.run_module('tools.run_labeled_description_recheck',run_name='__main__')",
                '--_worker', str(run_dir), str(mode_inputs), '--descriptions-path', str(descriptions),
                '--output-dir', str(run_dir), '--start', min(names), '--end', max(names),
                '--execution-mode', 'semantic-only', '--deterministic-order',
            ], cwd=project, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180, check=True)
        blocked = json.loads((output / 'reference_access.json').read_text(encoding='utf-8'))['blocked_svg_reads']
        reference_access[mode] = {'blocked_svg_reads': blocked}
        if blocked:
            raise ValueError('Forbidden reference SVG access')
        for case in manifest['cases']:
            matches = [p for folder in ('converted_svgs', 'converted_svg_failed')
                       for p in (run_dir / folder).glob('*.svg')
                       if p.stem.casefold() == case['case_id'].casefold()]
            if len(matches) != 1:
                raise ValueError(f"Expected one saved CLI SVG: {case['case_id']}/{mode}")
            case[mode + '_svg'] = str(matches[0].relative_to(output))
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    if args.baseline_only:
        print('Fresh original-description CLI baseline saved')
        return 0
    report = evaluate(manifest, output)
    report['reference_access'] = reference_access
    (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(report['satisfaction_gate']['summary'], sort_keys=True))
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
