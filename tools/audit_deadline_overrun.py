"""Replay the retained no-evaluation timeout and inspect durable phase evidence."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
from xml.etree import ElementTree as ET

from tools import evaluate_semantic_robustness as evaluation
from tools.run_plan_b_variations import run_case


def summarize_trace(path):
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    if not records or len({record['attempt'] for record in records}) != 1:
        raise ValueError('Expected exactly one timing attempt')
    previous = None
    gaps = []
    for record in records:
        if record['schema'] != 'conversion_timing_v1':
            raise ValueError('Unknown timing schema')
        if not all(math.isfinite(record[key]) for key in
                   ('monotonic_seconds', 'unix_seconds', 'process_cpu_seconds', 'elapsed_seconds')):
            raise ValueError('Non-finite timing evidence')
        if previous is not None:
            gap = record['monotonic_seconds']-previous['monotonic_seconds']
            if (gap < 0 or record['pid'] != previous['pid']
                    or record['process_cpu_seconds'] < previous['process_cpu_seconds']):
                raise ValueError('Timing sequence or observer changed')
            if (abs(gap-record['observation_gap_seconds']) > 1e-6
                    or abs(gap-(record['elapsed_seconds']-previous['elapsed_seconds'])) > 1e-6):
                raise ValueError('Inconsistent timing intervals')
            gaps.append(dict(from_phase=previous['phase'], to_phase=record['phase'], seconds=gap,
                observer_cpu_seconds=record['process_cpu_seconds']-previous['process_cpu_seconds'],
                unix_seconds=record['unix_seconds']-previous['unix_seconds']))
        previous = record
    by_phase = {record['phase']: record for record in records}

    def duration(start, finish):
        if start not in by_phase or finish not in by_phase:
            return None
        return by_phase[finish]['monotonic_seconds']-by_phase[start]['monotonic_seconds']

    return dict(records=len(records), phases=[record['phase'] for record in records],
                elapsed_seconds=records[-1]['elapsed_seconds'],
                largest_observation_gap=max(gaps, key=lambda gap: gap['seconds']) if gaps else None,
                spawn_seconds=duration('spawn_started', 'spawn_finished'),
                readiness_seconds=duration('spawn_finished', 'worker_ready'),
                teardown_seconds=duration('termination_requested', 'termination_finished'),
                outer_creation_seconds=duration('process_creation_started', 'process_created'),
                outer_reap_seconds=duration('reap_started', 'reap_finished'),
                cause='undetermined; phase observations do not distinguish sleep, scheduling, I/O or suspension')


def inspect_historical(prepared, historical, case_id):
    summary = evaluation.verify(prepared, historical)
    report = json.loads((historical/'report.json').read_text(encoding='utf-8'))
    record = next(record for record in report['records'] if record['case_id'] == case_id)
    control_path = historical/case_id/'conversion/reports'/(case_id+'_deadline.json')
    control = json.loads(control_path.read_text(encoding='utf-8'))
    return dict(report_sha256=evaluation.digest(historical/'report.json'), summary=summary,
                case_id=case_id, passed=record['passed'], raw_elapsed_seconds=record['raw']['elapsed_seconds'],
                returncode=record['raw'].get('returncode'), failures=record['raw']['failures'],
                control=control, control_sha256=evaluation.digest(control_path), cause='undetermined')


def verify(output):
    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    prepared = Path(report['prepared'])
    manifest = evaluation.verify_inputs(prepared)
    case = next(case for case in manifest['cases'] if case['case_id'] == report['case_id'])
    if inspect_historical(prepared, Path(report['historical_run']), report['case_id']) != report['historical']:
        raise ValueError('Historical evidence changed')
    for attempt in report['attempts']:
        folder = output/attempt['directory']
        for relative, expected in attempt['sha256'].items():
            if evaluation.digest(evaluation.contained(folder, relative)) != expected:
                raise ValueError('Replay evidence changed')
        observed = evaluation.observe(case, prepared, folder, attempt['record']['raw'],
                                      manifest['region_limits'], report['budget_seconds'])
        if observed != attempt['record']:
            raise ValueError('Replay decisions changed')
        for name, saved in attempt['timing'].items():
            if summarize_trace(folder/name) != saved:
                raise ValueError('Replay timing changed')
    passed = sum(attempt['record']['passed'] for attempt in report['attempts'])
    return dict(historical_attempts=report['historical']['summary']['attempts'],
                historical_failed_attempt_retained=not report['historical']['passed'],
                replay_attempts=len(report['attempts']), replay_passes=passed,
                replay_failures=len(report['attempts'])-passed, historical_cause='undetermined')


def run(prepared, historical, output, *, case_id='item04p2', budget=10., repetitions=3):
    if repetitions < 1 or not math.isfinite(budget) or budget <= 0:
        raise ValueError('Positive repetition count and finite budget required')
    manifest = evaluation.verify_inputs(prepared)
    case = next(case for case in manifest['cases'] if case['case_id'] == case_id)
    original = inspect_historical(prepared, historical, case_id)
    if original['passed']:
        raise ValueError('Expected a retained failed historical attempt')
    output.mkdir(parents=True, exist_ok=False)
    runtime = evaluation.source_hashes(evaluation.ROOT)
    report = dict(schema='deadline_overrun_audit_v1', prepared=str(prepared.resolve()),
                  historical_run=str(historical.resolve()), historical=original, case_id=case_id,
                  budget_seconds=budget, runtime_sha256=runtime, attempts=[])
    for index in range(repetitions):
        directory = f'replay-{index+1:02}'
        folder = output/directory
        inputs = folder/case_id/'input'
        inputs.mkdir(parents=True)
        shutil.copyfile(evaluation.contained(prepared, case['image']), inputs/(case_id+'.png'))
        root = ET.Element('root')
        entry = ET.SubElement(root, 'entry')
        ET.SubElement(entry, 'beschreibung').text = case['description']
        ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = case_id+'.png'
        ET.ElementTree(root).write(inputs/'descriptions.xml', encoding='utf-8', xml_declaration=True)
        raw = run_case(case, folder, timeout=budget+30, iterations=64,
                       extra_cli_args=('--search-seconds', str(budget), '--search-max-seconds', str(budget),
                                       '--search-seed', '17'))
        record = evaluation.observe(case, prepared, folder, raw, manifest['region_limits'], budget)
        traces = list((folder/case_id).rglob('*.timing.jsonl'))
        traces += list((folder/case_id/'conversion/reports').glob('*_timing.jsonl'))
        timing = {path.relative_to(folder).as_posix(): summarize_trace(path) for path in traces}
        files = [path for path in folder.rglob('*') if path.is_file()]
        report['attempts'].append(dict(directory=directory, record=record, timing=timing,
            sha256={path.relative_to(folder).as_posix(): evaluation.digest(path) for path in files}))
        evaluation.write_json(output/'report.json', report)
        print(directory, record['passed'], raw['elapsed_seconds'], flush=True)
    if runtime != evaluation.source_hashes(evaluation.ROOT):
        raise ValueError('Runtime changed during audit')
    return verify(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path)
    parser.add_argument('--historical-run', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--trace', type=Path)
    parser.add_argument('--repetitions', type=int, default=3)
    args = parser.parse_args()
    if args.trace:
        result = summarize_trace(args.trace)
    elif args.verify:
        result = verify(args.verify)
    else:
        if not all((args.prepared, args.historical_run, args.output)):
            parser.error('Replay requires --prepared, --historical-run and --output')
        result = run(args.prepared, args.historical_run, args.output, repetitions=args.repetitions)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
