"""Aspect references feed the real parsers without borrowing donor objects."""
from xml.etree import ElementTree as ET
import io

import pytest

from src.iCCModules.imageCompositeConverterSimilarity import (
    SimilarityReferenceError, resolve_similarity_description,
)
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection, _get_base_name_from_file


CATALOG = {
    'ROUND': 'Ein blauer Kreis mit schwarzer Kontur.',
    'PAINT': 'Ein rotes Rechteck mit grauem Rand.',
    'PANEL': 'Ein einzelnes Rechteck ohne Kontur.',
    'GRADIENT': 'Ein grünes Dreieck. Die rote Füllung hat einen horizontalen Farbverlauf.',
    'HANDLE': ('Ein unbeschrifteter Kreis mit einem geraden Griff nach links. '
               'Der Griff liegt auf einer Symmetrieachse des Kreises.'),
    'CATALOG_HANDLE': ('Kelle, ohne Text Kreis oben, Griff nach unten (dunkelgraue Liine). '
                       'Der Griff liegt auf einer Symmetrieachse des Kreises.'),
    'CATALOG_PAINT': 'Grauer Kreis mit grauem Rand und hellgrauem Hintergrund',
}


def resolve(text, catalog=None):
    return resolve_similarity_description(text, CATALOG if catalog is None else catalog,
                                         base_name=_get_base_name_from_file)


@pytest.mark.parametrize('aspect', ['Form', 'Formen', 'Geometrie', 'Form ist', 'Form:'])
@pytest.mark.parametrize('similar', ['ähnlich wie', 'aehnlich wie', 'wie'])
def test_form_reference_does_not_import_palette(aspect, similar):
    resolved = resolve(f'{aspect} {similar} ROUND.')
    assert resolved.text == 'Ein Kreis mit Kontur.'
    assert resolved.references[0]['aspect'] == 'shape'


def test_two_donors_keep_only_the_requested_aspects():
    resolved = resolve('Form ähnlich wie ROUND; Farben ähnlich wie PAINT.')
    assert resolved.text == 'Ein roter Kreis mit grauer Kontur.'
    assert 'Rechteck' not in resolved.text
    assert 'blau' not in resolved.text and 'schwarz' not in resolved.text
    assert {(r['aspect'], r['key']) for r in resolved.references} == {('shape', 'ROUND'), ('color', 'PAINT')}


def test_color_only_keeps_callers_shape_and_explicit_fill():
    assert resolve('Ein blauer Kreis mit Kontur. Farben ähnlich wie PAINT.').text == 'Ein blauer Kreis mit grauer Kontur.'


def test_negated_claims_do_not_discard_positive_colors_before_them():
    assert resolve('Ein Kreis. Farben ähnlich wie PAINT.', {'PAINT': 'Ein roter Kreis ohne Text.'}).text == 'Ein roter Kreis.'


def test_form_omits_background_paint_and_color_can_supply_it():
    catalog = {'ROUND': 'Grauer Kreis mit grauem Rand und hellgrauem Hintergrund',
               'PAINT': 'Ein rotes Rechteck mit schwarzem Rand und weissem Hintergrund.'}
    assert resolve('Form ähnlich wie ROUND.', catalog).text == 'Kreis mit Rand.'
    assert resolve('Form ähnlich wie ROUND; Farben ähnlich wie PAINT.', catalog).text == 'roter Kreis mit schwarzem Rand und weissem Hintergrund.'


def test_legacy_handle_prose_keeps_color_free_raster_model():
    from src.iCCModules.imageCompositeConverterStemDisk import stem_disk_direction
    text = resolve('Form ähnlich wie HANDLE.', {'HANDLE':
        'Kelle, ohne Text Kreis oben, Griff nach unten (dunkelgraue Liine). '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'}).text
    assert stem_disk_direction(text) == 'unten'


def test_color_only_never_imports_donor_shape_label_or_negation():
    resolved = resolve('Ein Kreis. Farben ähnlich wie PAINT.',
                       {'PAINT': 'Ein rotes Rechteck. Text "M". Keine Anschlüsse.'})
    assert resolved.text == 'Ein roter Kreis.'


def test_gradient_is_projected_without_donor_geometry():
    resolved = resolve('Form ähnlich wie PANEL; Farbverlauf ähnlich wie GRADIENT.')
    assert resolved.text == 'Ein einzelnes Rechteck ohne Kontur. Die rote Füllung hat einen horizontalen Farbverlauf.'
    assert 'Dreieck' not in resolved.text and 'grün' not in resolved.text


def test_color_only_gradient_respects_explicit_caller_fill():
    text = resolve('Ein blaues Rechteck ohne Kontur. Farbverlauf ähnlich wie GRADIENT.').text
    assert 'Die blaue Füllung' in text and 'rote' not in text


def test_axial_gradient_parser_receives_the_projected_paint_clause():
    from src.iCCModules.imageCompositeConverterAxialPanel import panel_contract
    # A shape reference contributes no fill adjective; the paint clause carries
    # the palette role, matching the established axial model vocabulary.
    text = resolve('Form ähnlich wie PANEL; Farbverlauf ähnlich wie GRADIENT.').text
    assert panel_contract(text) is not None


def test_explicit_absence_removes_only_inherited_attachment():
    result = resolve('Form ähnlich wie HANDLE, aber ohne Anschluss.')
    assert 'Griff' not in result.text and 'links' not in result.text
    assert 'Kreis' in result.text and 'ohne Anschluss' in result.text


def test_caller_no_text_overrides_inherited_label():
    result = resolve('Form ähnlich wie ROUND. Ohne Text.', {'ROUND': 'Ein Kreis mit Text "M".'})
    assert '"M"' not in result.text
    assert 'Kreis' in result.text and 'Ohne Text' in result.text
    _, params = Reflection({'UPLOAD': 'Form ähnlich wie ROUND. Ohne Text.',
                            'ROUND': 'Ein Kreis mit Text "M".'}).parse_description('UPLOAD', 'UPLOAD.png')
    assert params['language_assertions']['no_text']


def test_caller_label_replaces_inherited_label_and_preserves_case():
    text = resolve('Form ähnlich wie ROUND. Beschriftung "rF".',
                   {'ROUND': 'Ein Kreis. Beschriftung "M".'}).text
    assert '"M"' not in text and '"rF"' in text


def test_form_projection_does_not_rewrite_color_words_inside_a_label():
    text = resolve('Form ähnlich wie ROUND.', {'ROUND': 'Ein blauer Kreis. Text "rot".'}).text
    assert '"rot"' in text and 'blau' not in text


def test_projection_and_attachment_edit_preserve_label_bytes_and_paint_words():
    text = resolve('Form ähnlich wie ROUND. Ohne Anschluss.',
                   {'ROUND': 'Ein blauer Kreis. Text "rot,  Farbverlauf".'}).text
    assert '"rot,  Farbverlauf"' in text


def test_nested_reference_expansion_has_a_total_size_bound():
    catalog = {'BASE': 'Ein blauer Kreis.'}
    previous = 'BASE'
    for n in range(10):
        key = f'LEVEL{n}'
        catalog[key] = f'Form ähnlich wie {previous}; Farben ähnlich wie {previous}.'
        previous = key
    with pytest.raises(SimilarityReferenceError, match='zu viele'):
        resolve(f'Form ähnlich wie {previous}.', catalog)


def test_quoted_reference_is_literal_and_legacy_user_alias_is_unchanged():
    for text in ['Ein Kreis. Text "Form ähnlich wie UNKNOWN".', 'Wie ROUND, jedoch rot.']:
        assert resolve(text).text == text
        assert not resolve(text).references


def test_exact_variant_is_preferred_and_family_is_a_fallback():
    catalog = {'SHAPE': 'Ein Kreis.', 'SHAPE_L': 'Ein Rechteck.'}
    assert resolve('Form ähnlich wie shape_l.svg.', catalog).text == 'Ein Rechteck.'
    assert resolve('Form ähnlich wie SHAPE_M.jpg.', catalog).text == 'Ein Kreis.'


def test_nested_scoped_and_legacy_donor_references():
    catalog = {'BASE': 'Ein blauer Kreis.', 'ALIAS': 'Wie BASE, ohne Text.',
               'NEW': 'Form und Farben ähnlich wie ALIAS.'}
    text = resolve('Form ähnlich wie NEW.', catalog).text
    assert 'Kreis' in text and 'blau' not in text
    assert 'BASE' not in text and 'ALIAS' not in text


@pytest.mark.parametrize('text,catalog,message', [
    ('Form ähnlich wie MISSING.', {}, 'Keine hinterlegte'),
    ('Form ähnlich wie EMPTY.', {'EMPTY': ' '}, 'Keine hinterlegte'),
    ('Form ähnlich wie LOOP.', {'LOOP': 'Form ähnlich wie LOOP.'}, 'Zyklische'),
    ('Form ähnlich wie A.', {'A': 'Wie B.', 'B': 'Wie A.'}, 'Zyklische'),
    ('Form ähnlich wie ROUND; Form ähnlich wie PAINT.', CATALOG, 'nur eine'),
    ('Nicht Form ähnlich wie ROUND.', CATALOG, 'positive'),
    ('Farbverlauf ähnlich wie PAINT. Ein Kreis.', CATALOG, 'keinen Farbverlauf'),
    ('Farben ähnlich wie EMPTY. Ein Kreis.', {'EMPTY': 'Ein Kreis.'}, 'keine erkennbaren'),
])
def test_unresolvable_or_ambiguous_references_are_actionable_errors(text, catalog, message):
    with pytest.raises(SimilarityReferenceError, match=message):
        resolve(text, catalog)


def test_explicit_extra_objects_are_preserved_in_effective_description():
    result = resolve('Form ähnlich wie ROUND. Zusätzlich ein Dreieck und eine Linie.')
    assert 'Dreieck und eine Linie' in result.text


def test_exception_cannot_silently_discard_another_inherited_object():
    with pytest.raises(SimilarityReferenceError, match='weiteren Formen'):
        resolve('Form ähnlich wie HANDLE, aber ohne Anschluss.',
                {'HANDLE': 'Ein Kreis mit einem Griff und ein Dreieck.'})


def test_exception_cannot_discard_a_second_object_of_the_same_kind():
    with pytest.raises(SimilarityReferenceError, match='weiteren Formen'):
        resolve('Form ähnlich wie HANDLE, aber ohne Anschluss.',
                {'HANDLE': 'Ein Kreis mit einem Griff und ein Kreis.'})


def test_paint_projection_cannot_discard_a_shape_in_the_same_sentence():
    with pytest.raises(SimilarityReferenceError, match='nicht eindeutig trennbar'):
        resolve('Form ähnlich wie ROUND.', {'ROUND': 'Ein Kreis mit blauem Farbverlauf und ein Dreieck.'})


def test_multicolor_projection_preserves_palette_without_importing_objects():
    text = resolve('Ein Kreis. Farben ähnlich wie PAINT.',
                   {'PAINT': 'Ein rotes Rechteck und ein blaues Dreieck.'}).text
    assert 'rot, blau' in text
    assert 'Dreieck' not in text and 'Rechteck' not in text


def test_gradient_projection_preserves_multiple_stop_colors():
    text = resolve('Ein Rechteck. Farbverlauf ähnlich wie PAINT.',
                   {'PAINT': 'Ein Kreis mit horizontalem Farbverlauf von blau nach grün.'}).text
    assert 'blau, grün' in text and 'horizontalen Farbverlauf' in text
    assert 'Kreis' not in text


def test_reflection_preserves_original_and_resolved_provenance_and_labels():
    description = 'Form ähnlich wie ROUND; Farben ähnlich wie PAINT.'
    desc, params = Reflection({**CATALOG, 'UPLOAD': description}).parse_description('UPLOAD', 'UPLOAD.png')
    assert params['description_fragments'][0]['text'] == description
    assert params['effective_description'] == 'Ein roter Kreis mit grauer Kontur.'
    assert desc == params['effective_description'].lower()
    assert params['similarity_references']
    assert not params['documented_alias_refs']


def test_form_and_color_reference_with_bare_caller_color_override():
    assert resolve('Form ähnlich wie ROUND; Farben ähnlich wie PAINT, aber blau.').text == 'Ein blauer Kreis mit grauer Kontur.'


def test_reflection_does_not_route_a_color_donor_as_a_legacy_alias():
    text = 'Ein Kreis. Farben ähnlich wie AC0811.'
    _, params = Reflection({'UPLOAD': text, 'AC0811': 'Ein rotes Rechteck.'}).parse_description('UPLOAD', 'UPLOAD.png')
    assert not params.get('badge_param_source_ref')
    assert 'Rechteck' not in params['effective_description']


def test_resolved_plain_disk_still_passes_real_raster_gates():
    from tests.test_plain_disk_runtime import synthetic, fit
    from tools.run_plan_b_variations import render, measure_quality
    text = resolve('Form ähnlich wie ROUND; Farben ähnlich wie PAINT.').text
    image = render(synthetic(40, fill='#f2d8d8', stroke='#626262'), 40, 40)
    fitted = fit(image, text)
    assert fitted is not None
    assert measure_quality(image, fitted['svg'])['satisfactory']
    assert [n.tag.rsplit('}', 1)[-1] for n in ET.fromstring(fitted['svg']).iter()] == ['svg', 'rect', 'circle']


@pytest.fixture
def gui_jobs(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: CATALOG)
    monkeypatch.setitem(gui.PROFILES, 'quick', (15, 25))
    manager = gui.Jobs(tmp_path/'jobs')
    manager.project_directory = tmp_path/'project'
    yield manager
    manager.close()


def test_gui_rejects_missing_reference_before_starting_worker(gui_jobs):
    from PIL import Image
    from src.imageConverterGui import RequestError
    stream = io.BytesIO()
    Image.new('RGB', (40, 40), 'white').save(stream, format='PNG')
    job = gui_jobs.upload('neutral.png', stream.getvalue())
    with pytest.raises(RequestError, match='Keine hinterlegte'):
        gui_jobs.start(job['id'], 'Form ähnlich wie MISSING.', 'quick')
    assert gui_jobs.snapshot(job['id'])['status'] == 'ready'
    assert not gui_jobs.threads


@pytest.mark.parametrize('description', [
    'Form ähnlich wie ROUND; Farben ähnlich wie PAINT.',
    'Form ähnlich wie HANDLE, aber ohne Anschluss.',
    'Form ähnlich wie ROUND. Ohne Text.',
    'Form ähnlich wie CATALOG_HANDLE, aber ohne Anschluss. Farben ähnlich wie CATALOG_PAINT.',
])
def test_references_convert_through_real_gui_worker(gui_jobs, description):
    from PIL import Image
    from tests.test_plain_disk_runtime import synthetic
    from tools.run_plan_b_variations import render
    image = render(synthetic(40, fill='#f2d8d8', stroke='#626262'), 40, 40)
    stream = io.BytesIO()
    Image.fromarray(image[:, :, ::-1]).save(stream, format='PNG')
    job = gui_jobs.upload('neutral.png', stream.getvalue())
    started = gui_jobs.start(job['id'], description, 'quick')
    gui_jobs.threads[-1].join(timeout=60)
    result = gui_jobs.snapshot(started['id'])
    folder = gui_jobs.folder(started['id'])
    log = (folder/'console.log').read_text(encoding='utf-8')
    if result['status'] != 'done':
        log += '\n'.join(p.read_text(encoding='utf-8') for p in folder.rglob('batch_failure_summary.csv'))
    assert result['status'] == 'done', (result.get('message'), log)
    assert result['quality'] == 'passed', (result.get('message'), log)
    assert result['description'] == description
    assert 'Aufgelöste Bildbeschreibung:' in log and 'Ähnlichkeitsreferenz (Form):' in log
    assert [n.tag.rsplit('}', 1)[-1] for n in ET.parse(folder/'result.svg').iter()] == ['svg', 'rect', 'circle']


def test_workbench_freezes_resolved_description_for_all_variants(tmp_path, monkeypatch):
    from tools.plan_b_workbench import prepare
    from tests.test_plain_disk_runtime import synthetic
    from src.iCCModules import imageCompositeConverterDescriptions as descriptions
    monkeypatch.setattr(descriptions, 'loadCatalogDescriptionMappingImpl', lambda root: CATALOG)
    original = 'Form ähnlich wie ROUND; Farben ähnlich wie PAINT.'
    folder = tmp_path/'run'
    report = prepare(synthetic(40), original, folder, seed=17)
    assert report['source_description'] == original
    assert report['effective_source_description'] == 'Ein roter Kreis mit grauer Kontur.'
    assert report['similarity_references']
    assert len(report['cases']) == 17
    assert all('ähnlich wie' not in case['description'] for case in report['cases'])
    assert (folder/'source_description.txt').read_text(encoding='utf-8') == original


def test_sample_gui_worker_receives_and_logs_resolved_references(gui_jobs):
    from PIL import Image
    from tests.test_plain_disk_runtime import synthetic
    from tools.run_plan_b_variations import render
    svg = synthetic(40, fill='#f2d8d8', stroke='#626262')
    stream = io.BytesIO()
    Image.fromarray(render(svg, 40, 40)[:, :, ::-1]).save(stream, format='PNG')
    job = gui_jobs.upload('neutral.png', stream.getvalue())
    gui_jobs.attach_sample(job['id'], 'sample.svg', svg.encode('utf-8'))
    original = 'Form ähnlich wie ROUND; Farben ähnlich wie PAINT.'
    started = gui_jobs.start(job['id'], original, 'quick')
    gui_jobs.threads[-1].join(timeout=40)
    result = gui_jobs.snapshot(started['id'])
    assert result['status'] == 'done' and result['quality'] == 'passed', result
    folder = gui_jobs.folder(started['id'])
    assert (folder/'description.txt').read_text(encoding='utf-8') == 'Ein roter Kreis mit grauer Kontur.'
    assert 'Aufgelöste Bildbeschreibung:' in (folder/'console.log').read_text(encoding='utf-8')
    assert result['description'] == original


def test_standalone_sample_refinement_enforces_resolved_reference_counts(tmp_path, monkeypatch):
    from PIL import Image
    from src.imageConverterSample import render_svg, refine
    from tests.test_plain_disk_runtime import synthetic
    from src.iCCModules import imageCompositeConverterDescriptions as descriptions
    monkeypatch.setattr(descriptions, 'loadCatalogDescriptionMappingImpl',
                        lambda root: {'FAMILY': 'Das Motiv enthält genau zwei Kreise.'})
    svg = synthetic(40)
    source, sample, output = (tmp_path/name for name in ('source.png', 'sample.svg', 'output.svg'))
    Image.fromarray(render_svg(svg, 40, 40)).save(source)
    sample.write_text(svg, encoding='utf-8')
    report = refine(source, sample, output, 'Form ähnlich wie FAMILY.', 1)
    assert not report['passed']
    assert 'object_count:circle:2:1' in report['description_error']
