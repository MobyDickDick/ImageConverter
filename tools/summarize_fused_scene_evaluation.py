"""Build or verify local full scene-fusion evidence (generated files stay out of Git)."""
import argparse
from pathlib import Path

from tools.summarize_layered_scene_evaluation import build, verify


DATASETS = {'development': 'fusion-development-inputs',
            'holdout': 'fusion-complete-holdout-inputs', 'plan_b': 'fusion-complete-plan-b-inputs'}
RUNS = [('development_before', 'development', 'fusion-baseline'),
        ('development_after', 'development', 'fusion-complete-development'),
        ('holdout_before', 'holdout', 'fusion-complete-before'),
        ('holdout_after', 'holdout', 'fusion-complete-holdout'),
        ('holdout_renamed', 'holdout', 'fusion-complete-renamed'),
        ('plan_b', 'plan_b', 'fusion-complete-plan-b')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, default=Path('.tmp'))
    parser.add_argument('--output', type=Path, default=Path('.tmp/fusion-full-evidence'))
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        if not (args.output/'manifest.json').is_file():
            parser.error('Full local evidence is missing. Use --output with a generated full evidence directory; Git contains compact summaries only.')
        verify(args.output)
    else:
        build(args.work_dir, args.output, datasets=DATASETS, runs=RUNS)


if __name__ == '__main__':
    main()
