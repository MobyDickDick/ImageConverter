"""A geometric group must not turn missing prose or old SVGs into success."""
import copy
import json
from pathlib import Path

import pytest

from src.imageConverterClasses import (CLASSES, annotate_rows, classify_description,
                                       enrich_catalog, text_hash)
from tools.build_catalog_classes import build_classes, write_classes
from tools.build_catalog_inventory import build, write_report
from tests.test_catalog_inventory import prepare, quality


def test_placeholder_shape_suggestions_are_not_observed_geometry():
    text = ('Unzugeordnete Wurzelform. Grundkörper wie Kreis/Ellipse/Rechteck/Polygon, '
            'danach Leitungen/Griffe/Dreiecke und Zeichenkette. Manuell prüfen.')
    result = classify_description(text)
    assert result['class_id'] == 'unresolved'
    assert result['description_issue'] == 'placeholder'
    assert result['conversion_proven'] is False
    assert classify_description('')['class_id'] == 'unresolved'


def test_visual_evidence_expires_for_either_changed_source_or_description():
    text = 'Unzugeordnete Wurzelform.'
    visual = dict(class_id='disk_label', observation='Runde Kontur mit Q und Griff.',
                  image_sha256='original', description_sha256=text_hash(text))
    assert classify_description(text, visual=visual, image_sha256='original')['class_id'] == 'disk_label'
    assert classify_description(text, visual=visual, image_sha256='changed')['class_id'] == 'unresolved'
    assert classify_description(text+' Neu.', visual=visual, image_sha256='original')['class_id'] == 'unresolved'
    assert classify_description(text, visual=visual, image_sha256='original', reserved=True)['class_id'] == 'reserved'


def test_negative_text_claim_does_not_create_labeled_circle():
    assert classify_description('Ein Kreis ohne Text mit waagerechtem Balken.')['class_id'] == 'disk_marks'
    assert classify_description('Ein Kreis mit dem Buchstaben Q.')['class_id'] == 'disk_label'
    # Failure and complexity cannot be inferred from vague prose.
    assert classify_description('sehr komplexe Form, wahrscheinlich schwierig')['class_id'] == 'unresolved'


def test_classification_preserves_measurements_and_never_promotes_pixel_failure():
    row = dict(filename='neutral.jpg', role='catalog', image_sha256='bytes',
               description='Ein Kreis mit dem Buchstaben Q.', status='pixel_fail',
               archived=False, candidates=[dict(measurement=quality(False))], selected=None)
    original = copy.deepcopy(row)
    summary = annotate_rows([row])
    assert {k: row[k] for k in original} == original
    assert row['classification']['conversion_proven'] is False
    assert summary['assigned'] == summary['catalog_bitmaps'] == 1
    assert summary['classes']['disk_label']['saved_pixel_pass'] == 0


def test_alias_cycles_are_bounded_and_neutral_names_do_not_change_geometry(tmp_path):
    prepare(tmp_path, desc='Wie AA0020')
    xml = tmp_path/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'
    xml.write_text('<root><entry key="AA0020"><beschreibung>Ein Kreis mit Buchstabe Q. Wie AA0030.</beschreibung></entry>'
                   '<entry key="AA0030"><beschreibung>Wie AA0020.</beschreibung></entry></root>', encoding='utf-8')
    rows = [dict(filename=name, description='Wie AA0020', status='no_svg')
            for name in ('neutral.jpg', 'AC9999_L.jpg')]
    enrich_catalog(tmp_path, rows)
    assert rows[0]['classification']['class_id'] == rows[1]['classification']['class_id'] == 'disk_label'
    assert len(rows[0]['classification_description']) < 1000


def test_full_rebuild_uses_current_sources_and_invalidates_stale_quality(tmp_path):
    prepare(tmp_path, desc='Ein Rechteck mit Kontur.')
    rows, summary, _ = build(tmp_path, measure=lambda *args: quality())
    write_report(tmp_path, tmp_path/'artifacts/catalog_inventory', rows, summary, {})
    current, summary = build_classes(tmp_path)
    assert current[0]['status'] == 'pixel_pass'
    assert current[0]['classification']['class_id'] == 'panel_plain'
    (tmp_path/'artifacts/images_to_convert/AA0010.jpg').write_bytes(b'new bitmap')
    current, summary = build_classes(tmp_path)
    assert current[0]['status'] == 'unmeasured'
    assert summary['classes']['panel_plain']['saved_pixel_pass'] == 0
    assert current[0]['selected_svg'] is None
    output = tmp_path/'classes'
    write_classes(tmp_path, output, current, summary)
    assert 'AA0010.jpg' in (output/'index.html').read_text(encoding='utf-8')
    assert 'class_label' in (output/'classes.csv').read_text(encoding='utf-8-sig')
    assert json.loads((output/'manifest.json').read_text(encoding='utf-8'))['summary']['fresh_conversion_performed'] is False


def test_every_model_reference_names_an_existing_implementation():
    root = Path(__file__).resolve().parents[1]
    for _, modules, _ in CLASSES.values():
        for module in modules:
            assert (root/'src/iCCModules'/('imageCompositeConverter'+module+'.py')).is_file(), module


def test_live_catalog_exports_class_and_keeps_quality_timestamp(tmp_path):
    from src.imageConverterCatalog import CatalogQuality
    prepare(tmp_path, desc='Ein Kreis mit Text Q.')
    rows, summary, _ = build(tmp_path, measure=lambda *args: quality(False))
    write_report(tmp_path, tmp_path/'artifacts/catalog_inventory', rows, summary, {})
    manager = CatalogQuality(tmp_path, tmp_path/'jobs', lambda *args: None)
    payload = manager.payload()
    assert payload['summary']['generated_at'] == summary['generated_at']
    assert payload['rows'][0]['status'] == 'pixel_fail'
    assert payload['rows'][0]['classification']['class_id'] == 'disk_label'
    assert 'disk_label' in manager.export_csv().decode('utf-8-sig')
    manager.close()


def test_source_only_visual_assignment_survives_a_description_correction():
    visual = dict(class_id='disk_label', observation='Kreis mit Q.', independent_of_description=True,
                  image_sha256='original', description_sha256=text_hash('Falsche Beschreibung.'))
    result = classify_description('Korrigierte Beschreibung.', visual=visual, image_sha256='original')
    assert result['class_id'] == 'disk_label'
    assert result['basis'] == 'visual_audit'
    assert classify_description('Korrigierte Beschreibung.', visual=visual, image_sha256='new')['basis'] != 'visual_audit'


def visual_review_fixture(root):
    from PIL import Image, ImageDraw
    from tools.build_catalog_inventory import digest
    from tools.prepare_catalog_class_review import prepare as prepare_review
    (root/'config').mkdir()
    (root/'config/catalog_class_visual_review.json').write_text(json.dumps(dict(cases={})), encoding='utf-8')
    rows=[]
    for name in ('neutral_a.png','neutral_b.png'):
        path=root/name
        image=Image.new('RGB',(40,40),'white')
        ImageDraw.Draw(image).ellipse((5,5,34,34),outline='gray',width=2)
        image.save(path)
        rows.append(dict(filename=name,image=name,role='catalog',description='Kreis.',
                         image_sha256=digest(path.read_bytes()),classification=dict(basis='description_rule')))
    # A reserved input must be excluded before trying to decode its bytes.
    (root/'sealed.png').write_bytes(b'not an image; must never be decoded')
    rows.append(dict(filename='sealed.png',image='sealed.png',role='catalog',description='Reserved',
                     image_sha256='do_not_read',classification=dict(basis='description_rule')))
    reservation=root/'config/real_composition_holdout_test.json'
    reservation.write_text(json.dumps(dict(evaluation_policy=dict(status='sealed_unrun'),cases=[dict(file='sealed.png')])),encoding='utf-8')
    manifest=root/'catalog.json'
    manifest.write_text(json.dumps(dict(rows=rows)),encoding='utf-8')
    sheets=root/'sheets'
    prepared=prepare_review(root,manifest,sheets)
    assert prepared['count'] == 2
    decisions=root/'decisions.json'
    decisions.write_text(json.dumps(dict(pages={'0':[[0,1,'disk_plain','circle','Runde Kontur ohne Innenzeichen.']]})),encoding='utf-8')
    return manifest,sheets,decisions,reservation


def test_review_is_complete_pinned_and_replayable(tmp_path):
    from tools.apply_catalog_class_review import apply
    from tools.prepare_catalog_class_review import prepare as prepare_review
    manifest,sheets,decisions,_=visual_review_fixture(tmp_path)
    result=apply(tmp_path,sheets,decisions,complete=True)
    assert len(result['cases']) == 2
    assert result['full_catalog_review']['complete'] is True
    assert result['cases']['neutral_a.png']['review_evidence']['cell'] == 0
    assert result['cases']['neutral_b.png']['independent_of_description'] is True
    replay=prepare_review(tmp_path,manifest,tmp_path/'replay',replay=sheets/'manifest.json')
    original=json.loads((sheets/'manifest.json').read_text(encoding='utf-8'))
    assert replay['pages'][0]['sheet_sha256'] == original['pages'][0]['sheet_sha256']


@pytest.mark.parametrize('failure',['gap','duplicate','changed_source','new_reservation'])
def test_review_rejects_gaps_duplicates_changed_pixels_and_new_seals(tmp_path,failure):
    from tools.apply_catalog_class_review import apply
    _,sheets,decisions,reservation=visual_review_fixture(tmp_path)
    before=(tmp_path/'config/catalog_class_visual_review.json').read_bytes()
    data=json.loads(decisions.read_text(encoding='utf-8'))
    if failure == 'gap':
        data['pages']['0'][0][1]=0
    elif failure == 'duplicate':
        data['pages']['0'].append([0,0,'disk_plain','circle','Duplicate.'])
    elif failure == 'changed_source':
        (tmp_path/'neutral_b.png').write_bytes(b'changed pixels')
    else:
        reservation.write_text(json.dumps(dict(evaluation_policy=dict(status='sealed_unrun'),cases=[dict(file='neutral_b.png')])),encoding='utf-8')
    decisions.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(ValueError):
        apply(tmp_path,sheets,decisions,complete=True)
    assert (tmp_path/'config/catalog_class_visual_review.json').read_bytes() == before
