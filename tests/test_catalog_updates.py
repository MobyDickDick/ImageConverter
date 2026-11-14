"""Manual GUI successes update the live catalog, including concurrent reports."""
import copy
import json
import sys
import time

from PIL import Image
import pytest

from src import imageConverterGui as gui
from src.imageConverterCatalogUpdates import CatalogUpdates
from tools import build_catalog_inventory as inventory
from test_catalog_quality_server import catalog
from test_catalog_inventory import SVG, quality


def wait_until(predicate, timeout=10):
    end = time.monotonic()+timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(.02)
    assert predicate()


@pytest.fixture
def manual(catalog, tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'gui')
    uploaded = jobs.upload('AA0010.jpg', (catalog.root/'artifacts/images_to_convert/AA0010.jpg').read_bytes())
    job = jobs.jobs[uploaded['id']]
    job.update(status='done', result=True, quality='passed')
    (jobs.folder(job['id'])/'result.svg').write_text(SVG+'\n', encoding='utf-8')
    jobs.save(job)
    rows, summary, _ = inventory.build(catalog.root, measure=lambda *args: quality(False, .05))
    inventory.write_report(catalog.root, catalog.report_folder(), rows, summary, {})
    yield jobs, job
    jobs.close()


@pytest.mark.parametrize('both_pass', [False, True])
def test_backfill_checks_both_renderers_and_survives_reload(catalog, manual, monkeypatch, both_pass):
    jobs, job = manual
    result = quality(True)
    result['renderers']['librsvg']['satisfactory'] = both_pass
    monkeypatch.setattr(inventory.QualityWorker, 'measure', lambda *args: copy.deepcopy(result))
    manager = CatalogUpdates(catalog, jobs)
    try:
        wait_until(lambda: job.get('catalog_update', {}).get('status') == 'done')
        row = catalog.payload()['rows'][0]
        assert row['status'] == ('pixel_pass' if both_pass else 'pixel_fail')
        assert len(row['candidates']) == 2
        assert 'catalog_manual_svgs' in row['selected']['svg']
        assert job['catalog_update']['catalog_status'] == row['status']
        assert catalog.payload()['summary']['catalog_statuses'] == {row['status']: 1}
        assert catalog.asset(row['selected']['svg']).is_file()
        assert 'catalog_manual_svgs' in catalog.export_csv().decode('utf-8-sig')
        reloaded = gui.CatalogQuality(catalog.root, catalog.directory, gui.stop_process_tree)
        assert reloaded.payload()['rows'][0]['status'] == row['status']
        assert reloaded.manual_candidates
        reloaded.close()
    finally:
        manager.close()


def test_real_both_renderer_measurement_updates_manual_success(catalog, manual):
    jobs, job = manual
    manager = CatalogUpdates(catalog, jobs)
    try:
        wait_until(lambda: job.get('catalog_update', {}).get('status') == 'done', timeout=45)
        row = catalog.payload()['rows'][0]
        assert row['status'] == 'pixel_pass', row['selected']['measurement']
        assert set(row['selected']['measurement']['renderers']) == {'mupdf', 'librsvg'}
    finally:
        manager.close()


def test_slower_catalog_report_cannot_overwrite_manual_admission(catalog, manual, monkeypatch, tmp_path):
    jobs, job = manual
    # The background process has already read the older failing report.
    stale = (catalog.report_folder()/'manifest.json').read_text(encoding='utf-8')
    worker = tmp_path/'publish.py'
    worker.write_text('''import pathlib, sys, time
folder=pathlib.Path(sys.argv[1]); (folder/'ready').touch()
while not (folder/'release').exists(): time.sleep(.02)
(folder/'report').mkdir(); (folder/'report/manifest.json').write_text(sys.argv[2], encoding='utf-8')
''', encoding='utf-8')
    monkeypatch.setattr(catalog, 'command', lambda folder, *args: [sys.executable, str(worker), str(folder), stale])
    started = catalog.start()
    folder = catalog.directory/started['id']
    wait_until(lambda: (folder/'ready').exists())
    monkeypatch.setattr(inventory.QualityWorker, 'measure', lambda *args: quality(True))
    manager = CatalogUpdates(catalog, jobs)
    try:
        wait_until(lambda: job.get('catalog_update', {}).get('status') == 'done')
        assert catalog.payload()['rows'][0]['status'] == 'pixel_pass'
        (folder/'release').touch()
        catalog.thread.join(10)
        assert catalog.snapshot()['status'] == 'done'
        assert catalog.payload()['rows'][0]['status'] == 'pixel_pass'
        assert len(catalog.payload()['rows'][0]['candidates']) == 2
    finally:
        (folder/'release').touch()
        manager.close()


def test_same_filename_with_different_pixels_cannot_change_catalog(catalog, manual, monkeypatch):
    jobs, job = manual
    Image.new('RGB', (40,40), 'red').save(jobs.folder(job['id'])/'source.png')
    monkeypatch.setattr(inventory.QualityWorker, 'measure', lambda *args: pytest.fail('Wrong source must not be measured'))
    manager = CatalogUpdates(catalog, jobs)
    try:
        wait_until(lambda: job.get('catalog_update', {}).get('status') == 'error')
        assert 'Katalogoriginal' in job['catalog_update']['message']
        assert catalog.payload()['rows'][0]['status'] == 'pixel_fail'
        assert not catalog.manual_candidates
    finally:
        manager.close()


def test_finished_new_attempt_is_submitted_without_waiting_for_restart(catalog, manual, monkeypatch):
    jobs, old = manual
    old.update(quality='warning')  # The manager must ignore drafts at startup.
    monkeypatch.setattr(inventory.QualityWorker, 'measure', lambda *args: quality(True))
    manager = CatalogUpdates(catalog, jobs)
    try:
        new = jobs.upload('AA0010.jpg', (jobs.folder(old['id'])/'source.png').read_bytes())
        job = jobs.jobs[new['id']]
        job.update(status='done', result=True, quality='passed')
        (jobs.folder(job['id'])/'result.svg').write_text(SVG+'\n', encoding='utf-8')
        jobs.on_result(job['id'])
        wait_until(lambda: job.get('catalog_update', {}).get('status') == 'done')
        assert 'catalog_update' not in old
        assert catalog.payload()['rows'][0]['status'] == 'pixel_pass'
    finally:
        manager.close()


def test_new_reservation_blocks_replaying_an_older_manual_measurement(catalog, manual, monkeypatch):
    jobs, job = manual
    stale = json.loads((catalog.report_folder()/'manifest.json').read_text(encoding='utf-8'))
    monkeypatch.setattr(inventory.QualityWorker, 'measure', lambda *args: quality(True))
    manager = CatalogUpdates(catalog, jobs)
    try:
        wait_until(lambda: job.get('catalog_update', {}).get('status') == 'done')
        config = catalog.root/'config'
        config.mkdir(exist_ok=True)
        (config/'real_composition_holdout_new.json').write_text(json.dumps(dict(
            evaluation_policy=dict(status='sealed_unrun'), cases=[dict(file='AA0010.jpg')])))
        _, changed = catalog._merge_manual_candidates(stale)
        assert not changed
        assert catalog.payload()['rows'][0]['status'] == 'reserved'
    finally:
        manager.close()
