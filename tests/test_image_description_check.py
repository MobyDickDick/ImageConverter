"""Check independent image evidence, abstention, persistence and the HTTP path."""
import io
import json
import threading
from http.client import HTTPConnection

import pytest
from PIL import Image, ImageDraw

from src.imageConverterDescriptionCheck import check_description


def picture(shape='circle', fill=(140, 140, 140), outline='black'):
    image = Image.new('RGB', (96, 96), 'white')
    draw = ImageDraw.Draw(image)
    if shape == 'circle':
        draw.ellipse((15, 15, 80, 80), fill=fill, outline=outline, width=3)
    else:
        draw.rectangle((15, 15, 80, 80), fill=fill, outline=outline, width=3)
    return image


def encoded(image):
    data = io.BytesIO()
    image.save(data, format='PNG')
    return data.getvalue()


@pytest.mark.parametrize('text,field', [
    ('Ein rotes Dreieck.', 'Grundform'),
    ('Ein roter Kreis.', 'Flächenfarbe'),
    ('Ein Kreis mit blauem Rand.', 'Randfarbe'),
    ('Ein Kreis ohne Rand.', 'Rand'),
    ('Hintergrund: schwarz.', 'Hintergrund'),
    ('Ein Kreis auf schwarzem Hintergrund.', 'Hintergrund'),
])
def test_reports_specific_mismatches_from_pixels(text, field):
    report = check_description(picture(), text)
    assert report['status'] == 'mismatch'
    assert any(c['field'] == field and c['status'] == 'mismatch' for c in report['checks'])
    assert report['description'] == text
    assert report['observations']['shape'] == 'Kreis'


@pytest.mark.parametrize('text', [
    'Ein grauer Kreis mit schwarzem Rand. Hintergrund: weiß.',
    'Das Bild zeigt eine graue Kreisscheibe auf weissem Hintergrund.',
    'Ein Kreis. Mit der Beschriftung "A".',
])
def test_agreement_is_always_bounded_and_never_certifies_whole_description(text):
    report = check_description(picture(), text)
    assert report['status'] == 'partial'
    assert all(c['status'] == 'agrees' for c in report['checks'])
    assert 'gesamte Beschreibung' in report['message']
    assert 'nicht vollständig' in report['limitations']


@pytest.mark.parametrize('text', [
    'Kein rotes Dreieck.', 'Ein rotes Dreieck oder ein Kreis.',
    'Ein rotes Dreieck fehlt.', 'Ein rotes Dreieck wäre möglich.',
    'Ein rotes Dreieck soll entstehen.', 'Form ähnlich wie ein rotes Dreieck.',
    'Beschriftung: "Ein rotes Dreieck".', '„Ein rotes Dreieck“',
    'Eine Linie neben einem roten Dreieck.', 'Ein Kreis ist nicht rot.',
    'Vielleicht ein rotes Dreieck.', 'Falls ein rotes Dreieck vorhanden ist.',
    'Ein rotes Dreieck ist ausgeschlossen.', 'Ein rotes Dreieck wird gesucht.',
])
def test_negations_quotes_alternatives_and_unsupported_language_abstain(text):
    report = check_description(picture(), text)
    assert report['status'] == 'unknown'
    assert not report['checks']


def test_complex_and_empty_images_abstain_instead_of_using_catalog_text():
    image = picture()
    ImageDraw.Draw(image).text((40, 38), 'A', fill='black')
    report = check_description(image, 'Ein roter Kreis mit schwarzem Rand.')
    assert report['status'] == 'partial'
    assert report['observations']['kind'] == 'primary_outline'
    assert [c['field'] for c in report['checks']] == ['Grundform']
    assert check_description(image, 'Ein rotes Dreieck.')['status'] == 'unknown'
    assert check_description(image, 'Äussere Grundform: ein Dreieck.')['status'] == 'mismatch'
    ImageDraw.Draw(image).rectangle((1, 1, 4, 4), fill='black')
    assert check_description(image, 'Ein rotes Dreieck.')['status'] == 'unknown'
    assert check_description(Image.new('RGB', (96, 96), 'white'), 'Ein Kreis.')['status'] == 'unknown'
    assert check_description(picture(), '  ')['status'] == 'missing'


def test_gradient_shape_and_tightly_cropped_labeled_circle_check_only_outer_shape():
    image = picture()
    draw = ImageDraw.Draw(image)
    for y in range(28, 68):
        draw.line((28, y, 67, y), fill=(y*3, y*3, y*3))
    report = check_description(image, 'Äussere Grundform: ein blaues Rechteck mit rotem Rand.')
    assert report['status'] == 'mismatch'
    assert [c['field'] for c in report['checks']] == ['Grundform']
    cropped = picture().crop((15, 15, 81, 81))
    ImageDraw.Draw(cropped).text((28, 28), 'A', fill='black')
    assert check_description(cropped, 'Äussere Grundform: ein Dreieck.')['status'] == 'mismatch'
    # A genuinely clipped circle does not prove its complete outer shape.
    assert check_description(picture().crop((30, 15, 81, 81)), 'Ein Dreieck.')['status'] == 'unknown'


def test_outer_circle_does_not_disprove_a_described_inner_triangle():
    image = picture()
    ImageDraw.Draw(image).polygon([(48, 30), (60, 60), (36, 60)], fill='red')
    assert check_description(image, 'Ein rotes Dreieck.')['status'] == 'unknown'
    report = check_description(image, 'Eine einfarbig gefüllte Kreisscheibe mit einem roten Dreieck.')
    assert report['status'] == 'partial'
    assert [c['field'] for c in report['checks']] == ['Grundform']


def test_square_is_a_rectangle_and_color_boundaries_abstain():
    assert check_description(picture('square'), 'Ein Rechteck.')['status'] == 'partial'
    # A coarse colour name must not flag nearby grey values as contradictions.
    assert check_description(picture(), 'Ein hellgrauer Kreis.')['status'] == 'partial'
    assert not any(c['field'] == 'Flächenfarbe' for c in check_description(picture(), 'Ein hellgrauer Kreis.')['checks'])
    assert check_description(picture(fill=(245, 145, 25)), 'Ein oranger Kreis.')['status'] == 'partial'


def test_missing_claimed_rim_is_reported():
    assert check_description(picture(outline=None), 'Ein Kreis mit schwarzem Rand.')['status'] == 'mismatch'


def test_jobs_automatically_check_and_manual_check_does_not_edit_catalog(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {'KNOWN.PNG': 'Ein rotes Dreieck.'})
    jobs = gui.Jobs(tmp_path/'jobs')
    try:
        uploaded = jobs.upload('known.png', encoded(picture()))
        assert uploaded['description_check']['status'] == 'mismatch'
        assert uploaded['description_origin'] == 'catalog'
        # Older saved jobs receive a check when first read after an update.
        jobs.jobs[uploaded['id']].pop('description_check')
        assert jobs.snapshot(uploaded['id'])['description_check']['status'] == 'mismatch'
        checked = jobs.check_description(uploaded['id'], 'Ein grauer Kreis.')
        assert checked['description_check']['status'] == 'partial'
        assert checked['description'] == 'Ein rotes Dreieck.'
        assert not jobs.threads
        saved = jobs.save_description(uploaded['id'], 'Ein grauer Kreis.')
        assert saved['description_check']['description'] == saved['description']
        assert saved['description_check']['status'] == 'partial'
        restored = gui.Jobs(jobs.directory)
        try:
            assert restored.snapshot(saved['id'])['description_check'] == saved['description_check']
        finally:
            restored.close()
        # Current XML corrections invalidate and recompute an earlier report.
        monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {'KNOWN.PNG': 'Ein blauer Kreis.'})
        jobs.jobs[uploaded['id']]['description_origin'] = 'catalog'
        current = jobs.snapshot(uploaded['id'])
        assert current['description_check']['description'] == current['description'] == 'Ein blauer Kreis.'
        assert current['description_check']['status'] == 'mismatch'
    finally:
        jobs.close()


def test_http_checks_current_text_validates_input_and_rejects_active_job(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    server = gui.GuiServer(('127.0.0.1', 0), jobs)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(path, payload=None):
        connection = HTTPConnection(*server.server_address, timeout=10)
        try:
            connection.request('GET' if payload is None else 'POST', path,
                               body=None if payload is None else json.dumps(payload),
                               headers={'X-ImageConverter': '1'})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    try:
        uploaded = jobs.upload('unknown.png', encoded(picture()))
        path = f"/api/jobs/{uploaded['id']}/check"
        status, checked = request(path, dict(description='Ein roter Kreis.'))
        assert status == 200 and checked['description_check']['status'] == 'mismatch'
        assert checked['description'] == ''
        assert request('/api/config')[1]['description_check']
        for value in (None, 42, [], 'x'*12001):
            assert request(path, dict(description=value))[0] == 400
        jobs.jobs[uploaded['id']]['status'] = 'running'
        assert request(path, dict(description='Ein Kreis.'))[0] == 409
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
