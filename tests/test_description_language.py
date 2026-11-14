"""Language polarity and assertions must survive dispatch and early checkpoints."""
import pytest

from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
    DescriptionRejected, description_assertions, normalize_description, validate_svg_assertions,
    gradient_direction,
)


@pytest.mark.parametrize('text', ['Ohne Beschriftung.', 'Schriftzeichen fehlen.', 'Kein Text.'])
def test_absence_is_canonical_without_turning_into_present_label(text):
    assert normalize_description(text).casefold() == 'keine schriftzeichen.'
    assert description_assertions(text)['no_text']


def test_quoted_labels_are_never_normalized():
    text='Die Aufschrift "Umriss horizontal rF" steht in einer runden Scheibe.'
    normalized=normalize_description(text, orientations=True)
    assert '"Umriss horizontal rF"' in normalized
    assert 'Kreisscheibe' in normalized and 'Beschriftung' in normalized
    assert normalize_description(normalized, orientations=True)==normalized


def test_common_minus_and_axis_spellings_preserve_labels_and_negation():
    text = ('Kein Minnus-Zeichen. Ein horizonaler Farbverlauf neben der vertialen Linie. '
            'Die Beschriftung lautet "Minnus horizonaler vertialen".')
    normalized = normalize_description(text)
    assert normalized.startswith('Kein Minus-Zeichen. Ein horizontaler Farbverlauf neben der vertikalen Linie.')
    assert '"Minnus horizonaler vertialen"' in normalized
    assert normalize_description(normalized) == normalized


def test_head_direction_typos_preserve_quoted_labels_and_polarity():
    text = 'Links Spitze nach obben, rechts Spitze nach untten. Beschriftung "Spitze nach untten".'
    normalized = normalize_description(text)
    assert normalized == 'Links Spitze nach oben, rechts Spitze nach unten. Beschriftung "Spitze nach untten".'
    assert normalize_description(normalized) == normalized


def test_triangle_subject_directions_preserve_quotes_and_negation():
    text = ('Das linke Dreiek zeigt nach oben. Das rechte Dreick zeigt nach unten. '
            'Das Dreieck zeigt nicht nach oben. Beschriftung "Dreiek zeigt nach unten".')
    normalized = normalize_description(text)
    assert normalized == ('Das linke Dreieck mit Spitze nach oben. '
                          'Das rechte Dreieck mit Spitze nach unten. '
                          'Das Dreieck zeigt nicht nach oben. Beschriftung "Dreiek zeigt nach unten".')
    assert normalize_description(normalized) == normalized


def test_arrow_subject_and_plural_typo_preserve_quotes_and_negation():
    text = ('Zwei Dreicke. Der linke Pfeil zeigt nach oben, der rechte Pfeil nach unten. '
            'Der Pfeil zeigt nicht nach unten. Beschriftung "Dreicke Pfeil nach unten".')
    normalized = normalize_description(text)
    assert 'Zwei Dreiecke. Der linke Pfeil mit Spitze nach oben, der rechte Pfeil mit Spitze nach unten.' in normalized
    assert 'Der Pfeil zeigt nicht nach unten.' in normalized
    assert '"Dreicke Pfeil nach unten"' in normalized
    assert normalize_description(normalized) == normalized


@pytest.mark.parametrize('fault', ['deformed', 'wrong_direction', 'same_position', 'reflected'])
def test_described_heads_require_shape_separation_and_displayed_direction(fault):
    assertions = description_assertions('Zwei vertikale Linien, rot blau, Dreiecke. '
                                        'Links Spitze nach oben, rechts Spitze nach unten.')
    left = '<polygon points="2,0 0,4 4,4"/>'
    right = '<polygon points="20,0 24,0 22,4"/>'
    if fault == 'deformed':
        right = '<polygon points="20,0 24,40 22,4"/>'
    elif fault == 'wrong_direction':
        right = '<polygon points="22,0 20,4 24,4"/>'
    elif fault == 'same_position':
        right = left
    else:
        right = '<g transform="matrix(1,0,0,-1,0,4)">'+right+'</g>'
    with pytest.raises(DescriptionRejected):
        validate_svg_assertions('<svg>'+left+right+'</svg>', assertions)


def test_nested_reflected_sample_heads_are_checked_after_their_transforms():
    assertions = description_assertions('Zwei vertikale Linien, rot blau, Dreiecke. '
                                        'Links Spitze nach oben, rechts Spitze nach unten.')
    svg = ('<svg><g transform="translate(1 2) scale(2)">'
           '<g transform="matrix(-1,0,0,-1,4,4)"><polygon points="0,0 4,0 2,4"/></g>'
           '<polygon points="20,0 24,0 22,4"/></g></svg>')
    validate_svg_assertions(svg, assertions)


def test_spitz_and_gegen_direction_wording_preserves_quotes_and_negation():
    text = ('Links zeigt mit dem Spitz gegen oben, rechts mit der Spitze gegen unten. '
            'Spitz nicht nach unten. Beschriftung "Spitz gegen oben".')
    normalized = normalize_description(text)
    assert normalized == ('Links zeigt mit dem Spitze nach oben, rechts mit der Spitze nach unten. '
                          'Spitz nicht nach unten. Beschriftung "Spitz gegen oben".')
    assert normalize_description(normalized) == normalized


@pytest.mark.parametrize('phrase', ['blaue horizontale', 'horizontale blaue',
                                   'blaue waagerechte', 'waagerechte blaue',
                                   'blauer horizontaler', 'horizontaler blauer',
                                   'blauen horizontalen', 'horizontalen blauen'])
def test_blue_horizontal_bar_color_is_checked_in_both_word_orders(phrase):
    description = ('Zwei vertikale Linien, rot und blau, zwei Dreiecke. '
                   'Links Spitz gegen oben, rechts Spitz nach unten. '+phrase+' Linie.')
    assertions = description_assertions(description)
    heads = '<polygon points="2,0 0,4 4,4"/><polygon points="20,0 24,0 22,4"/>'
    bar = '<rect x="4" y="68" width="26" height="1" fill="blue"/>'
    validate_svg_assertions('<svg>'+heads+bar+'</svg>', assertions)
    with pytest.raises(DescriptionRejected, match='missing_described_horizontal_bar'):
        validate_svg_assertions('<svg>'+heads+bar.replace('blue', 'red')+'</svg>', assertions)


def test_bar_color_quotes_are_ignored_and_conflicts_rejected():
    description = ('Zwei vertikale Linien, rot und blau, zwei Dreiecke. '
                   'Links Spitze nach oben, rechts Spitze nach unten. Blaue horizontale Linie.')
    assert description_assertions(description+' Beschriftung "horizontale rote Linie".')['horizontal_bar'] == 'blue'
    with pytest.raises(DescriptionRejected, match='conflicting_horizontal_bar_colors'):
        description_assertions(description+' Eine horizontale rote Linie.')


@pytest.mark.parametrize('word', ['Farbübergang', 'Farbenübergang', 'Farbuebergang',
                                 'Graustufenübergang', 'Graustufenuebergang', 'Graustufenverlauf'])
def test_gradient_synonyms_preserve_label_bytes_and_absence(word):
    normalized = normalize_description(f'Vertikaler {word}. Kein Text. Die Farbe heisst "{word}".')
    expected = 'Graustufenverlauf' if word.startswith('Graustufen') else 'Farbverlauf'
    assert normalized.startswith(f'Vertikaler {expected}. keine Schriftzeichen.')
    assert f'"{word}"' in normalized


@pytest.mark.parametrize('text,reason', [
    ('Die Beschriftung lautet "rF". Keine Schriftzeichen.', 'text_present_and_absent'),
    ('Ein Ausrufezeichen. Ohne Beschriftung.', 'text_present_and_absent'),
    ('Die vordere Form liegt links von der hinteren Form.', 'unresolved_depth_selector'),
    ('Es gibt genau zwei Kreise. Das Motiv enthält genau einen Kreis.', 'conflicting_object_counts'),
])
def test_explicit_contradictions_and_unknown_referents_are_rejected(text, reason):
    with pytest.raises(DescriptionRejected,match=reason):
        description_assertions(text)


def test_native_count_excludes_definitions_and_rejects_missing_instances():
    svg='<svg><defs><circle r="3"/></defs><circle r="4"/></svg>'
    validate_svg_assertions(svg,description_assertions('Das Motiv enthält genau einen Kreis.'))
    with pytest.raises(DescriptionRejected,match='object_count'):
        validate_svg_assertions(svg,description_assertions('Das Motiv enthält genau zwei Kreise.'))


@pytest.mark.parametrize('replacement', [
    '<circle cx="5" cy="8" r="3"/>',
    '<ellipse cx="5" cy="8" rx="3" ry="2"/>',
    '<polygon points="0,0 1,1 2,2"/>',
    '<polygon points="0,0 4,0 4,4 0,4"/>',
    '<defs><polygon points="0,0 4,0 2,4"/></defs>',
])
def test_described_arrow_heads_cannot_be_replaced_by_other_primitives(replacement):
    description = ('Zwei vertikale Striche links rot, rechts blau. Unten Dreiecke, '
                   'links Spitze nach oben, rechts Spitze nach untten.')
    assertions = description_assertions(description)
    head = '<polygon points="0,0 4,0 2,4"/>'
    with pytest.raises(DescriptionRejected, match='object_count:triangle:2:1'):
        validate_svg_assertions('<svg>'+head+replacement+'</svg>', assertions)
    validate_svg_assertions('<svg><polygon points="2,0 0,4 4,4"/>'
                            '<polygon points="20,0 24,0 22,4"/></svg>', assertions)


def test_triangle_count_is_enforced_before_a_pixel_perfect_checkpoint():
    import numpy as np
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
    from src.iCCModules.imageCompositeConverterSearchPortfolio import validated_result
    session = ImageSearch(SearchPolicy())
    session.description_assertions = description_assertions('Es gibt genau zwei Dreiecke.')
    image = np.full((10,10,3), 255, dtype=np.uint8)
    with image_search(session), pytest.raises(DescriptionRejected, match='object_count:triangle'):
        validated_result(dict(svg='<svg><polygon points="0,0 4,0 2,4"/><circle r="3"/></svg>',
                              rendered=image), image)
    assert not session.validated


@pytest.mark.parametrize('bar,accepted', [
    ('<line x1="4" y1="68" x2="30" y2="68" stroke="red"/>', True),
    ('<rect x="4" y="68" width="26" height="1" fill="#eb1820"/>', True),
    ('<line x1="4" y1="68" x2="30" y2="69" stroke="red"/>', False),
    ('<line x1="4" y1="68" x2="30" y2="68" stroke="blue"/>', False),
    ('<rect x="4" y="0" width="1" height="102" fill="red"/>', False),
    ('<g transform="rotate(2)"><rect width="26" height="1" fill="red"/></g>', False),
    ('<g transform="translate(1 2) scale(1.1)"><rect width="26" height="1" fill="red"/></g>', True),
])
def test_described_red_horizontal_bar_requires_color_and_exact_direction(bar, accepted):
    assertions = description_assertions('Zwei vertikale Striche rot blau, Dreiecke, '
        'links Spitze nach oben, rechts Spitze nach unten. Unteres Drittel rote horizontale Linie.')
    heads = '<polygon points="2,0 0,4 4,4"/><polygon points="20,0 24,0 22,4"/>'
    svg = '<svg>'+heads+bar+'</svg>'
    if accepted:
        validate_svg_assertions(svg, assertions)
    else:
        with pytest.raises(DescriptionRejected, match='missing_described_horizontal_bar'):
            validate_svg_assertions(svg, assertions)


def test_quoted_geometry_is_not_an_object_count_assertion():
    assert not description_assertions('Die Aufschrift lautet "Es gibt genau zwei Kreise".')['counts']
    assert description_assertions('Eine Fläche der Farbe "rot". Keine Schriftzeichen.')['no_text']


def test_no_text_contract_is_checked_on_actual_svg():
    with pytest.raises(DescriptionRejected,match='unexpected_text_in_svg'):
        validate_svg_assertions('<svg><text>F</text></svg>',description_assertions('Keine Schriftzeichen.'))


def test_count_violation_cannot_be_saved_as_deadline_checkpoint():
    import numpy as np
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch,SearchPolicy,image_search
    from src.iCCModules.imageCompositeConverterSearchPortfolio import validated_result
    session=ImageSearch(SearchPolicy())
    session.description_assertions=description_assertions('Es gibt genau zwei Kreise.')
    checkpoints=[]
    session.on_validated=lambda *args: checkpoints.append(args)
    image=np.full((10,10,3),255,dtype=np.uint8)
    with image_search(session),pytest.raises(DescriptionRejected,match='object_count'):
        validated_result(dict(svg='<svg><circle r="4"/></svg>',rendered=image),image)
    assert not checkpoints and not session.validated


def test_reflection_retains_original_text_but_normalizes_dispatch_vocabulary():
    from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
    raw='Eine einfarbige runde Scheibe mit dunklem Umriss und serifenloser Aufschrift "rF". Anschlussfrei.'
    text,params=Reflection({'neutral':raw}).parse_description('neutral','neutral.png')
    assert 'kreisscheibe' in text and 'randkontur' in text and 'keine anschlüsse' in text
    assert params['description_fragments'][0]['text']==raw


def test_absence_in_one_image_does_not_leak_into_another_search():
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch,SearchPolicy,image_search
    a,b=ImageSearch(SearchPolicy()),ImageSearch(SearchPolicy())
    a.description_assertions=description_assertions('Keine Schriftzeichen.')
    with image_search(a):
        with image_search(b):
            assert not getattr(b,'description_assertions',None)
    assert a.description_assertions['no_text']


def test_orientation_belongs_to_the_gradient_not_another_bar():
    text=normalize_description('Vertikaler Farbverlauf um eine waagerechte Rechteckfläche.',orientations=True).casefold()
    assert gradient_direction(text,'senkrecht')
    assert not gradient_direction(text,'waagerecht')
    text=normalize_description('Senkrechter Balken im Kreis mit horizontalem Farbverlauf.',orientations=True).casefold()
    assert not gradient_direction(text,'senkrecht')
    assert gradient_direction(text,'waagerecht')
    assert gradient_direction('der farbverlauf der scheibe verläuft waagerecht','waagerecht')


def test_direct_artifact_writer_rejects_counts_before_persisting():
    from types import SimpleNamespace
    from src.iCCModules.imageCompositeConverterIterationInitialization import prepareIterationRuntimeImpl
    saved=[]
    setup=SimpleNamespace(emitIterationDescriptionHeaderImpl=lambda **kw:None,
        ensureIterationOutputDirsImpl=lambda **kw:None,
        buildIterationBaseAndLogPathImpl=lambda **kw:('neutral','unused.log'))
    runtime=SimpleNamespace(buildIterationArtifactCallbacksImpl=lambda **kw:dict(
        write_attempt_artifacts=lambda *args,**kw:saved.append(args)))
    result=prepareIterationRuntimeImpl(filename='neutral.png', params=dict(
        language_assertions=description_assertions('Es gibt genau zwei Kreise.')),
        reports_out_dir=None,svg_out_dir='unused',diff_out_dir='unused',target_img=None,width=10,height=10,
        run_seed=0,pass_seed_offset=0,iteration_setup_helpers=setup,iteration_runtime_helpers=runtime,
        time_ns_fn=lambda:0,render_svg_to_numpy_fn=lambda *args:None,
        create_diff_image_fn=None,cv2_module=None)
    writer=result['artifact_callbacks']['write_attempt_artifacts']
    with pytest.raises(DescriptionRejected):
        writer('<svg><circle r="2"/></svg>')
    assert not saved
    writer('<svg><circle r="2"/><circle r="3"/></svg>')
    assert len(saved)==1


def test_reference_inheritance_retains_the_callers_explicit_counts():
    from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
    reflection=Reflection({'neutral':'Wie ZZ1234. Es gibt genau zwei Kreise.'})
    reflection._inherit_mode_from_reference=lambda **kw:('reference',dict(mode='non_composite',elements=[],
        language_assertions=dict(counts=[],no_text=True)))
    _,params=reflection.parse_description('neutral','neutral.png')
    assert params['language_assertions']==dict(counts=[dict(kind='circle',count=2)],no_text=True)
