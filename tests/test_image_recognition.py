"""Recognition must abstain when pixels or reference evidence do not support it."""
import hashlib
import io

import pytest
from PIL import Image, ImageDraw

from src.imageConverterRecognition import ImageRecognition, plain_shape, rgb_image


def symbol(shape='circle', *, fill=(140, 140, 140), outline='black', size=96):
    image = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(image)
    box = (15, 15, size-16, size-16)
    if shape == 'circle':
        draw.ellipse(box, fill=fill, outline=outline, width=3)
    elif shape == 'rectangle':
        draw.rectangle((15, 22, size-16, size-23), fill=fill, outline=outline, width=3)
    else:
        draw.polygon([(size//2, 15), (size-16, size-16), (15, size-16)], fill=fill)
    return image


def image_bytes(image):
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


@pytest.fixture
def reference(tmp_path):
    source = tmp_path/'known.png'
    source.write_bytes(image_bytes(symbol()))
    svg = tmp_path/'known.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><circle cx="48" cy="48" r="33" fill="gray" stroke="black"/></svg>')
    row = dict(filename=source.name, image=source.name, image_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               role='catalog', status='pixel_pass', description='Ein grauer Kreis mit schwarzem Rand.',
               selected=dict(svg=svg.name, svg_sha256=hashlib.sha256(svg.read_bytes()).hexdigest(),
                             measurement=dict(renderers={r: dict(satisfactory=True) for r in ('mupdf', 'librsvg')})))
    payload = dict(rows=[row])
    return ImageRecognition(tmp_path, lambda: payload), row, source, svg, payload


@pytest.mark.parametrize('shape,expected', [('circle', 'Kreis'), ('rectangle', 'Rechteck'), ('triangle', 'Dreieck')])
def test_plain_shapes_from_pixels_without_catalog(shape, expected):
    result = plain_shape(symbol(shape))
    assert result and result['shape'] == expected
    assert 'grau' in result['description'] and 'Hintergrund: weiss' in result['description']


def test_unsupported_color_abstains_and_orange_adjective_is_valid():
    assert plain_shape(symbol(fill=(0, 255, 255))) is None
    assert 'oranger Kreis' in plain_shape(symbol(fill=(245, 145, 25)))['description']


@pytest.mark.parametrize('change', ['text', 'attachment', 'extra_pixel', 'gradient', 'clipped', 'blank', 'ellipse', 'internal_hole', 'near_rim_mark'])
def test_plain_shape_rejects_details_and_unsupported_scenes(change):
    image = symbol()
    draw = ImageDraw.Draw(image)
    if change == 'text':
        draw.text((40, 38), 'A', fill='black')
    elif change == 'attachment':
        draw.line((77, 48, 90, 48), fill='black', width=3)
    elif change == 'extra_pixel':
        image.putpixel((5, 5), (0, 0, 0))
    elif change == 'gradient':
        for y in range(28, 68):
            draw.line((28, y, 67, y), fill=(y*3, y*3, y*3))
    elif change == 'clipped':
        image = image.crop((20, 0, 96, 96))
    elif change == 'blank':
        image = Image.new('RGB', image.size, 'white')
    elif change == 'ellipse':
        image = Image.new('RGB', image.size, 'white')
        ImageDraw.Draw(image).ellipse((15, 30, 80, 65), fill='gray')
    elif change == 'internal_hole':
        draw.rectangle((35, 35, 40, 40), fill='white')
    elif change == 'near_rim_mark':
        draw.line((19, 47, 24, 47), fill='black', width=2)
    assert plain_shape(image) is None


def test_exact_decoded_pixels_recognized_after_rename_and_reencoding(reference):
    recognizer, row, source, _, _ = reference
    result = recognizer.recognize(rgb_image(image_bytes(rgb_image(source))))
    assert result['automatic']['kind'] == 'exact_reference'
    assert result['automatic']['description'] == row['description']
    assert result['matches'][0]['exact']
    assert result['matches'][0]['structure'] == {'circle': 1}
    assert result['reference_count'] == 1


def test_approximate_neighbour_never_automatically_copies_description(reference):
    recognizer, _, source, _, _ = reference
    image = rgb_image(source)
    ImageDraw.Draw(image).text((40, 38), 'A', fill='black')
    result = recognizer.recognize(image)
    assert result['matches'] and not result['matches'][0]['exact']
    assert result['automatic'] is None


@pytest.mark.parametrize('change', ['source', 'svg', 'failed_renderer', 'reserved', 'conflict', 'placeholder', 'outside', 'raster'])
def test_untrusted_or_stale_pairs_excluded_and_cache_invalidated(reference, change):
    recognizer, row, source, svg, _ = reference
    assert recognizer.recognize(rgb_image(source))['reference_count'] == 1
    if change == 'source':
        source.write_bytes(image_bytes(symbol(fill='red')))
    elif change == 'svg':
        svg.write_text('<svg/>')
    elif change == 'failed_renderer':
        row['selected']['measurement']['renderers']['librsvg']['satisfactory'] = False
    elif change == 'reserved':
        row['status'] = 'reserved'
    elif change == 'conflict':
        row['source_conflict'] = True
    elif change == 'placeholder':
        row['description'] = 'Unzugeordnete Wurzelform'
    elif change == 'outside':
        row['image'] = '../outside.png'
    else:
        svg.write_text('<svg><image href="image.png"/></svg>')
        row['selected']['svg_sha256'] = hashlib.sha256(svg.read_bytes()).hexdigest()
    assert recognizer.recognize(symbol())['reference_count'] == 0


def test_identical_pixels_with_conflicting_descriptions_abstain(reference):
    from copy import deepcopy
    recognizer, row, source, _, payload = reference
    other = deepcopy(row)
    other['description'] = 'Ein roter Kreis.'
    payload['rows'].append(other)
    result = recognizer.recognize(rgb_image(source))
    assert result['automatic'] is None
    assert 'unterschiedliche' in result['message']


def test_reference_asset_removed_after_reservation(reference):
    recognizer, row, source, _, _ = reference
    token = recognizer.recognize(rgb_image(source))['matches'][0]['token']
    assert recognizer.asset(token, 'source') == source
    row['status'] = 'reserved'
    assert recognizer.asset(token, 'source') is None


def test_gui_recognition_persists_and_does_not_overwrite_user_text(tmp_path, monkeypatch, reference):
    from src import imageConverterGui as gui
    recognizer, _, source, _, _ = reference
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.recognizer = recognizer
    try:
        uploaded = jobs.upload('unbekannt.png', source.read_bytes())
        assert not uploaded['description']
        recognized = jobs.recognize(uploaded['id'])
        assert recognized['description_origin'] == 'recognition'
        assert recognized['description'] == recognized['recognition']['automatic']['description']
        assert jobs.snapshot(uploaded['id'])['description'] == recognized['description']
        jobs.jobs[uploaded['id']].update(description='Meine eigene Beschreibung', description_origin='user')
        assert jobs.recognize(uploaded['id'])['description'] == 'Meine eigene Beschreibung'
        jobs.jobs[uploaded['id']]['status'] = 'running'
        with pytest.raises(gui.RequestError, match='laufende'):
            jobs.recognize(uploaded['id'])
        jobs.jobs[uploaded['id']].update(status='done', quality='warning')
        retry = jobs.editable(uploaded['id'])
        assert retry['recognition']['version'] == recognized['recognition']['version']
        jobs.save(retry)
        restored = gui.Jobs(jobs.directory)
        try:
            assert restored.snapshot(retry['id'])['recognition']['reference_count'] == 1
        finally:
            restored.close()
    finally:
        jobs.close()


def test_recognition_http_and_reference_previews(tmp_path, monkeypatch, reference):
    from http.client import HTTPConnection
    import json
    import threading
    from src import imageConverterGui as gui
    recognizer, _, source, svg, _ = reference
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    server = gui.GuiServer(('127.0.0.1', 0), jobs)
    jobs.recognizer = recognizer
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(path, method='GET', data=None):
        connection = HTTPConnection(*server.server_address, timeout=10)
        try:
            connection.request(method, path, body=data, headers={'X-ImageConverter': '1'})
            response = connection.getresponse()
            return response.status, response.read(), response.getheader('Content-Type')
        finally:
            connection.close()
    try:
        uploaded = jobs.upload('renamed.png', source.read_bytes())
        status, body, _ = request(f"/api/jobs/{uploaded['id']}/recognize", 'POST', b'{}')
        assert status == 200
        result = json.loads(body)
        assert result['description_origin'] == 'recognition'
        match = result['recognition']['matches'][0]
        status, body, mime = request(match['source_url'])
        assert status == 200 and body.startswith(b'\x89PNG') and mime == 'image/png'
        assert request(match['svg_url'])[:2] == (200, svg.read_bytes())
        assert request('/api/recognition/reference/'+'0'*64+'/svg')[0] == 404
        assert json.loads(request('/api/config')[1])['image_recognition']
        status, body, _ = request(f"/api/jobs/{uploaded['id']}/description", 'POST',
                                  json.dumps(dict(description='Meine Korrektur: ein grauer Kreis.')).encode())
        assert status == 200 and json.loads(body)['description_origin'] == 'user'
        assert json.loads(body)['description_save']['scope'] == 'image'
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_plain_shape_recognition_reaches_real_converter_without_user_description(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    # No reference pictures: this must come from the unknown raster itself.
    jobs.recognizer = ImageRecognition(tmp_path, lambda: dict(rows=[]))
    try:
        uploaded = jobs.upload('unbekannte-grundform.png', image_bytes(symbol()))
        recognized = jobs.recognize(uploaded['id'])
        assert recognized['recognition']['automatic']['kind'] == 'plain_shape'
        assert recognized['recognition']['reference_count'] == 0
        started = jobs.start(uploaded['id'], recognized['description'], 'quick', seed=1234)
        jobs.threads[-1].join(timeout=75)
        result = jobs.snapshot(started['id'])
        assert result['status'] == 'done' and result['quality'] == 'passed', result
        assert result['pixel_quality']['passed']
        assert result['description_origin'] == 'recognition'
    finally:
        jobs.close()
