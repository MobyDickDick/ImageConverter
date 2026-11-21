"""Evidence of real seed-dependent search, not forced differences in output."""
import copy
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest
from PIL import Image

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality, candidate_identity
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterDescriptionRegistration import register_description_ir
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterSearchPortfolio import configured_image_search, search_configuration

ROOT = Path(__file__).resolve().parents[1]


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def run(image, ir, description, seed=17, budget=160):
    h, w = image.shape[:2]
    calls = []
    geometries = []
    def renderer(svg, w, h):
        calls.append(candidate_identity(svg))
        root = ET.fromstring(svg)
        for node in root.iter():
            for paint in ('fill','stroke'):
                node.attrib.pop(paint,None)
        geometries.append(candidate_identity(ET.tostring(root,encoding='unicode')))
        return render(svg, w, h)
    with search_configuration(mode='portfolio', adaptive=True, seed=seed, seconds=30, max_seconds=30):
        with configured_image_search('neutral') as session:
            session.description_assertions = description_assertions(description)
            result = register_description_ir(ir, image=image, description=description,
                svg_fn=lambda ir:geometry.renderGeometryIrToSvgImpl(w,h,ir), render_fn=renderer,
                error_fn=lambda raster:float(abs(image.astype(float)-raster).mean()), max_evaluations=budget)
            return result, calls, dict(session.report(),geometry_candidates=geometries)


@pytest.mark.parametrize('kind', ['rectangle', 'circle', 'triangle'])
def test_wrong_default_paint_is_fitted_without_erasing_declared_shape(kind):
    if kind == 'rectangle':
        description = 'Ein Rechteck.'
        ir = [dict(kind='RectBorder', id='body', bbox=[.2,.2,.6,.6], fill='#e11e48',
                   stroke='#808080', stroke_width=.025)]
        part = '<rect x="10" y="10" width="30" height="30" fill="#dddddd" stroke="#808080" stroke-width="1.25"/>'
    elif kind == 'circle':
        description = 'Ein Kreis.'
        ir = [dict(kind='CircleBackground', id='body', bbox=[.2,.2,.6,.6],
                   fill='#e11e48', stroke='#808080', stroke_width=.025)]
        part = '<circle cx="25" cy="25" r="15" fill="#dddddd" stroke="#808080" stroke-width="1.25"/>'
    else:
        description = 'Ein Dreieck.'
        ir = [dict(kind='PolygonPath', id='body', points=[[.2,.8],[.8,.8],[.5,.2]], closed=True,
                   fill='#e11e48', stroke='#808080', stroke_width=.025)]
        part = '<path d="M 10 40 L 40 40 L 25 10 Z" fill="#dddddd" stroke="#808080" stroke-width="1.25"/>'
    target = render('<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'+part+'</svg>',50,50)
    original = copy.deepcopy(ir)
    result, calls, report = run(target, ir, description)
    assert ir == original
    assert result['quality']['passed']
    validate_svg_assertions(result['svg'], description_assertions(description))
    assert result['final_error'] < result['initial_error']*.1
    assert result['geometry_ir'][0]['fill'] != '#e11e48'
    assert len(calls) == len(set(calls)) == report['candidate_evaluations'] == result['evaluations']


def impossible():
    # Four separate disks cannot be represented by the one declared rectangle.
    part = ''.join(f'<circle cx="{x}" cy="{y}" r="6" fill="#666666"/>'
                   for x,y in ((10,10),(40,10),(10,40),(40,40)))
    image = render('<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'+part+'</svg>',50,50)
    ir = [dict(kind='RectBorder',id='body',bbox=[.2,.2,.6,.6],fill='#e11e48',stroke='#808080',stroke_width=.02)]
    return image, ir


def test_failed_search_changes_real_geometry_across_seeds_and_replays_exactly():
    image, ir = impossible()
    a, calls_a, report_a = run(image, ir, 'Ein Rechteck.', seed=17)
    replay, calls_replay, report_replay = run(image, ir, 'Ein Rechteck.', seed=17)
    b, calls_b, report_b = run(image, ir, 'Ein Rechteck.', seed=18)
    assert not a['quality']['passed'] and not b['quality']['passed']
    assert calls_a == calls_replay and a['svg'] == replay['svg']
    assert set(calls_a) != set(calls_b)  # Different rendered geometry, not only order.
    assert len(set(report_a['geometry_candidates'])) > 5
    assert set(report_a['geometry_candidates']) != set(report_b['geometry_candidates'])
    assert report_a['geometry_candidates'] == report_replay['geometry_candidates']
    assert report_a['render_sequence_sha256'] == report_replay['render_sequence_sha256']
    assert report_a['render_sequence_sha256'] != report_b['render_sequence_sha256']
    assert 40 < len(calls_a) <= 160 and len(calls_a) == len(set(calls_a))
    assert a['restarts'] > 1
    for result in (a,b):
        validate_svg_assertions(result['svg'],description_assertions('Ein Rechteck.'))


def test_missing_inventory_cannot_be_filled_by_extra_raster_objects():
    image, ir = impossible()
    result, calls, _ = run(image, ir, 'Ein Rechteck und ein Kreis.')
    assert result['no_valid_candidate'] and calls == []


@pytest.mark.parametrize('seed',[17,18])
def test_generic_runtime_recovers_reported_image_even_without_special_square_fitter(monkeypatch,seed):
    from tests.test_plain_vertical_square_stem import DESCRIPTION
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0701_L.jpg'))
    h,w = image.shape[:2]
    monkeypatch.setattr(runtime, 'fit_square_stem', lambda *a, **k:None)
    monkeypatch.setattr(runtime, 'scene_reconstruction_fitters', lambda:())
    artifacts, params = [], {}
    with search_configuration(mode='portfolio', adaptive=True,seed=seed,seconds=30,max_seconds=30):
        with configured_image_search('anonymous') as session:
            session.description_assertions = description_assertions(DESCRIPTION)
            result = runtime.runNonCompositeIterationImpl(mode='auto',params=params,stripe_strategy=None,
                semantic_mode_visual_override=False,width=w,height=h,base_name='anonymous',description=DESCRIPTION,
                perc_img=image,img_path='anonymous.jpg',print_fn=lambda *a:None,
                render_embedded_raster_svg_fn=lambda _:None,build_gradient_stripe_svg_fn=lambda *a,**k:None,
                build_gradient_stripe_validation_log_lines_fn=lambda **_:[],write_validation_log_fn=lambda _:None,
                render_svg_to_numpy_fn=render,record_render_failure_fn=lambda *a,**k:None,
                write_attempt_artifacts_fn=lambda svg,raster:artifacts.append((svg,raster)),
                calculate_error_fn=lambda a,b:float(abs(a.astype(float)-b).mean()))
            assert result is not None and artifacts
            svg,raster=artifacts[-1]
            assert pixel_quality(image,raster)['passed']
            validate_svg_assertions(svg,description_assertions(DESCRIPTION))
            assert session.report()['candidate_evaluations'] > 40
            assert session.validated
    assert params['geometry_ir_optimizer_result']['restarts'] > 1


def test_real_gui_failed_retries_record_different_searches(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    from tests.test_plain_vertical_square_stem import DESCRIPTION
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda:{})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    monkeypatch.setattr(jobs, 'publish_best', lambda *args:None)
    image, _ = impossible()
    data = io.BytesIO()
    Image.fromarray(image[:,:,::-1]).save(data,format='PNG')
    traces = []
    try:
        for seed in (17,18):
            uploaded = jobs.upload('independent_failure.png',data.getvalue())
            started = jobs.start(uploaded['id'],DESCRIPTION,'quick',seed=seed,use_current_svg=False)
            jobs.threads[-1].join(timeout=55)
            result = jobs.snapshot(started['id'])
            assert result['status'] != 'running' and result['quality'] != 'passed',result
            assert result['search_summary']['candidate_evaluations'] > 40,result
            records = [json.loads(line) for line in
                (jobs.folder(started['id'])/'output/search/progress.jsonl').read_text().splitlines()]
            final = next(r for r in reversed(records) if r['event']=='image_search_finished')
            traces.append(final['render_sequence_sha256'])
            if result.get('result'):
                validate_svg_assertions((jobs.folder(started['id'])/'result.svg').read_text(),
                                        description_assertions(DESCRIPTION))
        assert traces[0] != traces[1]
    finally:
        jobs.close()
