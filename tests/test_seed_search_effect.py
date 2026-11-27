"""A seed must reach real proposals, without forcing different good outputs."""
import io
import random
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    ImageSearch, SearchPolicy, candidate_identity, pixel_quality, preferred_quality,
)
from src.iCCModules.imageCompositeConverterFilledSymbols import _register
from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
from src.iCCModules.imageCompositeConverterNativeEdits import native_edits
from src.iCCModules.imageCompositeConverterSearchPortfolio import (
    configured_image_search, search_configuration, settings,
)
from src.imageConverterSample import refine, render_svg


SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="80" viewBox="0 0 64 80">'
       '<rect width="64" height="80" fill="#bbbbbb"/>'
       '<circle cx="32" cy="40" r="23" fill="#663344"/>'
       '<rect x="7" y="20" width="12" height="35" fill="#448855"/></svg>')


def render(svg, w, h):
    return render_svg(svg, w, h)[:, :, ::-1].copy()


def test_seeds_change_geometry_proposal_set_and_replay_independently_of_global_random():
    def proposals(seed):
        return [(candidate_identity(svg), op) for svg, op in native_edits(SVG, 64, 80, level=2, seed=seed)]
    a = proposals(17)
    random.seed(9801)
    assert proposals(17) == a
    b = proposals(18)
    assert a != b
    # This checks new geometry, not just a shuffle or seed in SVG metadata.
    assert {s for s, op in a if op == 'move_object'} != {s for s, op in b if op == 'move_object'}
    assert {s for s, op in a if op == 'resize_object'} != {s for s, op in b if op == 'resize_object'}
    assert len(a) == len(set(a))


def test_seed_affects_parameter_proposals_before_late_bot_fallback():
    image = np.zeros((16, 16, 3), dtype=np.uint8)
    def run(seed):
        calls, clock = [], [0.]
        def renderer(svg, w, h):
            calls.append(svg)
            clock[0] += .001
            return np.full_like(image, 200)
        with search_configuration(mode='portfolio', adaptive=True, seed=seed, seconds=10,
                                  max_seconds=10, minimum_seconds=10):
            with configured_image_search('neutral') as session:
                session.clock, session.active_since = lambda: clock[0], 0.
                result = _register(np.zeros(5), 5,
                    lambda p: '<svg values="'+' '.join(map(str, p))+'"/>', lambda p: True,
                    image, renderer, lambda a, b: 1., 'neutral_model', reconsider_after=8)
                return calls, result['svg'], session.report()
    a, best_a, report_a = run(17)
    replay, _, replay_report = run(17)
    b, best_b, report_b = run(18)
    assert a == replay and a != b
    assert report_a['render_sequence_sha256'] == replay_report['render_sequence_sha256']
    assert report_a['render_sequence_sha256'] != report_b['render_sequence_sha256']
    # Equally bad candidates cannot replace the incumbent just to vary output.
    assert best_a == best_b


def test_actual_bounded_structure_renders_replay_and_differ_across_seeds():
    image = np.zeros((80, 64, 3), dtype=np.uint8)
    initial = render(SVG, 64, 80)
    def run(seed):
        calls = []
        def renderer(svg, w, h):
            calls.append(candidate_identity(svg))
            return render(svg, w, h)
        with search_configuration(mode='portfolio', adaptive=True, seed=seed):
            with configured_image_search('neutral') as session:
                _, report = explore_structures(SVG, image, initial, renderer, session, {}, level=2, max_probes=8)
                return calls, report['proposals'], session.report()['render_sequence_sha256']
    a = run(17)
    assert run(17) == a
    b = run(18)
    assert a[0] != b[0] and a[2] != b[2]


def test_trace_does_not_change_when_only_seed_metadata_changes():
    image = render(SVG, 64, 80)
    traces = []
    for seed in (17, 18):
        session = ImageSearch(SearchPolicy())
        session.search_seed = seed
        session.render_candidate(image, SVG, render, 64, 80)
        traces.append(session.report()['render_sequence_sha256'])
    assert traces[0] == traces[1]


def test_weak_pixel_pass_template_keeps_selected_seed_without_second_search(tmp_path, monkeypatch):
    from src.iCCModules import imageCompositeConverterNativeSearch as search
    original = SVG.replace('<rect x="7" y="20" width="12" height="35" fill="#448855"/>', '')
    sample_svg = original.replace('cx="32"', 'cx="32.4"')
    target = render_svg(original, 64, 80)
    quality = pixel_quality(target, render_svg(sample_svg, 64, 80))
    assert quality['passed'] and not preferred_quality(quality)
    source, sample = tmp_path/'neutral.png', tmp_path/'sample.svg'
    Image.fromarray(target).save(source)
    sample.write_text(sample_svg, encoding='utf-8')
    seen = []
    def inspect(*args, **kwargs):
        seen.append(settings()['seed'])
        return None
    monkeypatch.setattr(search, 'continue_native_search', inspect)
    seed = 2**64-1
    report = refine(source, sample, tmp_path/'result.svg', 'Ein Kreis.', 1., seed=seed)
    assert seen == [] and report['search_seed'] == str(seed)


def test_gui_template_worker_receives_selected_seed_and_keeps_exact_result(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    buffer = io.BytesIO()
    Image.fromarray(render_svg(SVG, 64, 80)).save(buffer, format='PNG')
    try:
        uploaded = jobs.upload('neutral.png', buffer.getvalue())
        jobs.attach_sample(uploaded['id'], 'template.svg', SVG.encode())
        seed = 2**64-1
        started = jobs.start(uploaded['id'], 'Ein Kreis und ein Rechteck.', 'quick', seed=str(seed))
        jobs.threads[-1].join(timeout=20)
        result = jobs.snapshot(started['id'])
        assert result['status'] == 'done' and result['quality'] == 'passed', result
        assert result['sample_report']['search_seed'] == str(seed)
        assert result['sample_report']['search_budget_seconds'] == gui.PROFILES['quick'][1]
        assert result['sample_report']['evaluations'] == 1
        actual = render_svg((jobs.folder(started['id'])/'result.svg').read_text(), 64, 80)
        assert np.array_equal(actual, render_svg(SVG, 64, 80))
    finally:
        jobs.close()


def test_completed_template_checkpoint_survives_worker_exit_without_reconstruction(tmp_path, monkeypatch):
    from src.iCCModules import imageCompositeConverterNativeSearch as search
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    original = SVG.replace('<rect x="7" y="20" width="12" height="35" fill="#448855"/>', '')
    # This test declares one circle. A transformed coloured canvas rectangle
    # becomes an additional visible object and invalidates that fixture.
    original = original.replace('<rect width="64" height="80" fill="#bbbbbb"/>','')
    sample_svg = original.replace('cx="32"', 'cx="32.4"')
    Image.fromarray(render_svg(original, 64, 80)).save(tmp_path/'source.png')
    (tmp_path/'sample.svg').write_text(sample_svg)
    folder = tmp_path/'output'
    folder.mkdir()
    def interrupted(*args, **kwargs):
        pytest.fail('retired native search was invoked')
    monkeypatch.setattr(search, 'continue_native_search', interrupted)
    refine(tmp_path/'source.png', tmp_path/'sample.svg', folder/'refined.svg', 'Ein Kreis.', 2., seed=17)
    completed = (folder/'refined.svg').read_text()
    job = dict(width=64, height=80, description='Ein Kreis.', result=False)
    gui.collect_sample_result(tmp_path, job, -9)
    assert job['result'] and job['quality'] == 'passed'
    assert job['sample_report']['stop_reason'] == 'interrupted'
    assert np.array_equal(render_svg((tmp_path/'result.svg').read_text(), 64, 80), render_svg(completed, 64, 80))


@pytest.mark.parametrize('seed', [-1, 2**64, True])
def test_invalid_template_seed_is_rejected_before_work(tmp_path, seed):
    with pytest.raises(ValueError, match='Seed'):
        refine(tmp_path/'absent.png', tmp_path/'absent.svg', tmp_path/'out.svg', '', 1., seed=seed)
