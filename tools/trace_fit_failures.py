"""GitHub-only diagnostic runner for conservative fitter rejection sites."""
from __future__ import annotations

import json
from pathlib import Path
import sys


def main():
    import pytest
    observed = 0
    modules = {'imageCompositeConverterGradientArrow.py', 'imageCompositeConverterHollowCrossPanel.py',
               'imageCompositeConverterLabeledSquare.py', 'imageCompositeConverterSquareStem.py',
               'imageCompositeConverterAlarmBell.py', 'imageCompositeConverterDiagonalSquareKelle.py',
               'imageCompositeConverterRotatedSquareKelle.py'}

    def describe(value):
        if value is None or isinstance(value, (str, bool, int, float)):
            return value if not isinstance(value, str) else value[:300]
        if hasattr(value, 'shape'):
            return dict(shape=list(value.shape), dtype=str(value.dtype))
        if isinstance(value, dict):
            return {str(k): describe(v) for k, v in value.items() if k not in {'svg', 'rendered'}}
        if isinstance(value, (list, tuple)) and len(value) < 25:
            return [describe(v) for v in value]
        return type(value).__name__

    def trace(frame, event, value):
        nonlocal observed
        filename = Path(frame.f_code.co_filename).name
        if filename not in modules:
            return None
        if event == 'return' and ('fit' in frame.f_code.co_name or 'observe' in frame.f_code.co_name) and observed < 150:
            observed += 1
            record = dict(file=filename, function=frame.f_code.co_name, line=frame.f_lineno,
                          returned=describe(value), locals={k: describe(v) for k, v in frame.f_locals.items()
                          if not callable(v) and not k.startswith('__')})
            print('[fit-diagnostic] '+json.dumps(record, default=str), flush=True)
        return trace

    sys.settrace(trace)
    try:
        return pytest.main(['-q', '-s', *sys.argv[1:]])
    finally:
        sys.settrace(None)


if __name__ == '__main__':
    raise SystemExit(main())
