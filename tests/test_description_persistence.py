"""Text edits survive without conversion and update only the matching original."""
import os
import time

from PIL import Image
import pytest

from src import imageConverterGui as gui
from src.imageConverterDescriptionStore import DescriptionStore
from src.imageConverterRecognition import pixel_digest, rgb_image
from src.iCCModules.imageCompositeConverterDescriptions import loadCatalogDescriptionMappingImpl


@pytest.fixture
def store(tmp_path):
    source = tmp_path/'artifacts/images_to_convert/AC1234_M.png'
    source.parent.mkdir(parents=True)
    Image.new('RGB', (32, 24), 'blue').save(source)
    xml = ('<?xml version="1.0" encoding="utf-8"?>\r\n<root>\r\n'
           '  <entry key="AC1234"><beschreibung>Alte Familienbeschreibung.</beschreibung>'
           '<bilder><bild>AC1234_M.png</bild><bild>AC1234_S.png</bild></bilder></entry>\r\n</root>\r\n')
    for folder in ('images_to_convert', 'descriptions'):
        path = tmp_path/'artifacts'/folder/'Finale_Wurzelformen_V3.xml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(xml.encode())
    return DescriptionStore(tmp_path), source, pixel_digest(rgb_image(source))


def test_save_exact_image_to_both_tables_preserving_family_siblings_and_layout(store):
    writer, source, digest = store
    description = 'Links rot, rechts blau.\nText "A & B" <oben>. Alle Linien sind gleich breit.'
    result = writer.save(source.name, digest, description)
    assert result['scope'] == 'catalog' and len(result['files']) == 2
    mapping = loadCatalogDescriptionMappingImpl(writer.root)
    assert mapping['AC1234_M.PNG'] == description
    assert mapping['AC1234_S.PNG'] == 'Alte Familienbeschreibung.'
    assert mapping['AC1234'] == 'Alte Familienbeschreibung.'
    data = (writer.root/result['files'][0]).read_bytes()
    assert b'\r\n' in data and data.endswith(b'\r\n')
    assert b'beschreibung_modus="ersetzen"' in data
    assert writer.save(source.name, digest, 'Ein blaues Rechteck.')['scope'] == 'catalog'
    assert loadCatalogDescriptionMappingImpl(writer.root)['AC1234_M.PNG'] == 'Ein blaues Rechteck.'


def test_same_filename_with_different_pixels_does_not_change_catalog(store):
    writer, source, _ = store
    result = writer.save(source.name, pixel_digest(Image.new('RGB', (32, 24), 'red')), 'Ein rotes Rechteck.')
    assert result['scope'] == 'image'
    assert loadCatalogDescriptionMappingImpl(writer.root)['AC1234_M.PNG'] == 'Alte Familienbeschreibung.'


def test_empty_edit_stays_local_and_path_traversal_cannot_touch_table(store):
    writer, source, digest = store
    for name, text in [(source.name, ''), ('../'+source.name, 'Kreis')]:
        assert writer.save(name, digest, text)['scope'] == 'image'
    assert loadCatalogDescriptionMappingImpl(writer.root)['AC1234_M.PNG'] == 'Alte Familienbeschreibung.'


def test_autosave_without_conversion_survives_restart_and_renamed_upload(tmp_path, monkeypatch, store):
    writer, source, _ = store
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.description_store = writer
    try:
        uploaded = jobs.upload(source.name, source.read_bytes())
        saved = jobs.save_description(uploaded['id'], 'Ein blaues Rechteck.\nKorrigiert ohne Konvertierung.')
        assert saved['status'] == 'ready' and not jobs.threads
        assert saved['description_origin'] == 'user'
        assert saved['description_save']['scope'] == 'catalog'
        reloaded = gui.Jobs(jobs.directory)
        try:
            assert reloaded.snapshot(saved['id'])['description'] == saved['description']
            assert reloaded.upload('anderer-name.png', source.read_bytes())['description'] == saved['description']
        finally:
            reloaded.close()
    finally:
        jobs.close()


def test_edit_completed_result_creates_new_ready_revision_and_leaves_result_intact(tmp_path, monkeypatch, store):
    writer, source, _ = store
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.description_store = writer
    try:
        uploaded = jobs.upload(source.name, source.read_bytes())
        original = jobs.jobs[uploaded['id']]
        original.update(status='done', description='Alter Text.', quality='warning')
        jobs.save(original)
        revised = jobs.save_description(original['id'], 'Ein blaues Rechteck.')
        assert revised['id'] != original['id'] and revised['status'] == 'ready'
        assert original['description'] == 'Alter Text.' and original['status'] == 'done'
        # Editing an older revision later wins over a newer upload's creation date.
        jobs.upload('renamed.png', source.read_bytes())
        jobs.save_description(revised['id'], 'Nochmals korrigiert. Ein blaues Rechteck.')
        assert jobs.upload('again.png', source.read_bytes())['description'].startswith('Nochmals korrigiert.')
        cleared = jobs.save_description(revised['id'], '')
        assert cleared['description'] == '' and jobs.snapshot(cleared['id'])['description'] == ''
        original['status'] = 'running'
        with pytest.raises(gui.RequestError):
            jobs.save_description(original['id'], 'Nicht während der Konvertierung')
        original['status'] = 'done'
    finally:
        jobs.close()


def test_recovery_uses_only_latest_recent_explicit_user_corrections(store):
    writer, source, digest = store
    primary = writer.root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'
    timestamp = time.time()
    os.utime(primary, (timestamp-10, timestamp-10))
    base = dict(name=source.name, source_sha256=digest, created=timestamp-50, description_origin='user')
    jobs = [dict(base, id='old', started=timestamp-30, description='Ein graues Rechteck.'),
            dict(base, id='new', started=timestamp, description='Ein blaues Rechteck.')]
    assert writer.recover(jobs)[0]['job_id'] == 'new'
    assert loadCatalogDescriptionMappingImpl(writer.root)['AC1234_M.PNG'] == 'Ein blaues Rechteck.'
    assert writer.recover(jobs) == []


def test_catalog_write_failure_keeps_locally_saved_text_and_reports_warning(tmp_path, monkeypatch, store):
    writer, source, _ = store
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.description_store = writer
    try:
        uploaded = jobs.upload(source.name, source.read_bytes())
        (writer.root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').write_text('<broken')
        saved = jobs.save_description(uploaded['id'], 'Ein blaues Rechteck.')
        assert saved['description_save']['warning']
        assert jobs.snapshot(saved['id'])['description'] == 'Ein blaues Rechteck.'
    finally:
        jobs.close()


def test_conversion_start_also_persists_correction_without_prior_autosave(tmp_path, monkeypatch, store):
    writer, source, _ = store
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.description_store = writer
    monkeypatch.setattr(jobs, 'run', lambda job_id: None)
    try:
        uploaded = jobs.upload(source.name, source.read_bytes())
        started = jobs.start(uploaded['id'], 'Ein blaues Rechteck.', 'quick')
        assert started['description_save']['scope'] == 'catalog'
        assert loadCatalogDescriptionMappingImpl(writer.root)['AC1234_M.PNG'] == 'Ein blaues Rechteck.'
    finally:
        jobs.close()
