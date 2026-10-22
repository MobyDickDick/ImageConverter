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
