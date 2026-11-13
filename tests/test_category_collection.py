"""A representative is an original input, never a silently reused saved SVG."""
from http.client import HTTPConnection
import json
from pathlib import Path
import threading

from PIL import Image, ImageDraw
import pytest

from src import imageConverterGui as gui
from src.imageConverterCatalog import CatalogError, CatalogQuality
from src.imageConverterCollection import CategoryCollection
from tools.build_catalog_inventory import build, digest, write_report
from tests.test_catalog_inventory import prepare, quality


@pytest.fixture
def collection(tmp_path, monkeypatch):
    root=tmp_path/'repo'
    prepare(root,desc='Ein Kreis mit dem Buchstaben Q.')
    image=Image.new('RGB',(40,40),'white')
    ImageDraw.Draw(image).ellipse((5,5,34,34),outline='gray',width=2)
    source=root/'artifacts/images_to_convert/AA0010.jpg'
    image.save(source)
    rows,summary,_=build(root,measure=lambda *args:quality())
    write_report(root,root/'artifacts/catalog_inventory',rows,summary,{})
    (root/'config').mkdir(exist_ok=True)
    selected=dict(id='disk_label',filename='AA0010.jpg',image_sha256=digest(source.read_bytes()))
    (root/'config/catalog_conversion_collection.json').write_text(json.dumps(dict(cases=[selected])),encoding='utf-8')
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{'AA0010':'Ein Kreis mit dem Buchstaben Q.'})
    jobs=gui.Jobs(tmp_path/'jobs')
    catalog=CatalogQuality(root,tmp_path/'measurements',lambda *args:None)
    manager=CategoryCollection(root,catalog,jobs)
    yield manager
    jobs.close();catalog.close()


def test_stored_pixel_pass_does_not_claim_a_new_conversion(collection):
    payload=collection.payload()
    assert payload['summary']['categories_with_saved_pass']==1
    assert payload['summary']['fresh_passes']==0
    job=collection.load('disk_label')
    assert job['status']=='ready' and job['quality']=='unknown'
    assert not job['result'] and not job.get('sample')
    assert job['description']=='Ein Kreis mit dem Buchstaben Q.'
    assert job['collection_case_id']=='disk_label'
    assert not (collection.jobs.folder(job['id'])/'sample.svg').exists()


def test_reopening_is_idempotent_and_explicit_fresh_attempt_is_separate(collection):
    first=collection.load('disk_label')
    assert collection.load('disk_label')['id']==first['id']
    next_job=collection.load('disk_label',fresh=True)
    assert next_job['id']!=first['id']
    assert collection.payload()['cases'][0]['attempt_count']==2
    assert collection.jobs.snapshot(first['id'])['status']=='ready'


def test_selected_catalog_description_beats_secondary_table_but_keeps_user_edits(collection):
    collection.jobs.descriptions={'AA0010':'Veraltete Beschreibung aus einer anderen Tabelle.'}
    first=collection.load('disk_label')
    assert first['description']=='Ein Kreis mit dem Buchstaben Q.'
    collection.jobs.jobs[first['id']].update(description='Meine korrigierte Beschreibung.',description_origin='user')
    collection.jobs.save(collection.jobs.jobs[first['id']])
    retry=collection.load('disk_label',fresh=True)
    assert retry['description']=='Meine korrigierte Beschreibung.'


def test_retries_keep_collection_identity_and_passes_remain_when_later_attempt_fails(collection):
    first=collection.load('disk_label')
    stored=collection.jobs.jobs[first['id']]
    stored.update(status='done',quality='passed',result=True,pixel_quality=dict(passed=True))
    collection.jobs.save(stored)
    with collection.jobs.lock:
        retry=collection.jobs.editable(first['id'])
        retry.update(status='done',quality='warning',result=True)
        collection.jobs.save(retry)
    case=collection.payload()['cases'][0]
    assert case['latest_job']['id']==retry['id']
    assert case['passed_job']['id']==first['id']
    assert case['attempt_count']==2
    assert collection.payload()['summary']['fresh_passes']==1


def test_collection_provenance_survives_restart(collection):
    job=collection.load('disk_label')
    restarted=gui.Jobs(collection.jobs.directory)
    restored=CategoryCollection(collection.root,collection.catalog,restarted)
    assert restored.payload()['cases'][0]['latest_job']['id']==job['id']
    restarted.close()


def test_prepared_plan_b_stays_accessible_after_another_success(collection):
    first=collection.load('disk_label')
    collection.jobs.jobs[first['id']].update(status='done',quality='passed',result=True,workbench_id='a'*32)
    collection.jobs.save(collection.jobs.jobs[first['id']])
    second=collection.load('disk_label',fresh=True)
    collection.jobs.jobs[second['id']].update(status='done',quality='passed',result=True)
    collection.jobs.save(collection.jobs.jobs[second['id']])
    payload=collection.payload()
    assert payload['summary']['prepared_plan_b']==1
    assert payload['cases'][0]['passed_job']['id']==second['id']
    assert payload['cases'][0]['plan_b_job']['id']==first['id']


@pytest.mark.parametrize('problem',['changed','reserved','wrong_class'])
def test_changed_reserved_or_reclassified_sources_cannot_be_loaded(collection,problem):
    if problem=='changed':
        source=collection.root/'artifacts/images_to_convert/AA0010.jpg'
        source.write_bytes(b'changed')
    elif problem=='reserved':
        (collection.root/'config/real_composition_holdout_new.json').write_text(json.dumps(dict(
            evaluation_policy=dict(status='sealed_unrun'),cases=[dict(file='AA0010.jpg')])),encoding='utf-8')
    else:
        collection.catalog.payload()['rows'][0]['classification']['class_id']='panel_plain'
    assert collection.payload()['cases'][0]['available'] is False
    with pytest.raises(CatalogError):
        collection.load('disk_label')
    assert not collection.jobs.jobs


def test_arbitrary_ids_and_invalid_flags_are_rejected(collection):
    with pytest.raises(CatalogError):collection.load('../../private')
    with pytest.raises(CatalogError):collection.load('disk_label',fresh='yes')


def test_full_selection_has_one_example_per_noncomplex_geometric_category():
    from src.imageConverterClasses import CLASSES
    root=Path(__file__).resolve().parents[1]
    cases=json.loads((root/'config/catalog_conversion_collection.json').read_text(encoding='utf-8'))['cases']
    assert {c['id'] for c in cases}==set(CLASSES)-{'complex_photo','reserved','unresolved'}
    assert len(cases)==len({c['filename'] for c in cases})==15


def test_collection_http_routes_use_the_existing_job_and_plan_b_gates(collection):
    server=gui.GuiServer(('127.0.0.1',0),collection.jobs)
    server.catalog.close()
    server.catalog=collection.catalog
    server.collection=collection
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    def request(path,method='GET',body=None,authorized=True):
        connection=HTTPConnection(*server.server_address,timeout=5)
        try:
            headers={'Content-Type':'application/json'}
            if authorized:headers['X-ImageConverter']='1'
            connection.request(method,path,body=json.dumps(body) if body is not None else None,headers=headers)
            response=connection.getresponse()
            return response.status,response.read()
        finally:connection.close()
    try:
        assert request('/collection')[0]==200
        assert request('/collection.js')[0]==200
        assert request('/api/collection')[0]==200
        assert request('/api/collection/disk_label/load','POST',{},False)[0]==403
        code,body=request('/api/collection/disk_label/load','POST',{})
        job=json.loads(body)
        assert code==201 and job['status']=='ready'
        assert request('/api/jobs/'+job['id'])[0]==200
        assert request('/api/jobs/'+job['id']+'/workbench','POST',{})[0]==409
        assert request('/api/collection/not_a_case/load','POST',{})[0]==404
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close()
