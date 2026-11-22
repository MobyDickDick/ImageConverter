"""Generic search regressions: no catalog identity or motif-specific repair."""
from xml.etree import ElementTree as ET
from types import SimpleNamespace

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    ImageSearch, SearchPolicy, candidate_identity, image_search,
)
from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
from src.iCCModules.imageCompositeConverterNativeSearch import continue_native_search
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search, explore_parameters
from src.imageConverterSample import render_svg


def scene(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="80" viewBox="0 0 64 80">'
            '<rect width="64" height="80" fill="#bbbbbb"/>'+body+'</svg>')


def render(svg, width=64, height=80):
    return render_svg(svg, width, height)[:, :, ::-1].copy()


@pytest.mark.parametrize('body', [
    '<circle cx="32" cy="40" r="23" fill="#663344"/>',
    '<rect x="8" y="9" width="48" height="62" fill="#227755"/>',
    '<polygon points="5,65 32,8 59,65" fill="#335588"/>',
])
def test_transformed_white_overlay_can_be_removed_for_unrelated_shapes(body):
    target = render(scene(body))
    seed = scene('<g transform="translate(0 1)"><g transform="translate(0 -1)">'+body+
                 '<rect x="0" y="12" width="64" height="58" fill="white"/></g></g>')
    session = ImageSearch(SearchPolicy(seconds=3, max_seconds=3))
    with image_search(session):
        result, report = explore_structures(seed, target, render(seed), render, session, {}, level=1)
    assert result['error'] == 0
    assert any(p['origin'] == 'native_edit:remove' and p['accepted'] for p in report['proposals'])
    # Native source geometry is preserved; the unsupported overlay disappears.
    assert len([e for e in ET.fromstring(result['svg']).iter() if e.get('fill') == 'white']) == 0


def test_genuine_white_mark_is_not_removed_by_counterfactual_search():
    seed = scene('<rect x="8" y="9" width="48" height="62" fill="#227755"/>'
                 '<rect x="10" y="32" width="44" height="5" fill="white"/>')
    target = render(seed)
    session = ImageSearch(SearchPolicy(seconds=3, max_seconds=3))
    with image_search(session):
        result, report = explore_structures(seed, target, target, render, session, {}, level=1)
    assert result['svg'] == seed and result['error'] == 0
    assert any(p['origin'] == 'native_edit:remove' for p in report['proposals'])
    assert not any(p['accepted'] for p in report['proposals'])


def test_two_compensating_overlays_can_be_removed_together():
    target_svg = scene('<rect x="8" y="9" width="48" height="62" fill="#cde4d9"/>')
    # Removing white exposes black and loses; removing black alone is invisible.
    # The correct simpler construction requires a coupled structural edit.
    overlays = ('<rect x="12" y="12" width="40" height="56" fill="black"/>'
                '<rect x="12" y="12" width="40" height="56" fill="white"/>')
    seed = target_svg.replace('</svg>', overlays+'</svg>')
    target = render(target_svg)
    session = ImageSearch(SearchPolicy(seconds=3, max_seconds=3))
    with image_search(session):
        result, report = explore_structures(seed, target, render(seed), render, session, {}, level=2,
                                            max_probes=64)
    assert result['error'] == 0
    assert any(p['origin'] == 'native_edit:remove_pair' and p['accepted'] for p in report['proposals'])


def test_flat_parameter_strategies_use_distinct_restarts_until_requested_minimum():
    clock = [0.]
    def measure(p):
        clock[0] += .001
        return 10., 10., str(tuple(p)), np.zeros((1, 1, 3), dtype=np.uint8)
    seed = np.zeros(5)
    with search_configuration(mode='portfolio', adaptive=True, minimum_seconds=.5):
        with configured_image_search('any motif') as session:
            session.clock, session.active_since = lambda: clock[0], 0.
            _, _, report = explore_parameters(seed, 3, measure, measure(seed), source='generic',
                image=np.zeros((1, 1, 3)), satisfactory_fn=lambda *_: False)
            assert not session.minimum_pending
    assert clock[0] >= .5
    assert report['total_evaluations'] > 128
    assert any(worker['restarts'] > 0 for worker in report['attempts'])


def test_small_changes_to_same_construction_cannot_reset_parameter_allowance():
    from src.iCCModules.imageCompositeConverterVectorPolish import polish_generated_svg
    target = render(scene('<circle cx="32" cy="40" r="23" fill="#663344"/>'))
    calls = []
    def measured(*args):
        calls.append(1)
        return render(*args)
    session = ImageSearch(SearchPolicy(seconds=10, max_seconds=10, minimum_seconds=10))
    with image_search(session):
        for x in range(45, 51):
            seed = scene(f'<circle cx="{x}" cy="40" r="23" fill="#663344"/>')
            polish_generated_svg(seed, target, measured, structure_mode='off', acceptance_fn=lambda _: False)
    # The six input renders are separate from parameter work. New coordinates
    # do not grant another full budget to the same logical construction.
    assert len(calls) <= 288+6
    assert max(session.native_parameter_families.values()) <= 288


def test_render_evidence_survives_reentry_and_objective_changes():
    source = render(scene('<circle cx="32" cy="40" r="23" fill="#663344"/>'))
    first = scene('<g><circle cx="32" cy="40" r="23" fill="#663344"/></g>')
    second = scene('<g transform="scale(1)"><circle r="23" fill="#663344" cy="40" cx="32"/></g>')
    assert candidate_identity(first) == candidate_identity(second)
    session = ImageSearch(SearchPolicy())
    calls = []
    def counted(*args):
        calls.append(args[0])
        return render(*args)
    a, new_a = session.render_candidate(source, first, counted, 64, 80)
    b, new_b = session.render_candidate(source, second, counted, 64, 80)
    assert np.array_equal(a, b) and new_a and not new_b and len(calls) == 1
    changed = source.copy()
    changed[0, 0] = 0
    session.render_candidate(changed, second, counted, 64, 80)
    assert len(calls) == 2  # another source cannot inherit this evidence


def test_search_identity_preserves_text_spacing_and_tspan_tails():
    a = scene('<text xml:space="preserve">A<tspan>B</tspan> C</text>')
    b = scene('<text xml:space="preserve"> A<tspan>B</tspan>C</text>')
    assert candidate_identity(a) != candidate_identity(b)


def test_large_images_are_not_excluded_from_structural_counterprobes():
    target_svg = scene('<circle cx="32" cy="40" r="23" fill="#663344"/>').replace(
        'width="64" height="80" viewBox', 'width="640" height="800" viewBox')
    seed = target_svg.replace('</svg>', '<rect x="12" y="12" width="40" height="56" fill="white"/></svg>')
    target, initial = render(target_svg, 640, 800), render(seed, 640, 800)
    found = [False]
    def measured(svg, w, h):
        raster = render(svg, w, h)
        found[0] = np.array_equal(raster, target)
        return raster
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
    with image_search(session):
        result, report = explore_structures(seed, target, initial, measured, session, {}, level=1,
                                            stop_fn=lambda: found[0])
    assert result['error'] == 0 and report['render_evaluations'] == 1


def test_search_expands_and_exhausts_without_waiting_or_replaying(monkeypatch):
    from src.iCCModules import imageCompositeConverterVectorPolish as polish
    visited = []
    def exhausted(svg, image, render_fn, **kwargs):
        visited.append((candidate_identity(svg), kwargs['exploration_level']))
        return dict(svg=svg, rendered=render(svg), error=.1, initial_error=.1, improved=False,
                    structure_search={'probe_count': 0})
    monkeypatch.setattr(polish, 'polish_generated_svg', exhausted)
    seed = scene('<circle cx="32" cy="40" r="23" fill="#663344"/>')
    image = render(seed)
    session = ImageSearch(SearchPolicy(seconds=60, max_seconds=60, minimum_seconds=60))
    with image_search(session):
        report = continue_native_search(seed, image, render, acceptance_fn=lambda _: False)
        first_count = len(visited)
        again = continue_native_search(seed, image, render, acceptance_fn=lambda _: False)
    assert {level for _, level in visited} == {0, 1, 2, 3}
    assert len(visited) == len(set(visited)) == first_count
    assert report['search_control']['stop_reason'] == 'search_space_exhausted'
    assert again['search_control']['stop_reason'] == 'search_space_exhausted'
    assert report['search_control']['elapsed_seconds'] < 5


@pytest.mark.parametrize('color_order', ['BGR', 'RGB'])
def test_shared_scene_reconstruction_checks_meaning_before_replacing_any_template(monkeypatch, color_order):
    from src.iCCModules import imageCompositeConverterNonCompositeRuntime as models
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions
    target_svg = scene('<rect x="12" y="10" width="40" height="60" fill="#337799"/>')
    seed = scene('<circle cx="32" cy="40" r="23" fill="#337799"/>')
    bgr = render(target_svg)
    image = bgr if color_order == 'BGR' else bgr[:, :, ::-1].copy()
    calls = []
    def wrong(w,h,**kwargs):
        calls.append('wrong')
        # Even perfect pixels supplied by a proposal cannot assert a rectangle
        # if its actual SVG contains a circle.
        return dict(svg=seed, rendered=bgr, error=0.)
    def correct(w,h,**kwargs):
        calls.append('correct')
        assert np.array_equal(kwargs['image'],bgr)
        assert np.array_equal(kwargs['render_fn'](target_svg,w,h),bgr)
        return dict(svg=target_svg, rendered=bgr, error=0.)
    monkeypatch.setattr(models,'scene_reconstruction_fitters',lambda: [(wrong,'wrong'),(correct,'correct')])
    def renderer(svg,w,h):
        pixels = render(svg,w,h)
        return pixels if color_order == 'BGR' else pixels[:, :, ::-1].copy()
    session = ImageSearch(SearchPolicy(seconds=3,max_seconds=3))
    with image_search(session):
        result = continue_native_search(seed,image,renderer,description='Ein Rechteck.',
            assertions=description_assertions('Ein Rechteck.'),color_order=color_order)
    assert calls == ['wrong','correct']
    assert result['svg'] == target_svg and np.array_equal(result['rendered'],image)
    assert result['search_control']['stop_reason'] == 'satisfactory'


def test_rejected_protected_detail_cannot_be_adopted_through_frontier_callback(monkeypatch):
    from src.iCCModules import imageCompositeConverterVectorPolish as polish
    seed = scene('<circle cx="32" cy="40" r="23" fill="#663344"/>')
    other = scene('')
    target = render(other)
    calls = []
    def alternatives(svg, image, renderer, **kwargs):
        calls.append(svg)
        kwargs['on_alternative'](dict(svg=other, rendered=target, error=0.),
                                 dict(rejection='protected_existing_paint', accepted=False))
        raster = render(svg)
        return dict(svg=svg, rendered=raster, error=1., initial_error=1., improved=False,
                    structure_search={'probe_count': 0})
    monkeypatch.setattr(polish, 'polish_generated_svg', alternatives)
    session = ImageSearch(SearchPolicy(seconds=3, max_seconds=3))
    with image_search(session):
        result = continue_native_search(seed, target, render, acceptance_fn=lambda _: False, stop_fn=lambda: bool(calls))
    assert result['svg'] == seed


def test_cli_artifact_writer_does_not_start_an_unrequested_search():
    from src.iCCModules.imageCompositeConverterIterationInitialization import prepareIterationRuntimeImpl
    target_svg = scene('<circle cx="32" cy="40" r="23" fill="#663344"/>')
    target = render(target_svg)
    seed = target_svg.replace('</svg>', '<rect x="12" y="12" width="40" height="56" fill="white"/></svg>')
    saved = []
    setup = SimpleNamespace(emitIterationDescriptionHeaderImpl=lambda **kw: None,
        ensureIterationOutputDirsImpl=lambda **kw: None,
        buildIterationBaseAndLogPathImpl=lambda **kw: ('neutral', None))
    runtime = SimpleNamespace(buildIterationArtifactCallbacksImpl=lambda **kw: {
        'write_attempt_artifacts': lambda svg, *args, **kwargs: saved.append((svg, kwargs))})
    params = {'mode': 'composite'}
    session = ImageSearch(SearchPolicy(seconds=3, max_seconds=3, minimum_seconds=0))
    with image_search(session):
        state = prepareIterationRuntimeImpl(filename='neutral.png', params=params, reports_out_dir=None,
            svg_out_dir='', diff_out_dir='', target_img=target, width=64, height=80, run_seed=0,
            pass_seed_offset=0, iteration_setup_helpers=setup, iteration_runtime_helpers=runtime,
            time_ns_fn=lambda: 0, render_svg_to_numpy_fn=render, create_diff_image_fn=None,
            cv2_module=None, print_fn=lambda _: None)
        state['artifact_callbacks']['write_attempt_artifacts'](seed, failed=True)
    assert saved and saved[0][1]['failed'] is True  # no invented model approval
    assert saved[0][0] == seed
    assert 'vector_continuation' not in params
    assert session.renderings == 0


def test_uploaded_template_enters_the_same_search_after_alignment_fails(tmp_path):
    from PIL import Image
    from src.imageConverterSample import refine
    target_svg = scene('<circle cx="32" cy="40" r="23" fill="#663344"/>')
    target = render(target_svg)
    seed = target_svg.replace('</svg>', '<rect x="12" y="12" width="40" height="56" fill="white"/></svg>')
    source, sample, output = (tmp_path/name for name in ('neutral.png', 'template.svg', 'output.svg'))
    Image.fromarray(target[:, :, ::-1]).save(source)
    sample.write_text(seed, encoding='utf-8')
    report = refine(source, sample, output, 'Ein Kreis auf grauem Hintergrund.', 3.)
    assert report['restarted_from_description'] and report['passed'], report
    assert report['final_mse'] < report['initial_mse']*.1
    assert not any(n.tag.endswith('image') for n in ET.parse(output).getroot().iter())
