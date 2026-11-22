"""Description paint claims constrain fresh searches and reused native SVGs."""
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterSceneProgram import scene_program, program_svg, STRIDE
from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
    description_assertions, validate_svg_assertions, draft_assertions,
)
from src.iCCModules.imageCompositeConverterScopedPaint import constrain_parameters


@pytest.mark.parametrize('noun,kind', [('Dreiecke','triangle'), ('Kreise','circle'),
                                     ('Rechtecke','rect'), ('Ellipsen','ellipse'), ('Quadrate','square')])
def test_scoped_claims_apply_to_other_shape_families(noun, kind):
    description = (f'Zwei {noun}. Beide {noun} haben gleich breite Ränder. '
                   f'Beide {noun} haben je einen Farbübergang (hellgrau nach dunkelgrau).')
    program = scene_program(description)
    assert program is not None
    assert len(program['objects']) == 2
    assert all(obj['kind'] == kind for obj in program['objects'])
    parameters = np.full((2,STRIDE), .5)
    parameters[:,0] = [.25,.75]
    parameters[:,2:4] = [.2,.3]
    parameters[:,5] = [.2,.8]
    svg = program_svg(program, parameters, 100,100)
    assertions = description_assertions(description)
    validate_svg_assertions(svg, assertions)
    # No producer marker or primitive IDs may bypass the paint check.
    root = ET.fromstring(svg)
    root.attrib.pop('data-primitive-scene')
    for node in root:
        if node.tag.rsplit('}',1)[-1] in {'circle','ellipse','polygon','rect'}:
            node.attrib.pop('id',None)
    validate_svg_assertions(ET.tostring(root,encoding='unicode'), assertions)


DESCRIPTION = ('Ein Kreis und zwei Dreiecke. Beide Dreiecke haben gleich breite Ränder. '
               'Beide Dreiecke haben je einen Farbverlauf (hellgrau nach dunkelgrau).')


def valid_scene():
    program = scene_program(DESCRIPTION)
    parameters = np.full((3,STRIDE), .5)
    parameters[:,0] = [.2,.5,.8]
    parameters[:,2:4] = .15
    parameters[:,5] = [.1,.2,.8]
    return ET.fromstring(program_svg(program,parameters,100,100))


@pytest.mark.parametrize('change,error', [('border','unequal_borders'), ('solid','missing_gradient'),
                                        ('constant','constant_gradient'), ('color','wrong_gradient_colors')])
def test_rejected_for_every_output_path_including_drafts(change,error):
    root=valid_scene()
    triangles=root.findall('{*}polygon')
    gradient=root.find('{*}defs/{*}linearGradient')
    if change=='border':
        triangles[1].set('stroke-width','9')
    elif change=='solid':
        triangles[0].set('fill','#bbbbbb')
    elif change=='constant':
        for stop in gradient:
            stop.set('stop-color','#aaaaaa')
    else:
        gradient[0].set('stop-color','#ff0000')
    root.attrib.pop('data-primitive-scene')
    svg=ET.tostring(root,encoding='unicode')
    assertions=description_assertions(DESCRIPTION)
    for contract in (assertions,draft_assertions(assertions)):
        with pytest.raises(ValueError,match=error):
            validate_svg_assertions(svg,contract)


def test_equal_width_is_scoped_and_measured_after_transforms():
    root=valid_scene()
    # The circle is allowed its own width.
    validate_svg_assertions(ET.tostring(root,encoding='unicode'),description_assertions(DESCRIPTION))
    root.findall('{*}polygon')[1].set('transform','scale(2)')
    with pytest.raises(ValueError,match='unequal_borders'):
        validate_svg_assertions(ET.tostring(root,encoding='unicode'),description_assertions(DESCRIPTION))


def test_scoped_properties_are_independent_search_parameters_until_declared():
    parameters=np.full((2,STRIDE),.5)
    parameters[:,5]=[.2,.8]
    ordinary=scene_program('Zwei Dreiecke.')
    projected=constrain_parameters(ordinary,parameters).reshape(2,STRIDE)
    assert np.array_equal(projected,parameters)
    program=scene_program('Zwei Dreiecke. Beide Dreiecke haben gleich breite Ränder.')
    projected=constrain_parameters(program,parameters).reshape(2,STRIDE)
    assert projected[0,5]==projected[1,5]


def test_unsupported_qualifiers_are_not_consumed_as_implemented_claims():
    assert scene_program('Zwei Dreiecke. Beide Dreiecke haben je einen Farbverlauf (rot nach blau).') is None
    assert scene_program('Zwei Dreiecke. Beide Dreiecke haben gleich breite Ränder, ausser oben schwarz.') is None


def test_old_failed_paint_cannot_win_project_comparison(tmp_path,monkeypatch):
    from src import imageConverterGui as gui
    from PIL import Image
    import io
    output=io.BytesIO()
    Image.new('RGB',(100,100),'white').save(output,format='PNG')
    jobs=gui.Jobs(tmp_path/'jobs')
    jobs.project_directory=tmp_path/'project'
    try:
        uploaded=jobs.upload('neutral.png',output.getvalue())
        job=jobs.jobs[uploaded['id']]
        job.update(description=DESCRIPTION,status='done',result=True,quality='passed')
        root=valid_scene()
        result=jobs.folder(job['id'])/'result.svg'
        result.write_text(ET.tostring(root,encoding='unicode'),encoding='utf-8')
        project=jobs.project_svg(job)
        project.parent.mkdir(parents=True)
        root.findall('{*}polygon')[1].set('stroke-width','9')
        project.write_text(ET.tostring(root,encoding='unicode'),encoding='utf-8')
        # Even a numerically better raster fit cannot override explicit claims.
        quality=dict(passed=True,observed_foreground_pixels=20,output_foreground_pixels=20,
                     normalized_mse=.001,foreground_mse=.01,foreground_iou=.95,edge_alignment=.9)
        monkeypatch.setattr(gui,'saved_svg_quality',lambda *args:dict(quality))
        jobs.publish_best(job['id'])
        assert job['project_save']['status']=='saved'
        assert project.read_bytes()==result.read_bytes()
    finally:
        jobs.close()


def test_native_sample_is_a_starting_point_with_projected_shared_borders():
    from src.iCCModules.imageCompositeConverterSceneProgram import sample_parameters
    root=valid_scene()
    triangles=root.findall('{*}polygon')
    triangles[0].set('stroke-width','1')
    triangles[1].set('stroke-width','5')
    program=scene_program(DESCRIPTION)
    values=sample_parameters(program,ET.tostring(root,encoding='unicode'),100,100).reshape(3,STRIDE)
    assert values[1,5]==values[2,5]==.3
    validate_svg_assertions(program_svg(program,values,100,100),description_assertions(DESCRIPTION))


def test_sample_worker_keeps_rgb_reference_and_uses_scoped_search(tmp_path):
    from PIL import Image
    from src.imageConverterSample import refine,render_svg
    from src.imageConverterGui import collect_sample_result
    root=valid_scene()
    svg=ET.tostring(root,encoding='unicode')
    sample=tmp_path/'sample.svg'; sample.write_text(svg,encoding='utf-8')
    source=tmp_path/'source.png'
    Image.fromarray(render_svg(svg,100,100)).save(source)
    output=tmp_path/'output/refined.svg'
    result=refine(source,sample,output,DESCRIPTION,3,seed=17)
    assert result['result'] and result['passed']
    assert result['primitive_evolution']['operators']['template_initialization']==1
    assert result['search_context']['render_budget']==4096
    assert result['search_context']['full_scene_validations']==1
    validate_svg_assertions(output.read_text(),description_assertions(DESCRIPTION))
    job=dict(description=DESCRIPTION,width=100,height=100)
    collect_sample_result(tmp_path,job,0)
    assert job['status']=='done' and job['quality']=='passed'


def test_declared_gradient_cannot_be_hidden_in_definitions_or_metadata():
    root=valid_scene()
    root.findall('{*}polygon')[1].set('fill','#aaaaaa')
    root.findall('{*}polygon')[1].set('data-role','background')
    with pytest.raises(ValueError,match='missing_gradient'):
        validate_svg_assertions(ET.tostring(root,encoding='unicode'),description_assertions(DESCRIPTION))


def test_constrained_search_keeps_seeded_geometry_diversity(tmp_path):
    import cv2
    import fitz
    from src.iCCModules.imageCompositeConverterPrimitiveEvolution import evolve_primitives
    from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
    image=np.repeat(((np.indices((24,32)).sum(axis=0)%4<2)*180+40).astype('uint8')[:,:,None],3,axis=2)
    description='Zwei Dreiecke. Beide Dreiecke haben gleich breite Ränder.'
    traces=[]
    for index,seed in enumerate((17,17,18)):
        def render(svg,w,h):
            return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)
        result=evolve_primitives(image,description,render,seed=seed,directory=tmp_path/str(index),
                                seconds=10,max_evaluations=64)
        traces.append(result['search_report']['trace_hash'])
        assert result['search_report']['evaluations']==64
        validate_svg_assertions(result['svg'],description_assertions(description))
    assert traces[0]==traces[1] and traces[0]!=traces[2]


def test_ordinary_dispatch_uses_complete_paint_contract_before_legacy_model():
    import inspect
    from src.iCCModules.imageCompositeConverterIterationDispatch import runPreparedIterationModeImpl
    arguments={key:None for key in inspect.signature(runPreparedIterationModeImpl).parameters}
    expected=object()
    arguments.update(mode='composite',description=DESCRIPTION,params={},
                     run_non_composite_iteration_fn=lambda **kwargs:expected)
    assert runPreparedIterationModeImpl(**arguments) is expected
