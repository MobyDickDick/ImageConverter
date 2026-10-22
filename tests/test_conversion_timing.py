"""Observed phase gaps must stay distinct from explanations for those gaps."""
import json
import os
import subprocess
import sys
import time

import pytest

from src.iCCModules import imageCompositeConverterTiming as timing


def read_trace(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def invoke(tmp_path, code, timeout):
    with (tmp_path/'process.log').open('w', encoding='utf-8') as log:
        return timing.run_timed_process([sys.executable, '-c', code], cwd=tmp_path,
            env=dict(os.environ), stdout=log, stderr=subprocess.STDOUT, timeout=timeout)


def test_blocked_process_has_durable_timeout_and_reaping_evidence(tmp_path):
    with pytest.raises(subprocess.TimeoutExpired):
        invoke(tmp_path, 'import time; time.sleep(30)', .3)
    records = read_trace(tmp_path/'process.timing.jsonl')
    phases = [record['phase'] for record in records]
    assert phases == ['process_creation_started', 'process_created', 'wait_failed',
                      'kill_started', 'kill_finished', 'reap_started', 'reap_finished',
                      'process_attempt_finished']
    assert records[2]['error'] == 'TimeoutExpired'
    assert records[-1]['elapsed_seconds'] < 2.
    assert all(record['pid'] == os.getpid() for record in records)
    assert all(record['unix_seconds'] > 0 and record['process_cpu_seconds'] >= 0 for record in records)


def test_delayed_process_creation_is_charged_to_outer_budget(tmp_path, monkeypatch):
    original = timing.subprocess.Popen

    def delayed(*args, **kwargs):
        time.sleep(.35)
        return original(*args, **kwargs)

    monkeypatch.setattr(timing.subprocess, 'Popen', delayed)
    with pytest.raises(subprocess.TimeoutExpired):
        invoke(tmp_path, 'import time; time.sleep(30)', .2)
    records = read_trace(tmp_path/'process.timing.jsonl')
    assert records[1]['phase'] == 'process_created'
    assert records[1]['observation_gap_seconds'] >= .35
    assert records[2]['error'] == 'TimeoutExpired'


def test_late_success_after_observer_pause_is_a_timeout(tmp_path, monkeypatch):
    original = timing.subprocess.Popen.wait
    delayed = False

    def wait_after_pause(process, *args, **kwargs):
        nonlocal delayed
        if not delayed:
            delayed = True
            time.sleep(.4)
        return original(process, *args, **kwargs)

    monkeypatch.setattr(timing.subprocess.Popen, 'wait', wait_after_pause)
    with pytest.raises(subprocess.TimeoutExpired):
        invoke(tmp_path, 'pass', .3)
    records = read_trace(tmp_path/'process.timing.jsonl')
    phases = [record['phase'] for record in records]
    assert 'late_exit_observed' in phases
    assert records[phases.index('process_exit_observed')]['returncode'] == 0
    assert 'kill_started' not in phases


def test_successful_process_keeps_its_output_and_exit_status(tmp_path):
    completed = invoke(tmp_path, 'print("complete")', 3.)
    assert completed.returncode == 0
    assert (tmp_path/'process.log').read_text().strip() == 'complete'
    records = read_trace(tmp_path/'process.timing.jsonl')
    assert records[-2]['phase'] == 'process_exit_observed'
    assert records[-1]['phase'] == 'process_attempt_finished'


def test_trace_retains_prior_attempts_and_observation_gaps(tmp_path):
    path = tmp_path/'trace.jsonl'
    first = timing.TimingTrace(path)
    first.mark('before_pause')
    time.sleep(.05)
    first.mark('after_pause')
    timing.TimingTrace(path).mark('new_attempt')
    records = read_trace(path)
    assert records[1]['observation_gap_seconds'] >= .05
    assert records[0]['attempt'] == records[1]['attempt'] != records[2]['attempt']


@pytest.mark.parametrize('field,value', [('monotonic_seconds', -1.), ('pid', -1),
                                       ('observation_gap_seconds', 100.), ('elapsed_seconds', 100.)])
def test_phase_analyzer_rejects_inconsistent_timing_evidence(tmp_path, field, value):
    from tools.audit_deadline_overrun import summarize_trace
    path = tmp_path/'trace.jsonl'
    trace = timing.TimingTrace(path)
    trace.mark('before')
    trace.mark('after')
    records = read_trace(path)
    records[-1][field] = value
    path.write_text('\n'.join(json.dumps(record) for record in records)+'\n', encoding='utf-8')
    with pytest.raises(ValueError):
        summarize_trace(path)
