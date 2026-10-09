from pathlib import Path
import base64
import json
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterFilledSymbols import fit_disk_bar, fit_solid_arrow
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess, _expand_bezier_linear_gradients_for_fitz
from tools.evaluate_disk_bar_recheck import symbol_semantics
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT/'artifacts/evaluation/disk_bar_recheck_v1/manifest.json').read_text(encoding='utf-8'))
DISK = MANIFEST['cases'][1]['description']
ARROW = MANIFEST['cases'][0]['description']


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, family='disk_bar', description=None, **kwargs):
    h, w = image.shape[:2]
    function = fit_disk_bar if family == 'disk_bar' else fit_solid_arrow
    return function(w, h, description=description or (DISK if family == 'disk_bar' else ARROW), image=image,
                    render_fn=kwargs.get('render_fn', render),
                    error_fn=kwargs.get('error_fn', lambda a, b: normalized_mse(a, b)[0]))


def disk_svg(scale=1, shift=0, color='#295d85'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{80*scale}" height="{70*scale}">'
            '<defs><linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#c0d8eb"/><stop offset="1" stop-color="#719ebd"/>'
            '</linearGradient></defs>'
            f'<rect width="{80*scale}" height="{70*scale}" fill="#ffffff"/>'
            f'<circle cx="{(38+shift)*scale}" cy="{34*scale}" r="{27*scale}" fill="url(#shade)" stroke="#d2dde5" stroke-width="{1.5*scale}"/>'
            f'<rect x="{(22+shift)*scale}" y="{30*scale}" width="{32*scale}" height="{8*scale}" rx="{4*scale}" fill="{color}" stroke="#e0e8ef" stroke-width="{scale}"/></svg>')


def arrow_svg(scale=1, shift=0, color='#285e7b'):
    points = [(27+shift, 8), (43+shift, 8), (43+shift, 32), (55+shift, 32),
              (35+shift, 58), (15+shift, 32), (27+shift, 32)]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{80*scale}" height="{70*scale}">'
            f'<rect width="{80*scale}" height="{70*scale}" fill="#ffffff"/>'
            '<polygon points="'+' '.join(f'{x*scale},{y*scale}' for x, y in points)+f'" fill="{color}"/></svg>')


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_anonymous_catalog_rasters_fit_without_mutating_inputs(case):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    original = image.copy()
    result = fit(image, case['family'], case['description'])
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert normalized_mse(image, result['rendered'])[1] < .005
    assert symbol_semantics(result['svg'], case['family']) == 1
    assert result['evaluations'] <= 1+16*len(result['parameters'])
    assert '<image' not in result['svg']
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('family', ['disk_bar', 'solid_down_arrow'])
@pytest.mark.parametrize('scale,shift,color', [(1, 0, '#285e7b'), (1, 7, '#67382d'), (2, -4, '#286044')])
def test_independent_geometry_colors_and_resolution(family, scale, shift, color):
    source = disk_svg if family == 'disk_bar' else arrow_svg
    image = render(source(scale, shift, color), 80*scale, 70*scale)
    result = fit(image, family)
    assert result is not None
    assert symbol_semantics(result['svg'], family) == 1
    assert normalized_mse(image, result['rendered'])[1] < .004


@pytest.mark.parametrize('family', ['disk_bar', 'solid_down_arrow'])
@pytest.mark.parametrize('failure', ['render', 'nan', 'infinity'])
def test_failed_measurements_are_not_accepted(family, failure):
    image = render((disk_svg if family == 'disk_bar' else arrow_svg)(), 80, 70)
    kwargs = {'render_fn': lambda *args: None} if failure == 'render' else {'error_fn': lambda *args: float(failure if failure == 'nan' else 'inf')}
    assert fit(image, family, **kwargs) is None


@pytest.mark.parametrize('mutation', ['missing', 'extra', 'vertical', 'square', 'offcenter'])
def test_incompatible_disk_evidence_is_rejected(mutation):
    svg = disk_svg()
    root = ET.fromstring(svg)
    bar = list(root)[-1]
    if mutation == 'missing':
        root.remove(bar)
    elif mutation == 'extra':
        ET.SubElement(root, 'rect', x='3', y='3', width='6', height='6', fill='#000000')
    elif mutation == 'vertical':
        bar.set('width', '8'); bar.set('height', '32'); bar.set('x', '34'); bar.set('y', '18')
    elif mutation == 'square':
        bar.set('rx', '0')
    else:
        bar.set('y', '18')
    assert fit(render(ET.tostring(root, encoding='unicode'), 80, 70)) is None


@pytest.mark.parametrize('description', ['Ein Kreis.', DISK+' Zusätzlich ein Dreieck.', DISK+' ohne Balken.'])
def test_description_constraints_reject_incompatible_disk(description):
    assert fit(render(disk_svg(), 80, 70), description=description) is None


@pytest.mark.parametrize('family', ['disk_bar', 'solid_down_arrow'])
def test_runtime_rename_invariance_and_precedence(monkeypatch, family):
    image = render((disk_svg if family == 'disk_bar' else arrow_svg)(), 80, 70)
    def forbidden(*args, **kwargs):
        pytest.fail('Registered filled symbol must bypass reference SVGs and embedding')
    monkeypatch.setattr(runtime, '_try_load_sample_svg', forbidden)
    outputs = []
    for name in ('arbitrary_input', 'renamed_input'):
        logs = []
        runtime.runNonCompositeIterationImpl(mode='non_composite', params={}, stripe_strategy=None,
            semantic_mode_visual_override=False, width=80, height=70, base_name=name,
            description=DISK if family == 'disk_bar' else ARROW, perc_img=image, img_path=name+'.png',
            print_fn=lambda *args: None, render_embedded_raster_svg_fn=forbidden,
            build_gradient_stripe_svg_fn=forbidden, build_gradient_stripe_validation_log_lines_fn=forbidden,
            write_validation_log_fn=logs.append, render_svg_to_numpy_fn=render,
            record_render_failure_fn=forbidden, write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
            calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])
        assert logs == [[f'status=non_composite_raster_{family if family == "disk_bar" else "solid_arrow"}']]
    assert outputs[0] == outputs[1]


def test_both_catalogs_distinguish_base_arrow_and_disk_sizes():
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    for directory in ('descriptions', 'images_to_convert'):
        mapping = loadDescriptionMappingImpl(str(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml'),
                                            get_base_name_from_file_fn=getBaseNameFromFileImpl)
        assert mapping['GE0032'] == ARROW
        for suffix in ('L', 'M', 'S'):
            assert mapping['GE0032_'+suffix] == DISK


@pytest.mark.parametrize('kind', ['circle', 'ellipse'])
@pytest.mark.parametrize('horizontal', [False, True])
def test_native_linear_gradient_rendering_has_exact_mask_and_color(kind, horizontal):
    shape = '<circle cx="40" cy="35" r="24"' if kind == 'circle' else '<ellipse cx="40" cy="35" rx="26" ry="19"'
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="80" height="70">'
           f'<defs><linearGradient id="s" x1="0" y1="0" x2="{int(horizontal)}" y2="{int(not horizontal)}">'
           '<stop offset="0" stop-color="#cc8844"/><stop offset="1" stop-color="#4488cc"/>'
           '</linearGradient></defs><rect width="80" height="70" fill="#ffffff"/>'+shape+' fill="url(#s)"/></svg>')
    gradient = render(svg, 80, 70)
    flat = render(svg.replace('fill="url(#s)"', 'fill="#888888"'), 80, 70)
    # Verify the private paint alpha against the exact native shape. Comparing
    # almost-white RGB pixels instead would measure final color quantization.
    private = ET.fromstring(_expand_bezier_linear_gradients_for_fitz(svg, fitz_module=fitz, size_w=80, size_h=70))
    paint = next(e for e in private.iter() if e.tag.endswith('image'))
    pix = fitz.Pixmap(base64.b64decode(paint.get('href').split(',', 1)[1]))
    alpha = np.frombuffer(pix.samples, dtype=np.uint8).reshape(70, 80, 4)[:, :, 3]
    mask = ('<svg xmlns="http://www.w3.org/2000/svg" width="80" height="70">'+shape+' fill="#ffffff"/></svg>')
    with fitz.open(stream=mask.encode(), filetype='svg') as doc:
        native = doc[0].get_pixmap(alpha=True)
    expected = np.frombuffer(native.samples, dtype=np.uint8).reshape(70, 80, 4)[:, :, 3]
    np.testing.assert_array_equal(alpha, expected)
    assert np.min(gradient[35, 40]) > 60
    a, b = (gradient[35, 23], gradient[35, 57]) if horizontal else (gradient[22, 40], gradient[48, 40])
    assert a[2] > b[2]+40 and a[0]+40 < b[0]


def test_semantic_checker_rejects_missing_or_shifted_bar_and_wrong_arrow_direction():
    assert symbol_semantics(disk_svg(), 'disk_bar') == 1
    assert symbol_semantics(disk_svg().replace('y="30"', 'y="14"'), 'disk_bar') == 0
    assert symbol_semantics(disk_svg().replace('rx="4"', 'rx="0"'), 'disk_bar') == 0
    assert symbol_semantics(arrow_svg(), 'solid_down_arrow') == 1
    assert symbol_semantics(arrow_svg().replace('35,58', '35,4'), 'solid_down_arrow') == 0


@pytest.mark.parametrize('mutation', ['missing_shaft', 'extra_object', 'upward', 'disconnected'])
def test_incompatible_arrow_rasters_are_rejected(mutation):
    svg = arrow_svg()
    if mutation == 'missing_shaft':
        svg = svg.replace('27,8 43,8 43,32 55,32 35,58 15,32 27,32', '15,32 55,32 35,58')
    elif mutation == 'extra_object':
        svg = svg.replace('</svg>', '<circle cx="68" cy="10" r="4" fill="#222222"/></svg>')
    elif mutation == 'upward':
        root = ET.fromstring(svg)
        shape = list(root)[-1]
        shape.set('points', ' '.join(f'{x},{70-float(y)}' for x, y in
                                    (p.split(',') for p in shape.get('points').split())))
        svg = ET.tostring(root, encoding='unicode')
    else:
        svg = svg.replace('</svg>', '<rect x="20" y="29" width="30" height="4" fill="#ffffff"/></svg>')
    assert fit(render(svg, 80, 70), 'solid_down_arrow') is None


@pytest.mark.parametrize('family', ['disk_bar', 'solid_down_arrow'])
def test_perfect_synthetic_vector_calibrates_both_gates(tmp_path, family):
    from tools.evaluate_disk_bar_recheck import measure
    from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
    svg = (disk_svg if family == 'disk_bar' else arrow_svg)()
    image = tmp_path/'source.png'
    vector = tmp_path/'source.svg'
    cv2.imwrite(str(image), render(svg, 80, 70))
    vector.write_text(svg, encoding='utf-8')
    record = measure(image, vector, family)
    assert record['metrics'] == {'error_per_pixel': 0., 'edge_alignment': 1.,
                                 'object_mask_iou': 1., 'semantic_score': 1., 'dimension_match': 1.}
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {'commit': 'synthetic', 'seed': 0, 'toolchain': 'current', 'input_hashes': {'case': 'synthetic'}},
        'cases': {'case': {'metrics': record['metrics'], 'dimensions': record['dimensions']}}})
    assert evaluate_satisfaction(baseline, {'case': record})['cases'][0]['satisfactory']
