"""Try analytic geometric models; never encode raster pixels as SVG shapes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time


def draft(source: Path, output: Path, *, deadline: float, description='', seed=0):
    import numpy as np
    from PIL import Image
    from src.imageConverterSample import prepare_sample, render_svg
    from src.imageConverterPreview import atomic_preview
    from src.iCCModules.imageCompositeConverterSearchPortfolio import standalone_image_search
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_candidate_quality, vector_quality_score
    from src.iCCModules.imageCompositeConverterNonCompositeRuntime import scene_reconstruction_fitters
    from src.iCCModules.imageCompositeConverterTwoWayValve import fit_two_way_valve

    with Image.open(source) as opened:
        rgb = np.asarray(opened.convert('RGB'))
    image = rgb[:, :, ::-1].copy()
    height, width = image.shape[:2]
    report = dict(passed=False, model_confirmed=False, result=False, evaluations=0,
                  stop_reason='no_geometric_model', source='analytic_geometry')
    best = None
    def render(svg, w, h):
        return render_svg(svg, w, h)[:, :, ::-1].copy()
    fitters = ((fit_two_way_valve, 'two_way_valve'), *scene_reconstruction_fitters())
    with standalone_image_search(str(source.resolve()), seconds=max(.001, deadline-time.time()),
                                 seed=seed, render_budget=4096) as session:
        session.bind_reference(image)
        for fitter, name in fitters:
            if time.time() >= deadline or session.time_reason():
                report['stop_reason'] = 'time_limit'
                break
            try:
                result = fitter(width, height, description=description, image=image, render_fn=render,
                    error_fn=lambda a, b: float(np.mean((a.astype(float)-b.astype(float))**2)/255**2),
                    **({'require_quality': False} if fitter is fit_two_way_valve else {}))
                if result is None:
                    continue
                svg = prepare_sample(result['svg'].encode('utf-8'), width, height)
                quality = vector_candidate_quality(image, render(svg, width, height), svg)
            except (ValueError, SyntaxError) as exc:
                report.setdefault('model_errors', []).append(f'{name}: {exc}')
                continue
            rank = (not quality['passed'], vector_quality_score(quality))
            if best is None or rank < best:
                best = rank
                atomic_preview(output, svg)
                atomic_preview(output.with_name('live-preview.svg'), svg)
                report.update(result=True, model=name, pixel_quality=quality, stop_reason='models_exhausted')
            if quality['passed']:
                break
        report['evaluations'] = session.renderings
    output.with_suffix('.json').write_text(json.dumps(report), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    parser.add_argument('--description', type=Path)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    description = args.description or args.output.parent/'preview-description.txt'
    text = description.read_text(encoding='utf-8') if description.is_file() else ''
    draft(args.source, args.output, deadline=args.deadline, description=text, seed=args.seed)


if __name__ == '__main__':
    main()
