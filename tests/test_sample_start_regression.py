"""A stale optional SVG must not prevent a fresh description conversion."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image

from src import imageConverterGui as gui
from src.imageConverterSample import prepare_sample
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterRepresentation import logical_inventory

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Pumpensymbol: Ein gefüllter Kreis mit Randkontur enthält ein kontrastierendes '
               'gefülltes Dreieck, dessen Spitze nach unten zeigt. Weißer Hintergrund. '
               'Lage, Größe, Konturbreite und Farben ergeben sich aus dem Rasterbild.')
SAMPLE = ROOT/'tests/fixtures/template_start_regression/pump.svg'


def test_reported_pump_starts_through_real_gui_worker_and_drops_extra_template_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    before = SAMPLE.read_bytes()
    monkeypatch.setattr(jobs, 'publish_best', lambda *args: None)
    try:
        buffer = io.BytesIO()
        with Image.open(ROOT/'artifacts/images_to_convert/AC0253_2.jpg') as image:
            image.convert('RGB').save(buffer, format='PNG')
        uploaded = jobs.upload('neutral-pump.png', buffer.getvalue())
        jobs.attach_sample(uploaded['id'], 'previous.svg', before)
        started = jobs.start(uploaded['id'], DESCRIPTION, 'quick', seed='17')
        jobs.threads[-1].join(timeout=30)
        result = jobs.snapshot(started['id'])
        assert result['status'] == 'done' and result['result'], result
        report = result['sample_report']
        assert report['template_rejection'] == 'logical_object_count:all:2:4'
        assert report['restarted_from_description'] and report['continuation'] is None
        assert not result.get('recovery') and not result['description_error']
        folder = jobs.folder(started['id'])
        svg = (folder/'result.svg').read_text(encoding='utf-8')
        validate_svg_assertions(svg, description_assertions(DESCRIPTION))
        assert logical_inventory(svg, {'circle': 1, 'triangle': 1}) == {'circle': 1, 'triangle': 1}
        assert 'Traceback' not in (folder/'console.log').read_text(encoding='utf-8')
        assert 'Bildbeschreibung' in result['message']
        # Upload preparation fits overflowing paint to the original viewport;
        # starting the worker must preserve those prepared bytes and the donor.
        assert (folder/'sample.svg').read_text(encoding='utf-8') == prepare_sample(before, result['width'], result['height'])
        assert SAMPLE.read_bytes() == before
        # The draft is not certified merely because the conversion now starts.
        if not result['pixel_quality']['passed']:
            assert result['quality'] == 'warning'
    finally:
        jobs.close()


def test_invalid_description_cli_returns_diagnosis_without_traceback(tmp_path):
    source, description, output = tmp_path/'source.png', tmp_path/'description.txt', tmp_path/'output.svg'
    Image.new('RGB', (31,31), 'white').save(source)
    description.write_text('Es gibt genau zwei Kreise. Das Motiv enthält genau einen Kreis.', encoding='utf-8')
    completed = subprocess.run([sys.executable, '-m', 'src.imageConverterSample',
        '--source', str(source), '--sample', str(SAMPLE), '--description', str(description),
        '--output', str(output), '--seconds', '1'], cwd=ROOT,
        env=dict(os.environ, PYTHONIOENCODING='utf-8'), capture_output=True, timeout=10)
    assert completed.returncode == 1
    assert b'Traceback' not in completed.stdout+completed.stderr
    report = json.loads(output.with_suffix('.json').read_text(encoding='utf-8'))
    assert not report['result'] and not report['passed'] and not output.exists()
    assert report['description_error'] == 'conflicting_object_counts'


def test_gui_explains_failed_description_fit_instead_of_generic_sample_error(tmp_path):
    output = tmp_path/'output/refined.json'
    output.parent.mkdir()
    message = 'Die Vorlage passt nicht. Die neue Beschreibungskonvertierung ist ungenügend.'
    output.write_text(json.dumps(dict(result=False, passed=False, message=message,
        stop_reason='description_fit_failed')), encoding='utf-8')
    job = {}
    gui.collect_sample_result(tmp_path, job, 1)
    assert job['status'] == 'error' and not job['result'] and job['message'] == message
