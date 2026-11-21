"""Compatibility API for the removed second reconstruction stage."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time



def atomic_svg(path, svg):
    temporary = path.with_suffix('.svg.tmp')
    temporary.write_text(svg, encoding='utf-8')
    temporary.replace(path)


def recover(source: Path, output: Path, description: str, seconds: float, *, seed=0, candidate=None,
            clock=None, on_preview=None):
    """Report the removed phase without generating or replacing any SVG."""
    return dict(passed=False, model_confirmed=False,
                stop_reason='description_only_no_raster_recovery', evaluations=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--description', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    # The deadline includes interpreter startup and native-library imports.
    seconds = args.deadline-time.time()
    if seconds <= 0:
        return
    print('Keine zweite Rekonstruktion: Bildbeschreibung bleibt verbindlich.', flush=True)
    recover(args.source, args.output, args.description.read_text(encoding='utf-8'), seconds,
            seed=args.seed, candidate=args.candidate,
            on_preview=lambda report: print('Vektorentwurf aktualisiert: '
                + json.dumps(report, ensure_ascii=False), flush=True))


if __name__ == '__main__':
    main()
