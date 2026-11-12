"""Prepare and inspect reproducible SVG -> raster -> SVG experiments.

Unlike acceptance, diagnostic experiments also run variants of failing originals.
All attempts are retained; the converter still receives only pixels and wording.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import io
import json
import math
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

from tools import run_plan_b_variations as battery


def save_report(folder: Path, report: dict) -> None:
    temporary = folder / 'report.json.tmp'
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(folder / 'report.json')


def read_report(folder: Path) -> dict:
    return json.loads((folder / 'report.json').read_text(encoding='utf-8'))


def provenance() -> dict:
    """Identify actual Python sources, including local and untracked edits."""
    import hashlib
    from importlib import metadata
    digest = hashlib.sha256()
    for directory in ('src', 'tools'):
        for path in sorted((battery.ROOT / directory).rglob('*.py')):
            digest.update(path.relative_to(battery.ROOT).as_posix().encode('utf-8') + b'\0')
            digest.update(path.read_bytes() + b'\0')
    packages = {}
    for package in ('numpy', 'opencv-python-headless', 'opencv-python', 'PyMuPDF', 'Pillow'):
        try:
            packages[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            pass
    return dict(python=sys.version, python_executable=sys.executable,
                python_sources_sha256=digest.hexdigest(), packages=packages)


def inspect_svg(svg: str) -> dict:
    """Validate before rendering, and return a standalone SVG for the preview."""
    from src.imageConverterSample import prepare_sample
    if not isinstance(svg, str):
        raise ValueError('Bitte ein SVG auswählen.')
    prepare_sample(svg.encode('utf-8'), 1, 1)
    *_, width, height = battery.viewport(svg)
    if max(width, height) > 4096 or width * height > 4_000_000:
        raise ValueError('Die SVG-Zeichenfläche darf höchstens 4096 Pixel pro Seite und 4 Megapixel umfassen.')
    return dict(width=width, height=height,
                preview_svg=prepare_sample(svg.encode('utf-8'), width, height))


def prepare(svg: str, description: str, folder: Path, *, seed: int | None = None,
            name: str = 'Motiv.svg') -> dict:
    folder = folder.resolve()
    if folder.exists():
        raise FileExistsError(f'Der Laufordner existiert bereits: {folder}')
    if not isinstance(svg, str) or not isinstance(name, str):
        raise ValueError('Bitte ein SVG und einen gültigen Dateinamen angeben.')
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 12000:
        raise ValueError('Bitte eine eigenständige Bildbeschreibung mit 1 bis 12\'000 Zeichen eingeben.')
    if seed is None:
        seed = secrets.randbits(63)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('Der Seed muss eine ganze Zahl zwischen 0 und 2^63−1 sein.')
    # Validate resources before opening the SVG in a renderer. Retain the exact
    # uploaded bytes as evidence; prepare_sample is used only for validation.
    inspect_svg(svg)
    cases = [battery.make_original_case(svg, description.strip()),
             *battery.make_variations(svg, description.strip(), seed)]
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'source.svg').write_text(svg, encoding='utf-8')
    (folder / 'source_description.txt').write_text(description.strip(), encoding='utf-8')
    battery.write_cases(cases, folder)
    # Inputs can be moved by the CLI; immutable target images are for comparison.
    for case in cases:
        shutil.copyfile(folder / case['case_id'] / 'input' / (case['case_id'] + '.png'),
                        folder / case['case_id'] / 'target.png')
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=battery.ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'src', 'tools'], cwd=battery.ROOT, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = 'unknown', None
    report = dict(schema_version='plan_b_workbench_v1', name=Path(name.replace('\\', '/')).name[:180],
                  created=time.time(), seed=seed, source_svg_sha256=battery.sha256(svg.encode('utf-8')),
                  source_description=description.strip(), limits=dict(battery.LIMITS),
                  revision=revision, working_tree_dirty=dirty, status='prepared', active_case=None,
                  provenance=provenance(),
                  cases=cases, attempts=[], notes={}, purpose='diagnostic',
                  variation_profile='whole_motif_scale_0.94_1.06_translate_0.025')
    save_report(folder, report)
    return report


EXECUTION_FAILURES = {'converter_error', 'conversion_timeout', 'missing_or_ambiguous_output',
                      'conversion_or_measurement_error', 'reference_svg_access'}


def summary(report: dict) -> dict:
    latest = {c['case_id']: c['result'] for c in report['cases'] if 'result' in c}
    failures = Counter(reason for result in latest.values() for reason in result.get('failures', []))
    passed = sum(bool(r['satisfactory']) for r in latest.values())
    technical = sum(bool(EXECUTION_FAILURES.intersection(r.get('failures', []))) for r in latest.values())
    return dict(total=len(report['cases']), completed=len(latest), passed=passed,
                quality_failed=len(latest)-passed-technical, execution_failed=technical,
                failure_counts=dict(failures),
                satisfactory=len(latest) == battery.REQUIRED_COUNT and passed == battery.REQUIRED_COUNT)


def execute(folder: Path, case_ids: list[str], *, iterations: int = 64, timeout: float = 60) -> dict:
    folder = folder.resolve()
    report = read_report(folder)
    available = {c['case_id']: c for c in report['cases']}
    if (not case_ids or len(set(case_ids)) != len(case_ids) or any(c not in available for c in case_ids)):
        raise ValueError('Bitte gültige, verschiedene Fälle auswählen.')
    if type(iterations) is not int or not 1 <= iterations <= 4096 or not math.isfinite(timeout) or not 1 <= timeout <= 600:
        raise ValueError('Suchbudget: 1–4096 Iterationen; Zeitlimit: 1–600 Sekunden je Fall.')
    attempt_id = f'attempt_{len(report["attempts"])+1:04d}'
    output = folder / 'attempts' / attempt_id
    output.mkdir(parents=True, exist_ok=False)
    attempt = dict(id=attempt_id, cases=case_ids, iterations=iterations, timeout_seconds=timeout,
                   search_seed=report['seed'], started=time.time(), status='running', results=[],
                   provenance=provenance())
    report['attempts'].append(attempt)
    report.update(status='running')
    save_report(folder, report)
    try:
        for case_id in case_ids:
            report['active_case'] = case_id
            save_report(folder, report)
            case = {key: value for key, value in available[case_id].items() if key != 'result'}
            case['svg'] = (folder / case['reference_svg']).read_text(encoding='utf-8')
            battery.write_cases([case], output)
            case_provenance = provenance()
            print(f'[Workbench] {attempt_id} {case_id} gestartet', flush=True)
            result = battery.run_case(case, output, iterations=iterations, timeout=timeout,
                                      keep_debug_artifacts=True,
                                      extra_cli_args=('--search-seed', str(report['seed'])))
            result['artifact_root'] = output.relative_to(folder).as_posix()
            result['provenance'] = case_provenance
            attempt['results'].append(result)
            available[case_id]['result'] = result
            save_report(folder, report)
            print(f'[Workbench] {case_id}: {"PASS" if result["satisfactory"] else "FAIL"} {result["failures"]}', flush=True)
        attempt['status'] = 'completed'
        report['status'] = 'completed'
    except BaseException as exc:
        attempt.update(status='interrupted' if isinstance(exc, KeyboardInterrupt) else 'error', error=str(exc))
        report['status'] = attempt['status']
        raise
    finally:
        attempt['finished'] = time.time()
        report['active_case'] = None
        save_report(folder, report)
    return report


def export_csv(report: dict) -> bytes:
    stream = io.StringIO(newline='')
    fields = ['case_id', 'attempt', 'seed', 'iterations', 'timeout_seconds', 'satisfactory',
              'failures', 'elapsed_seconds', 'normalized_mse', 'foreground_mse', 'edge_alignment',
              'foreground_iou', 'input_sha256', 'output_sha256', 'description', 'note']
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for attempt in report['attempts']:
        for result in attempt['results']:
            writer.writerow(dict(case_id=result['case_id'], attempt=attempt['id'], seed=report['seed'],
                                 iterations=attempt['iterations'], timeout_seconds=attempt['timeout_seconds'],
                                 satisfactory=result['satisfactory'], failures=';'.join(result['failures']),
                                 elapsed_seconds=result.get('elapsed_seconds'), **result.get('metrics', {}),
                                 input_sha256=result.get('input_sha256'), output_sha256=result.get('output_sha256'),
                                 description=result['description'], note=report['notes'].get(result['case_id'], '')))
    return ('\ufeff' + stream.getvalue()).encode('utf-8')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--svg', type=Path)
    parser.add_argument('--description-file', type=Path)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--cases', nargs='+', help='original, probe_01 … probe_16, or all')
    parser.add_argument('--iterations', type=int, default=64)
    parser.add_argument('--timeout-seconds', type=float, default=60)
    args = parser.parse_args(argv)
    if bool(args.svg) != bool(args.description_file):
        parser.error('--svg und --description-file gehören zusammen')
    if args.svg:
        prepare(args.svg.read_text(encoding='utf-8-sig'), args.description_file.read_text(encoding='utf-8-sig'),
                args.run_dir, seed=args.seed, name=args.svg.name)
    if args.cases:
        cases = [c['case_id'] for c in read_report(args.run_dir)['cases']] if args.cases == ['all'] else args.cases
        execute(args.run_dir, cases, iterations=args.iterations, timeout=args.timeout_seconds)
    report = read_report(args.run_dir)
    print(json.dumps(summary(report), ensure_ascii=False))
    # A finished diagnostic run can contain quality failures. Consult its report.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
