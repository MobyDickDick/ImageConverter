"""Replay the original-description baseline and the observed zigzag-panel CLI."""
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

from tools.evaluate_zigzag_panel_recheck import evaluate


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == '--_worker':
        from tools.run_plan_b_variations import converter_worker
        from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
        if sys.argv[2] == 'before':
            runtime.fit_zigzag_panel = lambda *args, **kwargs: None
        random.seed(0)
        np.random.seed(0)
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        return converter_worker(sys.argv[3:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise ValueError('Use a fresh output directory: previous CLI artifacts must not seed a recheck')
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    inputs = output/'inputs'
    inputs.mkdir(parents=True)
    for case in manifest['cases']:
        name = case['case_id']
        if not name or not all(c.isalnum() or c in '_-' for c in name):
            raise ValueError('case_id must be a safe file stem')
        original = (args.manifest.parent/case['image']).resolve()
        if hashlib.sha256(original.read_bytes()).hexdigest() != case['source_sha256']:
            raise ValueError(f"Source hash mismatch: {name}")
        target = inputs/(name+original.suffix)
        shutil.copyfile(original, target)
        case['image'] = str(target.relative_to(output))
    paths = [str(Path(np.__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1]), *sys.path]
    env = dict(os.environ, TINY_ICC_OUTPUT_VARIATION='0', PYTHONHASHSEED='0', IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0')
    for mode in ('before', 'after'):
        # A failed CLI case can archive its input under nonconvertable. Each
        # side receives its own fresh copy; neither can change the other's set.
        mode_inputs = output/('inputs_'+mode)
        mode_inputs.mkdir()
        table = ET.Element('root')
        for case in manifest['cases']:
            shutil.copyfile(output/case['image'], mode_inputs/Path(case['image']).name)
            entry = ET.SubElement(table, 'entry', kind='wurzelform', key=case['case_id'])
            ET.SubElement(entry, 'beschreibung').text = manifest['baseline_description'] if mode == 'before' else manifest['description']
            ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = Path(case['image']).name
        description_file = mode_inputs/(mode+'.xml')
        ET.ElementTree(table).write(description_file, encoding='utf-8', xml_declaration=True)
        run_dir = output/mode
        names = sorted(case['case_id'] for case in manifest['cases'])
        with (output/(mode+'.log')).open('w', encoding='utf-8') as log:
            subprocess.run([sys.executable, '-I', '-c', 'import sys,runpy; sys.path[:0]='+repr(paths)+
                            "; runpy.run_module('tools.run_zigzag_panel_recheck',run_name='__main__')",
                            '--_worker', mode, str(run_dir), str(mode_inputs), '--descriptions-path', str(description_file),
                            '--output-dir', str(run_dir), '--start', names[0], '--end', names[-1],
                            '--execution-mode', 'semantic-only', '--deterministic-order'],
                           cwd=Path(__file__).resolve().parents[1], env=env, stdout=log, stderr=subprocess.STDOUT,
                           timeout=180, check=True)
        blocked = json.loads((output/'reference_access.json').read_text(encoding='utf-8'))['blocked_svg_reads']
        if blocked:
            raise ValueError('The converter attempted a forbidden reference SVG read')
        for case in manifest['cases']:
            matches = [p for directory in ('converted_svgs', 'converted_svg_failed')
                       for p in (run_dir/directory).glob('*.svg') if p.stem.casefold() == case['case_id'].casefold()]
            if len(matches) != 1:
                raise ValueError(f"Expected one saved CLI SVG: {case['case_id']}/{mode}")
            case[mode+'_svg'] = str(matches[0].relative_to(output))
    report = evaluate(manifest, output)
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    (output/'report.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report['satisfaction_gate']['summary'], sort_keys=True))
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
