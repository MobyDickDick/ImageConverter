"""Generate, convert and independently verify scenes, retaining only replay recipes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def run(generator, seed, options=(), *, journal=None):
    if not generator.startswith('evaluate_') or not (ROOT/'tools'/f'{generator}.py').is_file():
        raise ValueError('Use an existing tools.evaluate_* generator')
    # The caller may choose generation parameters, never override ownership of
    # the temporary paths or ask a generator to read unrelated input folders.
    allowed = {'--rounded', '--outlines', '--variations', '--rotate', '--paraphrase',
               '--wide-nesting', '--include-edits', '--children', '--count', '--repeat-fill', '--same-fill'}
    if any(arg.startswith('-') and arg not in allowed for arg in options):
        raise ValueError('Unsupported generation option')
    journal = journal or ROOT/'config/test_run_seeds.jsonl'
    journal.parent.mkdir(parents=True, exist_ok=True)
    recipe = dict(generator=generator, seed=seed, options=list(options), search_seed=17,
                  budget_seconds=5, started=datetime.now(timezone.utc).isoformat())
    # Save the seed before preparing anything: a failed or interrupted run is
    # reproducible even when its temporary directory has already disappeared.
    with journal.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(recipe, ensure_ascii=False)+'\n')
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    parent = ROOT/'.tmp'
    parent.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='scene-', dir=parent) as work:
        inputs, output = Path(work)/'inputs', Path(work)/'cli'
        subprocess.run([sys.executable, '-m', 'tools.'+generator, '--prepare', str(inputs),
                        '--seed', str(seed), *options], cwd=ROOT, check=True)
        from tools.evaluate_layered_scene import evaluate_cases
        result = evaluate_cases(inputs, output, require_all=True)
        print(f"Verified: {result['accepted']}/{result['completed']} accepted; temporary data removed on exit")
        return {key: result[key] for key in ('accepted', 'completed')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('generator')
    parser.add_argument('--seed', required=True, type=int)
    args, options = parser.parse_known_args()
    run(args.generator, args.seed, options)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
