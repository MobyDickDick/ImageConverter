"""Native topology, local missing-detail, assertions and shared-deadline checks."""
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search, pixel_quality
from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures, inventory
from src.iCCModules.imageCompositeConverterVectorPolish import polish_generated_svg
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search
from tools.run_plan_b_variations import render


def scene(body, size=80):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<rect width="{size}" height="{size}" fill="white"/>{body}</svg>')


def fixtures():
    seed = scene('<rect x="9" y="9" width="62" height="62" fill="#bb2244"/>')
    target = scene('<circle cx="40" cy="40" r="31" fill="#bb2244"/>'
                   '<line x1="22" y1="20" x2="34" y2="66" stroke="white" stroke-width="2"/>'
                   '<line x1="58" y1="20" x2="46" y2="66" stroke="white" stroke-width="2"/>')
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    return seed, render(target, 80, 80)


def probe(mode='combined', assertions=None):
    seed, target = fixtures()
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
    with image_search(session):
        result, report = explore_structures(seed, target, render(seed, 80, 80), render, session, assertions, mode=mode)
    return seed, target, result, report, session


def test_complete_alternatives_and_added_lines_recover_local_details_as_draft():
    seed, target, result, report, session = probe()
    assert report['probe_count'] <= 32
    assert report['selected_inventory']['circle'] == 1
    assert report['selected_inventory']['line'] >= 2
    assert any(p['inventory'].get('circle') for p in report['proposals'])
    assert any(p['inventory'].get('rect') == 2 for p in report['proposals'])
    before = render(seed, 80, 80)
    for x in (18, 42):
        region = np.s_[18:70, x:x+20]
        old = np.square(target[region].astype(float)-before[region]).mean()
        new = np.square(target[region].astype(float)-result['rendered'][region]).mean()
        assert new < old*.4
    assert not session.validated and report['model_confirmed'] is False
    assert 'path' not in result['svg'] and 'image' not in result['svg']


def test_primitive_and_line_hypotheses_are_independently_observable():
    _, _, primitive, p, _ = probe('primitives')
    _, _, lines, l, _ = probe('lines')
    assert inventory(primitive['svg']).get('circle') == 1
    assert 'line' not in inventory(primitive['svg'])
    assert 'circle' not in inventory(lines['svg'])
    assert inventory(lines['svg'])['line'] > 0
    assert {r['origin'] for r in p['proposals']} == {'raster_primitive_reconstruction'}
    assert all('residual_line_group' in r['origin'] for r in l['proposals'])


def test_explicit_object_counts_reject_topology_before_rendering():
    assertions = dict(counts=[dict(kind='line', count=0), dict(kind='circle', count=0)], no_text=True)
    _, _, result, report, _ = probe(assertions=assertions)
    assert not inventory(result['svg']).get('circle')
    assert not inventory(result['svg']).get('line')
    rejected = [p for p in report['proposals'] if p.get('rejection') == 'description_assertions']
    assert rejected and all('error' not in p for p in rejected)


def test_structure_renders_share_existing_deadline_without_new_session():
    seed, target = fixtures()
    now, calls = [0.], []
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: now[0])
    initial = render(seed, 80, 80)
    def slow(svg, w, h):
        calls.append(svg)
        assert now[0] < 1
        now[0] += .4
        return render(svg, w, h)
    with image_search(session):
        _, report = explore_structures(seed, target, initial, slow, session, {})
    assert len(calls) == session.evaluations == 3
    assert report['stop_reason'] == 'time_limit'
    assert session.limit == 1 and session.extensions == 0


def test_correct_incumbent_keeps_original_bytes_and_is_not_validated_by_fallback():
    seed, _ = fixtures()
    target = render(seed, 80, 80)
    with search_configuration(mode='portfolio', adaptive=True, minimum_seconds=1, seconds=1, max_seconds=1):
        with configured_image_search('exact') as session:
            assert polish_generated_svg(seed, target, render) is None
            assert not session.validated and not session.evaluations


def test_tiny_missing_line_is_explored_despite_small_global_error():
    seed = scene('', 256)
    target = render(scene('<line x1="100" y1="100" x2="140" y2="100" stroke="#333333" stroke-width="1"/>', 256), 256, 256)
    initial = render(seed, 256, 256)
    assert pixel_quality(target, initial)['normalized_mse'] < .001
    session = ImageSearch(SearchPolicy(seconds=2, max_seconds=2, minimum_seconds=2))
    with image_search(session):
        result = polish_generated_svg(seed, target, render)
    assert result and result['structure_search']['probe_count'] > 0
    assert result['improved'] and inventory(result['svg']).get('line')
    assert not session.validated


def test_parameter_refinement_cannot_erase_new_local_detail(monkeypatch):
    from src.iCCModules import imageCompositeConverterFilledSymbols as filled
    seed, target = fixtures()
    def damaged(parameters, geometry_count, build, valid, image, render_fn, error_fn, source, **kwargs):
        # Artificially claim a better scalar value while actually removing marks.
        svg = scene('<circle cx="40" cy="40" r="31" fill="#bb2244"/>')
        return dict(svg=svg, rendered=render(svg, 80, 80), error=0., evaluations=1,
                    search_control={}, source=source)
    monkeypatch.setattr(filled, '_register', damaged)
    session = ImageSearch(SearchPolicy(seconds=2, max_seconds=2, minimum_seconds=2))
    with image_search(session):
        result = polish_generated_svg(seed, target, render)
    assert result['structure_search']['refinement_reverted_for_local_detail']
    assert inventory(result['svg']).get('line', 0) >= 2
    actual = np.square(target.astype(float)-result['rendered']).mean()/255**2
    assert result['error'] == pytest.approx(actual)


def test_rgb_and_bgr_callers_propose_identical_native_colors(monkeypatch):
    from src.iCCModules import imageCompositeConverterFilledSymbols as filled
    monkeypatch.setattr(filled, '_register', lambda *a, **kw: None)
    seed, bgr = fixtures()
    def run(order):
        session = ImageSearch(SearchPolicy(seconds=2, max_seconds=2, minimum_seconds=2))
        def renderer(svg, w, h):
            pixels = render(svg, w, h)
            return pixels if order == 'BGR' else pixels[:, :, ::-1].copy()
        with image_search(session):
            return polish_generated_svg(seed, bgr if order == 'BGR' else bgr[:, :, ::-1].copy(), renderer, color_order=order)
    a, b = run('BGR'), run('RGB')
    assert a['svg'] == b['svg']
    assert a['error'] == pytest.approx(b['error'])
    assert np.array_equal(a['rendered'], b['rendered'][:, :, ::-1])


def test_negative_counterprobes_fail_local_detail_despite_matching_parent():
    _, target = fixtures()
    parent_only = scene('<circle cx="40" cy="40" r="31" fill="#bb2244"/>')
    shifted = scene('<circle cx="40" cy="40" r="31" fill="#bb2244"/>'
                    '<line x1="28" y1="20" x2="40" y2="66" stroke="white" stroke-width="2"/>')
    for broken in (parent_only, shifted):
        raster = render(broken, 80, 80)
        region = np.s_[18:70, 18:38]
        assert np.square(target[region].astype(float)-raster[region]).mean()/255**2 > .01


def test_probe_limit_is_independent_of_image_time():
    seed, target = fixtures()
    session = ImageSearch(SearchPolicy())
    with image_search(session):
        _, report = explore_structures(seed, target, render(seed, 80, 80), render, session, {}, max_probes=2)
    assert report['probe_count'] == session.evaluations == 2
    assert report['stop_reason'] == 'probe_limit'


def test_failed_structural_renders_count_as_evaluations_and_keep_incumbent():
    seed, target = fixtures()
    session = ImageSearch(SearchPolicy())
    with image_search(session):
        result, report = explore_structures(seed, target, render(seed, 80, 80), lambda *args: None,
                                             session, {}, mode='primitives', max_probes=2)
    assert result['svg'] == seed
    assert report['render_evaluations'] == session.evaluations == 2
    assert all(r['rejection'] == 'render_failed' for r in report['proposals'])


def test_frozen_audit_circle_recovers_both_chords_without_model_approval():
    import json
    from pathlib import Path
    import cv2
    from tools.evaluate_fallback_structure import local_regions, digest
    root = Path(__file__).resolve().parents[1] / 'artifacts/evaluation/fallback_structure_v1/inputs'
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    for name, sha in manifest['sha256'].items():
        assert digest(root / name) == sha
    folder = root / 'probe_01'
    image = cv2.imread(str(folder / 'original.jpg'))
    seed = (folder / 'seed.svg').read_text(encoding='utf-8')
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
    with image_search(session):
        result, report = explore_structures(seed, image, render(seed, 60, 60), render, session, {})
    assert inventory(result['svg']).get('circle') == 1
    assert inventory(result['svg']).get('line') == 2
    assert all(r['passed'] for r in local_regions(image, result['rendered'], manifest['cases'][1]['regions']))
    assert not session.validated and not report['model_confirmed']
