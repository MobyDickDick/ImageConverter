"""Build native vectors, accepting pixel and explicit description checks.

Like sample refinement, recovery can accept the delivered SVG independently of
the normal converter's model search. This does not assert model confirmation.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import time
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality, preferred_quality, vector_quality_score, vector_candidate_quality
from src.iCCModules.imageCompositeConverterArrowPair import fit_arrow_pair
from src.iCCModules.imageCompositeConverterHollowCrossPanel import fit_hollow_cross_panel
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions, draft_assertions
from src.iCCModules.imageCompositeConverterFallbackGroups import canvas
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search
from src.iCCModules.imageCompositeConverterNativeSearch import continue_native_search
from src.iCCModules.imageCompositeConverterStrokeConstraints import constrain_stroke_width
from src.imageConverterCatalog import atomic_json
from src.imageConverterSample import prepare_sample


def atomic_svg(path, svg):
    temporary = path.with_suffix('.svg.tmp')
    temporary.write_text(svg, encoding='utf-8')
    temporary.replace(path)


def recover(source: Path, output: Path, description: str, seconds: float, *, seed=0, candidate=None,
            clock=None, on_preview=None):
    image = cv2.imread(str(source))
    if image is None:
        raise ValueError('Das Original konnte nicht gelesen werden.')
    h, w = image.shape[:2]
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        assertions = description_assertions(description)
        assertion_error = ''
    except ValueError as exc:
        assertion_error = str(exc)
        assertions = dict(counts=[], no_text=False)
    partial_assertions = draft_assertions(assertions)
    # Rendering remains in this killable worker. Each completed improvement is
    # published immediately, so termination cannot erase the best native draft.
    from src.imageConverterSample import render_svg
    best, evaluations, revision = None, 0, 0
    report = dict(passed=False, model_confirmed=False, stop_reason='searching', evaluations=0)

    def publish(svg, raster, error):
        nonlocal best, revision
        quality = vector_candidate_quality(image, raster, svg)
        score = vector_quality_score(quality)
        if best is not None and best['passed'] and (not quality['passed'] or score >= best['score']-1e-10):
            return
        # A blank canvas is useful as a search seed, never as a result for a
        # nonblank source. Transparent white is the renderer's canvas color.
        if np.min(image) < 220 and np.min(raster) >= 245:
            return
        try:
            validate_svg_assertions(svg, partial_assertions)
        except ValueError:
            return  # an over-complete seed may be explored, never published as progress
        error_message = assertion_error
        try:
            validate_svg_assertions(svg, assertions)
        except ValueError as exc:
            error_message = str(exc)
        passed = bool(quality['passed'] and not error_message)
        # A fully checked construction outranks a cheaper invalid patchwork.
        if best is not None:
            if (not passed, score) >= (not best['passed'], best['score']-1e-10):
                return
        best = dict(svg=svg, rendered=raster, error=error, passed=passed, score=score)
        revision += 1
        report.update(evaluations=evaluations, revision=revision, pixel_quality=quality,
                      description_error=error_message, normalized_mse=error, selection_score=score,
                      passed=passed)
        atomic_svg(output, svg)
        atomic_json(output.with_suffix('.json'), report)
        if on_preview:
            on_preview(dict(report))

    def search_done():
        return bool(report['passed'] and preferred_quality(report.get('pixel_quality')))

    def render(svg, width, height, *, preview=True):
        nonlocal evaluations
        svg = constrain_stroke_width(svg, partial_assertions)
        evaluations += 1
        raster = render_svg(svg, width, height)[:, :, ::-1].copy()
        if preview:
            publish(svg, raster, float(np.square(image.astype(float)-raster.astype(float)).mean()/255**2))
        if best is not None and evaluations % 64 == 0:
            report.update(evaluations=evaluations, candidate_evaluations=session.evaluations,
                          elapsed_seconds=session.elapsed)
            atomic_json(output.with_suffix('.json'), report)
        return raster

    with search_configuration(mode='portfolio', adaptive=True, seed=seed, budget=384,
                              seconds=seconds, max_seconds=seconds, minimum_seconds=seconds):
        with configured_image_search(str(source)) as session:
            if clock is not None:
                session.clock, session.active_since = clock, clock()
            if candidate and candidate.is_file():
                try:
                    svg = prepare_sample(candidate.read_bytes(), w, h)
                    render(svg, w, h)
                except (ValueError, SyntaxError):
                    pass
            if not search_done():
                panel = fit_hollow_cross_panel(w,h,description=description,image=image,
                    render_fn=render,
                    error_fn=lambda a,b: float(np.square(a.astype(float)-b.astype(float)).mean()/255**2))
                if panel is not None:
                    publish(panel['svg'],panel['rendered'],panel['error'])
            arrow = None if search_done() else fit_arrow_pair(w, h, description=description, image=image,
                render_fn=render,
                error_fn=lambda a, b: float(np.square(a.astype(float)-b.astype(float)).mean()/255**2),
                draft=True)
            if arrow is not None:
                # Add shafts, heads and crossbar one at a time. Direction
                # conflicts remain explicit diagnostics, never a blank preview.
                root = ET.fromstring(arrow['svg'])
                partial = ET.Element(root.tag, root.attrib)
                for node in root:
                    if session.time_reason():
                        break
                    partial.append(copy.deepcopy(node))
                    render(ET.tostring(partial, encoding='unicode'), w, h)
            svg = best['svg'] if best else ET.tostring(canvas(image), encoding='unicode')
            # Structural composition inserts observed objects and residual
            # lines. Parameter searches then vary placement, widths and colors.
            # Only the actual published vector passing both checks can finish.
            fitted = None
            if not search_done() and not session.time_reason():
                fitted = continue_native_search(svg, image, render, assertions=partial_assertions,
                    description=description,
                    stop_fn=search_done,
                    acceptance_fn=lambda candidate: bool(search_done() and best and candidate == best['svg']),
                    on_candidate=lambda candidate: publish(candidate['svg'], candidate['rendered'], candidate['error']))
            search_control = fitted['search_control'] if fitted else {}
            report.update(stop_reason='quality_target_reached' if search_done() else
                          session.time_reason() or search_control.get('stop_reason', 'search_space_exhausted'),
                          search_control=search_control, evaluations=evaluations,
                          elapsed_seconds=session.elapsed, candidate_evaluations=session.evaluations)
            atomic_json(output.with_suffix('.json'), report)
    return report


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
    print('Plan B: verbleibende Suchzeit für elementweisen Vektoraufbau nutzen.', flush=True)
    recover(args.source, args.output, args.description.read_text(encoding='utf-8'), seconds,
            seed=args.seed, candidate=args.candidate,
            on_preview=lambda report: print('Vektorentwurf aktualisiert: '
                + json.dumps(report, ensure_ascii=False), flush=True))


if __name__ == '__main__':
    main()
