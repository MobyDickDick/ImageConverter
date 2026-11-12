"""Probe scoped power requests without changing power plans or entering sleep."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path

from src.iCCModules.imageCompositeConverterPower import conversion_awake


def probe():
    count_handles = lambda: None
    if os.name == 'nt':
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.GetProcessHandleCount.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetProcessHandleCount.restype = wintypes.BOOL

        def count_handles():
            count = wintypes.DWORD()
            if not kernel.GetProcessHandleCount(kernel.GetCurrentProcess(), ctypes.byref(count)):
                raise ctypes.WinError(ctypes.get_last_error())
            return count.value

    baseline = count_handles()
    events = []

    def event(phase, **details):
        events.append(dict(phase=phase, handle_count=count_handles(), **details))

    with conversion_awake(event_fn=event):
        pass
    try:
        with conversion_awake(event_fn=event):
            raise KeyboardInterrupt('controlled cancellation probe')
    except KeyboardInterrupt:
        pass
    final = count_handles()
    statuses = [e['status'] for e in events]
    expected = ['acquired', 'released'] * 2 if os.name == 'nt' else ['unsupported'] * 2
    handles_ok = os.name != 'nt' or (
        final == baseline and all(e['handle_count'] == baseline + (e['status'] == 'acquired')
                                  for e in events))
    return dict(schema='conversion_power_probe_v1', platform=os.name,
                baseline_handle_count=baseline, final_handle_count=final, events=events,
                passed=statuses == expected and handles_ok,
                scope='API acquisition and release only; no actual standby experiment')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = probe()
    encoded = json.dumps(report, indent=2)+'\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded, encoding='utf-8')
    print(encoded, end='')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
