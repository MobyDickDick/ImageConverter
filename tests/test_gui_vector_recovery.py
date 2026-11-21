"""Description-only conversion must never start a second raster reconstruction."""
import io
import json

import numpy as np
from PIL import Image
import pytest

from src import imageConverterGui as gui
from src import imageConverterRecovery as recovery
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.imageConverterSample import refine, render_svg

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24">'
       '<circle cx="16" cy="12" r="7" fill="#225599"/></svg>')


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    monkeypatch.setattr(jobs, 'publish_best', lambda *args: None)
    buffer = io.BytesIO()
    Image.fromarray(render_svg(SVG,32,24)).save(buffer, format='PNG')
    uploaded = jobs.upload('neutral.png', buffer.getvalue())
    job = jobs.jobs[uploaded['id']]
    job.update(description='Ein Kreis.', search_seed=7)
    try:
        yield jobs, job, jobs.folder(job['id'])
    finally:
        jobs.close()


@pytest.mark.parametrize('output_kind', ['passed', 'failed', 'missing'])
def test_gui_stops_after_description_fit_even_with_remaining_time(case, monkeypatch, output_kind):
    jobs, job, folder = case
    job.update(status='running', started=gui.time.time(), profile='thorough')
    commands = []
    class Process:
        returncode = 0 if output_kind == 'passed' else 1
        def __init__(self, command, **kwargs):
            commands.append(command)
            assert 'src.imageConverterRecovery' not in command
            if output_kind != 'missing':
                name = 'converted_svgs/UPLOAD.svg' if output_kind == 'passed' else 'converted_svg_failed/Failed_UPLOAD.svg'
                path = folder/'output'/name
                path.parent.mkdir(parents=True)
                path.write_text(SVG, encoding='utf-8')
        def wait(self, timeout):
            assert timeout > 230  # first stage returned early with time available
    def forbidden(*args, **kwargs):
        pytest.fail('second reconstruction was invoked')
    monkeypatch.setattr(gui.subprocess, 'Popen', Process)
    monkeypatch.setattr(jobs, 'recover_result', forbidden)
    jobs.run(job['id'])
    assert len(commands) == 1 and job['conversion_policy'] == 'description_only_v1'
    assert not job.get('recovery')
    assert job['result'] == (output_kind != 'missing')
    assert job['quality'] == ('passed' if output_kind == 'passed' else 'warning' if output_kind == 'failed' else 'unknown')


def test_retired_recovery_never_renders_or_overwrites_any_result(case):
    _, job, folder = case
    output = folder/'recovery.svg'
    output.write_text('keep historical evidence', encoding='utf-8')
    observed = []
    report = recovery.recover(folder/'does-not-exist.png', output, 'Ein Kreis.', 240,
                              on_preview=observed.append)
    assert output.read_text() == 'keep historical evidence'
    assert report['evaluations'] == 0 and not report['passed'] and not observed
    assert report['stop_reason'] == 'description_only_no_raster_recovery'


@pytest.mark.parametrize('fault', ['extra_line', 'missing_circle', 'curve_patch', 'unresolved_description'])
def test_failed_cli_artifact_with_wrong_inventory_is_not_a_result(case, fault):
    _, job, folder = case
    svg = SVG
    if fault == 'extra_line':
        svg = svg.replace('</svg>', '<line x1="1" y1="1" x2="8" y2="9"/></svg>')
    elif fault == 'missing_circle':
        svg = svg.replace('<circle', '<ellipse').replace('r="7"', 'rx="7" ry="4"')
    elif fault == 'curve_patch':
        svg = svg.replace('</svg>', '<path d="M 1 1 Q 4 8 9 1 Z"/></svg>')
    else:
        job['description'] = 'Ein motorgetriebenes Symbol.'
    path = folder/'output/converted_svg_failed/Failed_UPLOAD.svg'
    path.parent.mkdir(parents=True)
    path.write_text(svg, encoding='utf-8')
    gui.collect_result(folder, job, 1)
    assert not job['result'] and job['result_rejection'] == 'description_inventory'
    assert job['description_error']
    assert not (folder/'result.svg').exists()


def test_template_alignment_preserves_described_inventory_without_native_search(case, monkeypatch):
    _, _, folder = case
    source = folder/'source.png'
    sample, output = folder/'sample.svg', folder/'refined.svg'
    sample.write_text(SVG.replace('cx="16"', 'cx="13"'), encoding='utf-8')
    from src.iCCModules import imageCompositeConverterNativeSearch as native
    def forbidden(*args, **kwargs):
        pytest.fail('template started raster reconstruction')
    monkeypatch.setattr(native, 'continue_native_search', forbidden)
    report = refine(source, sample, output, 'Ein Kreis.', .2, seed=12)
    assert report['continuation'] is None
    validate_svg_assertions(output.read_text(), description_assertions('Ein Kreis.'))


def test_fragmented_template_is_rejected_without_rebuilding(case):
    _, _, folder = case
    sample, output = folder/'sample.svg', folder/'refined.svg'
    sample.write_text(SVG.replace('</svg>', '<circle cx="4" cy="4" r="2"/></svg>'))
    with pytest.raises(ValueError, match='logical_object_count'):
        refine(folder/'source.png', sample, output, 'Ein Kreis.', .2)
    assert not output.exists()


def test_failure_diagnostics_do_not_manufacture_svg_results(tmp_path):
    from src.iCCModules import imageCompositeConverterConversionExecution as execution
    def forbidden(*args, **kwargs):
        pytest.fail('an error path attempted to embed the original')
    svg, diff = tmp_path/'missing.svg', tmp_path/'diagnostic.png'
    assert not execution._ensureEmbeddedSvgAtPath(svg_path=str(svg), image_path='unused',
        render_embedded_raster_svg_fn=forbidden)
    assert execution._writeFailedEmbeddedSvgArtifact(svg_out_dir=str(tmp_path), filename='neutral.png',
        image_path='unused', render_embedded_raster_svg_fn=forbidden) is None
    execution._ensureOutputArtifacts(svg_path=str(svg), diff_path=str(diff))
    assert not svg.exists() and not list(tmp_path.glob('*.svg'))
    assert diff.is_file()  # diagnostics remain available without fake geometry
