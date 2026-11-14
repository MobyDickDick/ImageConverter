"""The project overview must not promote filenames or stale archive metrics."""
from pathlib import Path
import json
from xml.etree import ElementTree as ET

import pytest

from tools.build_catalog_inventory import (QualityWorker, build, classify, digest,
                                          inside, write_report, update_candidate)


SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
       '<rect width="40" height="40" fill="white"/>'
       '<rect x="8" y="8" width="24" height="24" fill="#555555"/></svg>')


def prepare(root, *, archived=False, reserved=False, desc='Graues Rechteck.'):
    images = root/'artifacts/images_to_convert'
    images.mkdir(parents=True)
    (images/'AA0010.jpg').write_bytes(b'original JPEG bytes')
    xml = ET.Element('root')
    entry = ET.SubElement(xml, 'entry', key='AA0010')
    ET.SubElement(entry, 'beschreibung').text = desc
    ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = 'AA0010.jpg'
    ET.ElementTree(xml).write(images/'Finale_Wurzelformen_V3.xml', encoding='utf-8')
    output = root/'artifacts/converted_images/converted_svgs'
    output.mkdir(parents=True)
    (output/'aa0010.svg').write_text(SVG, encoding='utf-8')
    if archived:
        archive = root/'artifacts/satisfactory_conversions'
        (archive/'images').mkdir(parents=True)
        (archive/'svgs').mkdir()
        (archive/'images/AA0010.jpg').write_bytes(b'original JPEG bytes')
        (archive/'svgs/AA0010.svg').write_text(SVG, encoding='utf-8')
        case = dict(variant='AA0010', description=desc, image='images/AA0010.jpg',
            svg='svgs/AA0010.svg', image_sha256=digest(b'original JPEG bytes'),
            svg_sha256=digest(SVG.encode()), evidence='artifacts/proof.json',
            execution_mode='semantic-only', metrics=dict(error_per_pixel=0.))
        (archive/'index.json').write_text(json.dumps(dict(cases=[case])))
    if reserved:
        (root/'config').mkdir()
        (root/'config/real_composition_holdout_families.json').write_text(json.dumps(dict(
            evaluation_policy=dict(status='sealed_unrun'), cases=[dict(file='AA0010.jpg')])) )


def quality(passed=True, mse=.001):
    return dict(measured_at='2026-11-07T00:00:00+00:00', renderers={name:dict(
        satisfactory=passed, metrics=dict(normalized_mse=mse), failures=[] if passed else ['foreground_iou_outside_limit'])
        for name in ('mupdf', 'librsvg')})


def test_archive_admission_and_fresh_pixel_checks_remain_distinct(tmp_path):
    prepare(tmp_path, archived=True)
    rows, summary, _ = build(tmp_path, measure=lambda *args: quality(False))
    assert summary['catalog_bitmaps'] == summary['archived'] == summary['archive_pinned_pairs_valid'] == 1
    assert summary['archived_current_pixel_pass'] == 0
    assert rows[0]['status'] == 'pixel_fail'
    assert rows[0]['semantic_revalidated'] is False
    assert len(rows[0]['candidates']) == 1  # Identical SVG copies measured once.
    assert len(rows[0]['candidates'][0]['all_paths']) == 2
    assert summary['archive_missing_evidence'] == 1


def test_changed_source_and_description_are_not_hidden_by_archive_membership(tmp_path):
    prepare(tmp_path, archived=True)
    image = tmp_path/'artifacts/images_to_convert/AA0010.jpg'
    image.write_bytes(b'changed source')
    xml_path = image.parent/'Finale_Wurzelformen_V3.xml'
    tree = ET.parse(xml_path)
    tree.find('.//beschreibung').text = 'Neue Beschreibung.'
    tree.write(xml_path, encoding='utf-8')
    rows, summary, _ = build(tmp_path, measure=lambda *args: quality())
    assert rows[0]['status'] == 'pixel_pass'
    assert rows[0]['archive']['source_matches'] is False
    assert summary['archive_pinned_pairs_valid'] == 0
    assert summary['archive_description_differences'] == 1


@pytest.mark.parametrize('reserved,conflict', [(True, False), (False, True)])
def test_reserved_inputs_and_conflicting_source_copies_are_never_measured(tmp_path, reserved, conflict):
    prepare(tmp_path, reserved=reserved)
    if conflict:
        folder = tmp_path/'artifacts/images_to_convert/nonconvertable'
        folder.mkdir()
        (folder/'AA0010.jpg').write_bytes(b'contradictory copy')
    rows, _, _ = build(tmp_path, measure=lambda *args: pytest.fail('Forbidden measurement'))
    assert rows[0]['status'] == ('reserved' if reserved else 'source_conflict')


def test_additional_sealed_family_manifest_also_blocks_catalog_measurement(tmp_path):
    prepare(tmp_path,reserved=True)
    source=tmp_path/'config/real_composition_holdout_families.json'
    source.rename(tmp_path/'config/real_composition_holdout_fallback_groups.json')
    rows,_,_=build(tmp_path,measure=lambda *args:pytest.fail('Sealed new families must not run'))
    assert rows[0]['status']=='reserved'


def test_missing_svg_means_unknown_and_auxiliary_gifs_do_not_inflate_catalog(tmp_path):
    prepare(tmp_path)
    (tmp_path/'artifacts/converted_images/converted_svgs/aa0010.svg').unlink()
    (tmp_path/'artifacts/images_to_convert/top.gif').write_bytes(b'UI asset')
    rows, summary, _ = build(tmp_path, measure=lambda *args: pytest.fail('No SVG to measure'))
    assert summary['catalog_bitmaps'] == 1 and summary['auxiliary_bitmaps'] == 1
    assert summary['catalog_statuses'] == dict(no_svg=1)
    assert {r['status'] for r in rows} == {'no_svg', 'auxiliary'}


def test_cache_requires_image_svg_and_runtime_signature_and_errors_are_retried(tmp_path):
    prepare(tmp_path)
    calls, cache = [], {}
    def measure(*args):
        calls.append(args)
        return quality()
    for signature in ('one', 'one', 'two'):
        _, _, cache = build(tmp_path, measure=measure, cache=cache, signature=signature)
    assert len(calls) == 2
    (tmp_path/'artifacts/images_to_convert/AA0010.jpg').write_bytes(b'changed')
    build(tmp_path, measure=measure, cache=cache, signature='two')
    assert len(calls) == 3
    (tmp_path/'artifacts/converted_images/converted_svgs/aa0010.svg').write_text(SVG+'\n')
    build(tmp_path, measure=measure, cache=cache, signature='two')
    assert len(calls) == 4
    for key in cache:
        cache[key] = dict(error='old timeout', renderers={})
    build(tmp_path, measure=measure, cache=cache, signature='two')
    assert len(calls) == 5


@pytest.mark.parametrize('failed_renderer', ['mupdf', 'librsvg'])
def test_one_passing_renderer_cannot_certify_the_pair(failed_renderer):
    measured = quality()
    measured['renderers'][failed_renderer]['satisfactory'] = False
    assert classify(measured) == 'pixel_fail'


def test_candidate_selection_requires_both_renderers_before_smaller_mse(tmp_path):
    prepare(tmp_path)
    failed = tmp_path/'artifacts/converted_images/converted_svg_failed'
    failed.mkdir()
    (failed/'AA0010.svg').write_text(SVG+'\n')
    def measure(image, svg):
        return quality(svg.parent == failed, .009 if svg.parent == failed else .000001)
    rows, _, _ = build(tmp_path, measure=measure)
    assert rows[0]['status'] == 'pixel_pass'
    assert 'converted_svg_failed' in rows[0]['selected']['svg']


def test_report_escapes_source_text_and_keeps_all_records(tmp_path):
    prepare(tmp_path, desc='</script><script>alert("x")</script>')
    rows, summary, _ = build(tmp_path, measure=lambda *args: quality())
    output = tmp_path/'report'
    write_report(tmp_path, output, rows, summary, {})
    html = (output/'index.html').read_text(encoding='utf-8')
    assert '\\u003c/script' in html
    assert '</script><script>alert' not in html
    saved = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    assert len(saved['rows']) == 1 and saved['rows'][0]['description'] == rows[0]['description']


def test_evidence_cannot_escape_the_repository(tmp_path):
    with pytest.raises(ValueError, match='leaves repository'):
        inside(tmp_path, '../outside.svg')


def test_real_isolated_measurement_uses_two_renderers_and_closes_its_worker(tmp_path):
    import cv2
    from tools.evaluate_svg_text_baseline import render_librsvg
    image, svg = tmp_path/'input.png', tmp_path/'output.svg'
    cv2.imwrite(str(image), render_librsvg(SVG, 40, 40))
    svg.write_text(SVG)
    worker = QualityWorker(timeout=15)
    try:
        result = worker.measure(image, svg)
    finally:
        worker.close()
    assert classify(result) == 'pixel_pass'
    assert set(result['renderers']) == {'mupdf', 'librsvg'}
    assert worker.process is None


def background_svg(root, name='AA0010.svg', suffix=''):
    path = root/'artifacts/converted_images/catalog_background_svgs'/('b'*32)/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SVG+suffix, encoding='utf-8')
    return path


def test_single_candidate_update_never_discovers_or_opens_other_images(tmp_path, monkeypatch):
    import copy
    from tools import build_catalog_inventory as inventory
    prepare(tmp_path, archived=True)
    rows, summary, _ = build(tmp_path, measure=lambda *args:quality(False, .05))
    untouched = copy.deepcopy(rows[0])
    untouched.update(filename='BB0010.jpg', group='BB', image='missing-other-image.jpg', variant='BB0010')
    untouched['candidates'][0]['svg'] = 'missing-other.svg'
    rows.append(untouched)
    summary['catalog_bitmaps'] += 1
    summary['catalog_statuses']['pixel_fail'] += 1
    summary['groups']['BB'] = dict(total=1, archived=1, statuses=dict(pixel_fail=1))
    payload = copy.deepcopy(dict(rows=rows, summary=summary))
    original = copy.deepcopy(payload)
    monkeypatch.setattr(inventory, 'discover', lambda *args:pytest.fail('Full catalog scan'))
    monkeypatch.setattr(inventory, 'runtime_signature', lambda *args:pytest.fail('Full runtime scan'))
    candidate = background_svg(tmp_path, suffix='\n')
    calls = []
    def measure(image, svg):
        calls.append((image, svg))
        return quality(True)
    updated, result = update_candidate(tmp_path, payload, 'AA0010.jpg', candidate, measure=measure)
    assert calls == [(tmp_path/rows[0]['image'], candidate)]
    assert payload == original
    assert updated[1] == original['rows'][1]
    assert updated[0]['status'] == 'pixel_pass'
    assert updated[0]['candidates'][0]['measurement'] == original['rows'][0]['candidates'][0]['measurement']
    assert result['catalog_statuses'] == {'pixel_fail':1, 'pixel_pass':1}
    assert result['groups']['AA']['statuses'] == {'pixel_pass':1}
    assert result['groups']['BB'] == summary['groups']['BB']
    assert result['archived_current_pixel_pass'] == 1
    assert sum(c['saved_pixel_pass'] for c in result['geometry_classes']['classes'].values()) == 1
    assert result['full_generated_at'] == summary['generated_at']
    assert result['measurement_scope'] == 'single_candidate'


@pytest.mark.parametrize('error', ['source', 'copy', 'reserved', 'outside'])
def test_single_candidate_refuses_changed_sources_reservations_and_wrong_paths(tmp_path, error):
    prepare(tmp_path)
    rows, summary, _ = build(tmp_path, measure=lambda *args:quality(False))
    candidate = background_svg(tmp_path)
    if error == 'source':
        (tmp_path/rows[0]['image']).write_bytes(b'changed')
    elif error == 'copy':
        copy = tmp_path/'copy.jpg'
        copy.write_bytes(b'changed')
        rows[0]['all_source_paths'].append('copy.jpg')
    elif error == 'reserved':
        folder = tmp_path/'config'
        folder.mkdir()
        (folder/'real_composition_holdout_new.json').write_text(json.dumps(dict(
            evaluation_policy=dict(status='sealed_unrun'), cases=[dict(file='AA0010.jpg')])))
    else:
        candidate = tmp_path/'artifacts/converted_images/converted_svgs/aa0010.svg'
    with pytest.raises(ValueError):
        update_candidate(tmp_path, dict(rows=rows,summary=summary), 'AA0010.jpg', candidate,
                         measure=lambda *args:pytest.fail('Must refuse before measuring'))


def test_identical_attempts_keep_provenance_without_duplicate_candidates(tmp_path):
    prepare(tmp_path)
    rows, summary, _ = build(tmp_path, measure=lambda *args:quality(False))
    candidate = background_svg(tmp_path)
    updated, _ = update_candidate(tmp_path, dict(rows=rows,summary=summary), 'AA0010.jpg', candidate,
                                  measure=lambda *args:quality(True))
    assert len(updated[0]['candidates']) == 1
    assert len(updated[0]['selected']['all_paths']) == 2
    assert updated[0]['status'] == 'pixel_pass'
