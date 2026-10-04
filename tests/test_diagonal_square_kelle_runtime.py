from pathlib import Path
import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterInteriorMark import fit_rectilinear_interior_mark
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterSemantic import apply_semantic_badge_description_rules
from tools.evaluate_diagonal_square_kelle_recheck import measure, square_and_right_stem_semantics
from tools.review_conversion_quality import normalized_mse


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Kelle mit Quadrat anstelle von Kreis oben. Geometrische Variante: '
               'Hauptdiagonal gespiegelt. Der Griff liegt auf einer Symmetrieachse des Kreises.')


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def convert(image, name, monkeypatch):
    artifacts, logs = [], []
    height, width = image.shape[:2]

    def forbid_sample(**kwargs):
        pytest.fail('Square topology must bypass sample lookup')

    monkeypatch.setattr(runtime, '_try_load_sample_svg', forbid_sample)
    result = runtime.runNonCompositeIterationImpl(
        mode='non_composite', params={'mode': 'non_composite'}, stripe_strategy=None,
        semantic_mode_visual_override=False, width=width, height=height, base_name=name,
        description=DESCRIPTION, perc_img=image, img_path=f'{name}.jpg', print_fn=lambda *args: None,
        render_embedded_raster_svg_fn=lambda path: None,
        build_gradient_stripe_svg_fn=lambda *args, **kwargs: None,
        build_gradient_stripe_validation_log_lines_fn=lambda **kwargs: [],
        write_validation_log_fn=logs.append, render_svg_to_numpy_fn=render,
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, raster: artifacts.append((svg, raster)),
        calculate_error_fn=lambda target, raster: normalized_mse(target, raster)[0],
    )
    assert result is not None
    assert 'non_composite_selection=semantic_description_geometry' in logs[-1]
    return artifacts[-1]


@pytest.mark.parametrize('phrase', ['Hauptdiagonal gespiegelt', 'an der Hauptdiagonale gespiegelt'])
def test_parser_reflects_existing_square_topology_without_catalog_or_label(phrase):
    upright = geometry.buildGeometryIrFromDescriptionImpl('Kelle mit Quadrat oben')[0]
    ir = geometry.buildGeometryIrFromDescriptionImpl('Kelle mit Quadrat oben, '+phrase)
    assert len(ir) == 1
    element = ir[0]
    x, y, w, h = upright['body_bbox']
    assert element['body_bbox'] == [y, x, h, w]
    assert element['connector'] == [[py, px] for px, py in upright['connector']]
    assert element['transform']['mirror_axis'] == 'main_diagonal'
    assert element['primitive_decomposition']['orientation'] == 'left'
    assert 'label' not in element
    params = {'geometry_ir': ir}
    assert not apply_semantic_badge_description_rules(desc=DESCRIPTION, params=params)


@pytest.mark.parametrize('size', ['S', 'M', 'L'])
def test_runtime_recovers_connected_square_and_observed_mark_at_multiple_sizes(size, monkeypatch):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/AC0724_1_{size}.jpg'))
    assert image is not None
    svg, raster = convert(image, 'anonymous_square', monkeypatch)
    assert square_and_right_stem_semantics(svg) == 1.
    assert '<circle' not in svg and '<text' not in svg and '<image' not in svg
    assert 'raster_interior_mark' in svg
    assert normalized_mse(image, raster)[1] < .004


def test_runtime_is_invariant_to_filename(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0724_1_S.jpg'))
    svg, raster = convert(image, 'AC0724_1_S', monkeypatch)
    renamed_svg, renamed_raster = convert(image, 'unrelated_holdout', monkeypatch)
    assert svg == renamed_svg
    np.testing.assert_array_equal(raster, renamed_raster)


@pytest.mark.parametrize('scale', [1, 2])
@pytest.mark.parametrize('mark', ['bar_and_stem', 'none', 'diagonal'])
def test_observation_generalizes_color_position_scale_and_rejects_other_topologies(scale, mark):
    width, height = 60*scale, 40*scale
    ir = geometry.buildGeometryIrFromDescriptionImpl('Kelle mit Quadrat, Hauptdiagonal gespiegelt')
    body = ir[0]
    body.update(body_bbox=[.1, .1, .5, .75], connector=[[.6, .475], [.95, .475]], body_fill='#244ca0')
    svg = geometry.renderGeometryIrToSvgImpl(width, height, ir)
    if mark == 'bar_and_stem':
        path = f'M {15*scale} {10*scale} H {28*scale} V {13*scale} H {23*scale} V {28*scale} H {20*scale} V {13*scale} H {15*scale} Z'
    else:
        path = f'M {15*scale} {10*scale} L {28*scale} {28*scale} L {25*scale} {28*scale} Z'
    if mark != 'none':
        svg = svg.replace('</svg>', f'<path d="{path}" fill="#f4e6cc"/></svg>')
    image = render(svg, width, height)
    fitted = fit_rectilinear_interior_mark(ir, image=image, description=DESCRIPTION,
        render_fn=lambda candidate: render(geometry.renderGeometryIrToSvgImpl(width, height, candidate), width, height),
        error_fn=lambda raster: normalized_mse(image, raster)[0])
    if mark == 'bar_and_stem':
        assert fitted is not None
        assert fitted['final_error'] < fitted['initial_error']*.1
        assert fitted['geometry_ir'][-1]['fill'] == '#f4e6cc'
    else:
        assert fitted is None


def test_explicit_absence_of_mark_is_a_hard_constraint():
    ir = geometry.buildGeometryIrFromDescriptionImpl('Kelle mit Quadrat, Hauptdiagonal gespiegelt')
    assert fit_rectilinear_interior_mark(ir, image=np.zeros((15, 25, 3), np.uint8),
        description=DESCRIPTION+' Ohne Text.', render_fn=lambda _: pytest.fail('must not render'),
        error_fn=lambda _: pytest.fail('must not score')) is None


def test_quality_metrics_calibrate_to_perfect_saved_svg(tmp_path):
    source = ('<svg xmlns="http://www.w3.org/2000/svg" width="30" height="20">'
              '<path d="M 18 10 L 30 10" stroke="#808080" stroke-width="2"/>'
              '<rect x="2" y="2" width="16" height="16" fill="#cf2348"/></svg>')
    svg_path, image_path = tmp_path/'perfect.svg', tmp_path/'perfect.png'
    svg_path.write_text(source, encoding='utf-8')
    assert cv2.imwrite(str(image_path), render(source, 30, 20))
    measured = measure(image_path, svg_path)
    assert measured['mean_delta2'] == 0.
    assert measured['metrics'] == {'error_per_pixel': 0., 'edge_alignment': 1., 'object_mask_iou': 1.,
                                   'semantic_score': 1., 'dimension_match': 1.}
    broken = source.replace('M 18 10 L 30 10', 'M 20 10 L 30 10')
    assert square_and_right_stem_semantics(broken) == 0.
    wrong_side = source.replace('M 18 10 L 30 10', 'M 2 10 L 0 10')
    assert square_and_right_stem_semantics(wrong_side) == 0.


def test_mark_semantics_rejects_outside_or_nonorthogonal_path():
    source = ('<svg width="30" height="20">'
              '<path d="M 18 10 L 30 10" stroke="#808080"/>'
              '<rect x="2" y="2" width="16" height="16" fill="#cf2348"/>'
              '<path d="M 5 5 L 15 5 L 15 7 L 11 7 L 11 15 L 9 15 L 9 7 L 5 7 Z" fill="white"/></svg>')
    assert square_and_right_stem_semantics(source) == 1.
    assert square_and_right_stem_semantics(source.replace('M 5 5', 'M 0 5')) == 0.
    assert square_and_right_stem_semantics(source.replace('L 15 5', 'L 15 6')) == 0.


def test_recheck_runner_rejects_stale_cli_outputs(tmp_path, monkeypatch):
    import sys
    from tools.run_diagonal_square_kelle_recheck import main

    manifest = tmp_path/'manifest.json'
    manifest.write_text('{}', encoding='utf-8')
    output = tmp_path/'used_output'
    (output/'before').mkdir(parents=True)
    monkeypatch.setattr(sys, 'argv', ['recheck', str(manifest), '--output-dir', str(output)])
    with pytest.raises(ValueError, match='fresh output directory'):
        main()
