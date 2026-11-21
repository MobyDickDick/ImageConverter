"""Compose explicitly referenced SVG components in a supervised worker."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def convert(source, output, description, seconds, *, seed=0):
    from src.iCCModules.imageCompositeConverterSearchPortfolio import standalone_image_search
    with standalone_image_search(str(source.resolve()), seconds=seconds, seed=seed,
                                 directory=output.parent/'search') as session:
        try:
            report = _convert(source, output, description, seconds)
        except ValueError as exc:
            if not session.reason():
                raise
            report = dict(passed=False, result=False, stop_reason=session.reason(), message=str(exc))
        report['search_context'] = session.report()
        report['evaluations'] = session.renderings
        from src.imageConverterCatalog import atomic_json
        atomic_json(output.with_suffix('.json'), report)
        return report


def _convert(source, output, description, seconds):
    import numpy as np
    from PIL import Image
    from src.imageConverterRecovery import atomic_svg
    from src.imageConverterCatalog import atomic_json
    from src.iCCModules.imageCompositeConverterSvgComponents import compose_components, render_components
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_candidate_quality
    with Image.open(source) as image:
        target = np.asarray(image.convert('RGB'))
    svg, references, evaluations = compose_components(description, target, seconds=seconds)
    height, width = target.shape[:2]
    # Composition already uses the faithful RGB component renderer. Reuse its
    # measured candidate instead of routing the same raster through BGR/RGB.
    pixels = render_components(svg, width, height)
    if pixels is None:
        raise ValueError('Das Bildbudget endete vor der vollständigen Bauteilprüfung.')
    quality = vector_candidate_quality(target, pixels, svg)
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import candidate_scope, current_search
    session = current_search()
    session.measured(svg, float(quality['normalized_mse']), source='component_final',
                     scope='full_scene', valid=True, passed=quality['passed'])
    if quality['passed']:
        with candidate_scope('full_scene', 'component_final'):
            session.validate(dict(svg=svg), target)
    report = dict(passed=bool(quality['passed']), improved=False, evaluations=evaluations,
                  stop_reason='svg_components_composed', components=references,
                  final_quality=quality, description_error='')
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_svg(output, svg)
    atomic_json(output.with_suffix('.json'), report)
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return report


def main():
    from src.iCCModules.imageCompositeConverterDependencies import activate_vendored_site_packages
    activate_vendored_site_packages()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--description', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=30.)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    if not 0 < args.seconds <= 240:
        parser.error('--seconds muss zwischen 0 und 240 liegen')
    try:
        convert(args.source, args.output, args.description.read_text(encoding='utf-8'), args.seconds, seed=args.seed)
    except (OSError, ValueError, SyntaxError) as exc:
        from src.imageConverterCatalog import atomic_json
        args.output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(args.output.with_suffix('.json'), dict(passed=False, result=False,
            stop_reason='invalid_components', description_error=str(exc), message=str(exc)))
        print(str(exc), flush=True)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
