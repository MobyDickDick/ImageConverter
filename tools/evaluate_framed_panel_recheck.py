"""Replay frozen Workbench PNGs through the real CLI and independent SVG gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import cv2
import numpy as np

from tools import run_plan_b_variations as battery
from tools.plan_b_workbench import provenance
from src.iCCModules.imageCompositeConverterFramedPanel import profile_quality


def run(archive: Path, output: Path, names: list[str] | None = None, description: str | None = None) -> dict:
    allowed = ['original', *[f'probe_{i:02d}' for i in range(1, 17)]]
    if names is not None and (not names or len(set(names)) != len(names) or set(names)-set(allowed)):
        raise ValueError('Expected distinct original/probe_01..probe_16 cases')
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with ZipFile(archive) as source:
        report = json.loads(source.read('report.json'))
        if report.get('schema_version') != 'plan_b_workbench_v1':
            raise ValueError('Expected a Workbench export')
        cases = {case['case_id']: case for case in report['cases']}
        if set(cases) != set(allowed):
            raise ValueError('Expected exactly the original and 16 frozen cases')
        previous = next(a for a in reversed(report['attempts']) if a['status'] == 'completed')
        baseline = {row['case_id']: row for row in previous['results']}
        # The archive supplies data only; never execute its saved command arrays.
        current = dict(schema_version='framed_panel_frozen_recheck_v1',
                       archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                       source_svg_sha256=report['source_svg_sha256'],
                       seed=previous['search_seed'], iterations=previous['iterations'],
                       timeout_seconds=previous['timeout_seconds'], provenance=provenance(),
                       limits=battery.LIMITS, description_override=description, cases=[])
        rsvg = shutil.which('rsvg-convert')
        if not rsvg:
            raise ValueError('Independent librsvg check requires rsvg-convert')
        current['independent_renderer'] = subprocess.check_output([rsvg, '--version'], text=True).strip()
        def save():
            (output/'summary.json').write_text(json.dumps(current, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        save()
        for name in names or allowed:
            frozen = cases[name]
            raw = source.read(f'{name}/input/{name}.png')
            if hashlib.sha256(raw).hexdigest() != frozen['input_sha256']:
                raise ValueError(f'Frozen input hash differs: {name}')
            case = {k: frozen[k] for k in ('case_id', 'width', 'height', 'variation', 'description', 'input_sha256')}
            if description is not None:
                if not case['description'].startswith(report['source_description']):
                    raise ValueError('Frozen wording does not preserve its base description')
                case['description'] = description.strip()+case['description'][len(report['source_description']):]
            inputs = output/name/'input'
            inputs.mkdir(parents=True)
            (inputs/(name+'.png')).write_bytes(raw)
            # Same escaped description-table schema as battery.write_cases;
            # preserve the PNG bytes instead of rasterizing the reference again.
            table_root = ET.Element('root')
            entry = ET.SubElement(table_root, 'entry', kind='wurzelform', key=name)
            ET.SubElement(entry, 'beschreibung').text = case['description']
            ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = name+'.png'
            ET.ElementTree(table_root).write(inputs/'descriptions.xml', encoding='utf-8', xml_declaration=True)
            print(f'[Frozen panel] {name} started', flush=True)
            result = battery.run_case(case, output, iterations=previous['iterations'],
                timeout=previous['timeout_seconds'], keep_debug_artifacts=True,
                extra_cli_args=('--search-seed', str(previous['search_seed'])))
            row = dict(case_id=name, input_sha256=frozen['input_sha256'],
                       before={k: baseline[name].get(k) for k in ('satisfactory', 'failures', 'metrics', 'elapsed_seconds')},
                       after=result)
            if result.get('output_svg'):
                svg_path = output/result['output_svg']
                reference = output/name/'reference.svg'
                reference.write_bytes(source.read(f'references/{name}.svg'))
                for svg, target in ((reference, output/name/'native_reference.png'),
                                    (svg_path, output/name/'native_output.png')):
                    subprocess.run([rsvg, '-w', str(case['width']), '-h', str(case['height']),
                                    '-b', 'white', '-o', str(target), str(svg)], check=True, timeout=15)
                native_ref = cv2.imread(str(output/name/'native_reference.png'))
                native_out = cv2.imread(str(output/name/'native_output.png'))
                frozen_raster = cv2.imread(str(inputs/(name+'.png')))
                # The immutable input PNG is the reconstruction target in both
                # renderer checks. Re-rendering its source SVG changes historical
                # raster bytes and must not silently redefine that target.
                row['source_renderer_mse'] = float(np.mean((native_ref.astype(float)-frozen_raster)**2))
                row['independent_quality'] = battery.measure_quality(frozen_raster, svg_path.read_text(encoding='utf-8'),
                    render_fn=lambda *args: native_out)
                yy, xx = np.nonzero(frozen_raster.min(axis=2) < 235)
                bounds = (int(xx.min()), int(yy.min()), int(xx.max())+1, int(yy.max())+1)
                row['independent_profile'] = profile_quality(frozen_raster, native_out, 1, bounds)
            current['cases'].append(row)
            current['summary'] = dict(completed=len(current['cases']),
                passed=sum(c['after']['satisfactory'] for c in current['cases']),
                independent_passed=sum(c.get('independent_quality', {}).get('satisfactory', False) for c in current['cases']))
            save()
            print(f'[Frozen panel] {name}: {result["satisfactory"]} {result["failures"]}', flush=True)
    return current


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--cases', nargs='+')
    parser.add_argument('--description-file', type=Path, help='Supplementary wording check on the same frozen rasters')
    args = parser.parse_args()
    description = args.description_file.read_text(encoding='utf-8-sig') if args.description_file else None
    result = run(args.archive, args.output_dir, args.cases, description)
    print(json.dumps(result['summary']))
    return 0 if all(c['after']['satisfactory'] and c.get('independent_quality', {}).get('satisfactory')
                    and c.get('independent_profile', {}).get('passed') for c in result['cases']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
