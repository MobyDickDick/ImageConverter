"""Verify disposable scenes; preserve compact failure evidence and replay recipes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def preserve_failure(work, destination, recipe, error):
    """Copy bounded diagnostic text before the owned temporary tree is removed.

    Generated rasters, reference/output SVGs and worker pickle files stay
    disposable. Hashes and truncation flags describe exactly what was retained.
    This is diagnostic evidence, never an alternative acceptance certificate.
    """
    destination.mkdir(parents=True, exist_ok=False)
    inventory = []
    candidates = [work/'prepare.log', work/'cli/report.json', work/'cli/verification.json']
    candidates += sorted((work/'cli').glob('*/converter.log'))
    candidates += sorted((work/'cli').glob('*/reference_access.json'))
    for reports in sorted((work/'cli').glob('*/conversion/reports')):
        candidates += sorted(p for p in reports.iterdir()
                             if p.is_file() and p.suffix in {'.json', '.log', '.jsonl'})
    total = 0
    for source in candidates:
        if not source.is_file():
            continue
        # A small fixed cap keeps failure uploads useful even after a noisy
        # worker. Missing/truncated diagnostics are visible in the inventory.
        data = source.read_bytes()
        relative = source.relative_to(work)
        available = max(0, min(256_000, 2_000_000-total))
        saved = data[-available:] if available else b''
        if source.name == 'report.json':
            # run_case includes the generator's reference SVG in each result.
            try:
                report = json.loads(data)
                for case in report.get('cases', []):
                    case.pop('svg', None)
                data_to_save = json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8')
                saved = data_to_save[:available]
            except (ValueError, TypeError, AttributeError):
                # Do not copy an incomplete report that may contain raw SVGs.
                # Its hash plus the worker logs still identify the failure.
                saved = b''
        target = destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(saved)
        total += len(saved)
        inventory.append(dict(path=relative.as_posix(), source_bytes=len(data),
                              source_sha256=hashlib.sha256(data).hexdigest(), saved_bytes=len(saved),
                              saved_sha256=hashlib.sha256(saved).hexdigest(),
                              truncated=len(data) > available or not saved and bool(data),
                              reference_svg_removed=source.name == 'report.json'))
    summary = dict(recipe=recipe, error_type=type(error).__name__, error=str(error),
                   evidence_kind='failure_diagnostics_only', files=inventory)
    (destination/'failure.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return destination


def run(generator, seed, options=(), *, journal=None, diagnostics=None, case_ids=()):
    if not generator.startswith('evaluate_') or not (ROOT/'tools'/f'{generator}.py').is_file():
        raise ValueError('Use an existing tools.evaluate_* generator')
    # The caller may choose generation parameters, never override ownership of
    # the temporary paths or ask a generator to read unrelated input folders.
    allowed = {'--rounded', '--outlines', '--variations', '--rotate', '--paraphrase',
               '--wide-nesting', '--include-edits', '--children', '--count', '--repeat-fill', '--same-fill',
               '--groups', '--clipped-parent'}
    if any(arg.startswith('-') and arg not in allowed for arg in options):
        raise ValueError('Unsupported generation option')
    journal = journal or ROOT/'config/test_run_seeds.jsonl'
    journal.parent.mkdir(parents=True, exist_ok=True)
    recipe = dict(generator=generator, seed=seed, options=list(options), search_seed=17,
                  budget_seconds=5, case_ids=list(case_ids), started=datetime.now(timezone.utc).isoformat())
    # Save the seed before preparing anything: a failed or interrupted run is
    # reproducible even when its temporary directory has already disappeared.
    with journal.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(recipe, ensure_ascii=False)+'\n')
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    parent = ROOT/'.tmp'
    parent.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='scene-', dir=parent) as work:
        work = Path(work)
        inputs, output = Path(work)/'inputs', Path(work)/'cli'
        try:
            with (work/'prepare.log').open('w', encoding='utf-8') as log:
                subprocess.run([sys.executable, '-m', 'tools.'+generator, '--prepare', str(inputs),
                                '--seed', str(seed), *options], cwd=ROOT, check=True,
                               stdout=log, stderr=subprocess.STDOUT)
            if case_ids:
                manifest = json.loads((inputs/'manifest.json').read_text(encoding='utf-8'))
                selected = [case for case in manifest if case['case_id'] in case_ids]
                if len(selected) != len(set(case_ids)):
                    raise ValueError('Requested case IDs are missing or duplicated')
                (inputs/'manifest.json').write_text(json.dumps(selected, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            from tools.evaluate_layered_scene import evaluate_cases
            result = evaluate_cases(inputs, output, require_all=True)
            print(f"Verified: {result['accepted']}/{result['completed']} accepted; temporary data removed on exit")
            return {key: result[key] for key in ('accepted', 'completed')}
        except BaseException as error:
            destination = (diagnostics or parent/'scene-failures')/work.name
            try:
                preserve_failure(work, destination, recipe, error)
                with journal.open('a', encoding='utf-8', newline='\n') as stream:
                    stream.write(json.dumps(dict(recipe, diagnostics=str(destination),
                                                 error_type=type(error).__name__))+'\n')
                print(f'Failure diagnostics: {destination}', file=sys.stderr, flush=True)
            except Exception as evidence_error:
                print(f'Could not preserve failure diagnostics: {evidence_error}', file=sys.stderr, flush=True)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('generator')
    parser.add_argument('--seed', required=True, type=int)
    parser.add_argument('--diagnostics', type=Path, help='Directory for compact failure bundles')
    parser.add_argument('--case-id', action='append', default=[], help='Run only this generated case (repeatable)')
    args, options = parser.parse_known_args()
    run(args.generator, args.seed, options, diagnostics=args.diagnostics, case_ids=args.case_id)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
