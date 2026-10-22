"""Durable phase observations; observation gaps do not identify their cause."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time
import uuid


def clock_observation():
    return dict(monotonic_seconds=time.monotonic(), unix_seconds=time.time(),
                process_cpu_seconds=time.process_time(), pid=os.getpid())


class TimingTrace:
    def __init__(self, path):
        self.path = Path(path)
        self.attempt = uuid.uuid4().hex
        self.started = time.monotonic()
        self.previous = self.started
        self.max_gap = 0.
        self.last_heartbeat = self.started

    def mark(self, phase, **details):
        observation = clock_observation()
        current = observation['monotonic_seconds']
        gap = max(0., current-self.previous)
        self.max_gap = max(self.max_gap, gap)
        record = dict(schema='conversion_timing_v1', attempt=self.attempt, phase=phase,
                      **observation, elapsed_seconds=max(0., current-self.started),
                      observation_gap_seconds=gap, **details)
        with self.path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(record, allow_nan=False)+'\n')
        self.previous = current
        return record

    def heartbeat(self):
        current = time.monotonic()
        if current-self.last_heartbeat >= 1.:
            self.mark('supervisor_poll')
            self.last_heartbeat = current


def run_timed_process(command, *, cwd, env, stdout, stderr, timeout, check=False):
    trace = TimingTrace(Path(stdout.name).with_suffix('.timing.jsonl'))
    trace.mark('process_creation_started', timeout_seconds=timeout)
    deadline = trace.started+timeout
    try:
        with subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr) as process:
            trace.mark('process_created', child_pid=process.pid)
            try:
                while True:
                    remaining = deadline-time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(command, timeout)
                    try:
                        returncode = process.wait(timeout=min(1., remaining))
                    except subprocess.TimeoutExpired:
                        trace.heartbeat()
                        continue
                    trace.mark('process_exit_observed', returncode=returncode)
                    if time.monotonic() > deadline:
                        trace.mark('late_exit_observed')
                        raise subprocess.TimeoutExpired(command, timeout)
                    if check and returncode:
                        raise subprocess.CalledProcessError(returncode, command)
                    return subprocess.CompletedProcess(command, returncode)
            except BaseException as exc:
                trace.mark('wait_failed', error=type(exc).__name__)
                if process.poll() is None:
                    trace.mark('kill_started')
                    process.kill()
                    trace.mark('kill_finished')
                trace.mark('reap_started')
                process.wait()
                trace.mark('reap_finished', returncode=process.returncode)
                raise
    finally:
        trace.mark('process_attempt_finished')
