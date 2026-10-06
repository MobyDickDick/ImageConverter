from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterRadialDisk import fit_radial_disk
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_radial_disk_recheck import radial_disk_semantics, measure
from tools.review_conversion_quality import normalized_mse

DESCRIPTION = ('Kugelform: ein gefüllter Kreis mit radialem Farbverlauf, innen hell '
               'und außen dunkler, auf weißem Hintergrund.')
ROOT = Path(__file__).resolve().parents[1]


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, error_fn=None, render_fn=render):
    h, w = image.shape[:2]
    return fit_radial_disk(w, h, description=description, image=image, render_fn=render_fn,
                           error_fn=error_fn or (lambda a, b: normalized_mse(a, b)[0]))


def source_svg(scale=1, color='#335577'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{60*scale}" height="{50*scale}">'
            '<defs><radialGradient id="shade"><stop offset="0" stop-color="#dddddd"/>'
            f'<stop offset="0.6" stop-color="#8899aa"/><stop offset="1" stop-color="{color}"/>'
            '</radialGradient></defs>'
            f'<rect width="{60*scale}" height="{50*scale}" fill="#ffffff"/>'
            f'<circle cx="{35*scale}" cy="{23*scale}" r="{18*scale}" fill="url(#shade)"/></svg>')


@pytest.mark.parametrize('variant', [f'GE028{i}' for i in range(6)])
def test_disk_fits_color_holdouts_from_pixels_without_mutation(variant):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/{variant}.jpg'))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] < result['initial_error']
    assert normalized_mse(image, result['rendered'])[1] < .004
    assert radial_disk_semantics(result['svg']) == 1
    assert result['evaluations'] <= 145
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale', [1, 2])
@pytest.mark.parametrize('color', ['#335577', '#775533'])
def test_svg_raster_svg_generalizes_size_location_and_color(scale, color):
    image = render(source_svg(scale, color), 60*scale, 50*scale)
    result = fit(image)
    assert result is not None
    assert radial_disk_semantics(result['svg']) == 1
    assert normalized_mse(image, result['rendered'])[1] < .003
    assert abs(result['parameters'][0]-35*scale) < 1
    assert abs(result['parameters'][1]-23*scale) < 1


@pytest.mark.parametrize('variant', ['GE0280', 'GE0281'])
def test_runtime_bypasses_samples_and_embedding_and_is_rename_invariant(monkeypatch, variant):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/{variant}.jpg'))
    catalog = ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml')
    description = next(e.findtext('beschreibung') for e in catalog.iter('entry') if e.get('key') == variant)
    h, w = image.shape[:2]
    def forbidden(*args, **kwargs):
        pytest.fail('Disk registration must bypass sample SVGs and raster embedding')
    monkeypatch.setattr(runtime, '_try_load_sample_svg', forbidden)
    outputs = []
    for name in (variant, 'renamed_color_patch'):
        logs = []
        result = runtime.runNonCompositeIterationImpl(
            mode='non_composite', params={}, stripe_strategy=None, semantic_mode_visual_override=False,
            width=w, height=h, base_name=name, description=description, perc_img=image, img_path=name+'.jpg',
            print_fn=lambda *args: None, render_embedded_raster_svg_fn=forbidden,
            build_gradient_stripe_svg_fn=forbidden, build_gradient_stripe_validation_log_lines_fn=forbidden,
            write_validation_log_fn=logs.append, render_svg_to_numpy_fn=render,
            record_render_failure_fn=forbidden, write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
            calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])
        assert result is not None
        assert logs == [['status=non_composite_raster_radial_disk']]
    assert outputs[0] == outputs[1]
    assert '<image' not in outputs[0]
    assert '<text' not in outputs[0]
    assert radial_disk_semantics(outputs[0]) == 1


@pytest.mark.parametrize('description', ['Hellgraues Quadrat.', DESCRIPTION+' mit Text',
                                         DESCRIPTION+' mit Griff', DESCRIPTION+' Zusätzlich ein Dreieck',
                                         DESCRIPTION.replace('innen hell', 'innen dunkel'),
                                         DESCRIPTION.replace('außen dunkler', 'außen hell')])
def test_incompatible_descriptions_reject_disk(description):
    assert fit(render(source_svg(), 60, 50), description) is None


@pytest.mark.parametrize('mutation', ['flat', 'hole', 'second', 'ellipse'])
def test_missing_radial_evidence_and_extra_objects_are_rejected(mutation):
    svg = source_svg()
    if mutation == 'flat':
        svg = svg.replace('fill="url(#shade)"', 'fill="#335577"')
    elif mutation == 'ellipse':
        svg = svg.replace('<circle ', '<ellipse ').replace('r="18"', 'rx="18" ry="9"')
    elif mutation == 'second':
        svg = svg.replace('</svg>', '<circle cx="5" cy="5" r="3" fill="#335577"/></svg>')
    image = render(svg, 60, 50)
    if mutation == 'hole':
        image[18:29, 30:41] = 0
    assert fit(image) is None


@pytest.mark.parametrize('error', [42., float('nan'), float('inf')])
def test_non_improving_and_nonfinite_error_reject_registration(error):
    assert fit(render(source_svg(), 60, 50), error_fn=lambda a, b: error) is None


def test_render_failure_and_invalid_pixels_reject_registration():
    image = render(source_svg(), 60, 50)
    assert fit(image, render_fn=lambda *args: None) is None
    assert fit(np.full_like(image, np.nan, dtype=float)) is None


def test_gate_metrics_calibrate_a_perfect_saved_pair(tmp_path):
    svg = source_svg()
    image_path, svg_path = tmp_path/'target.png', tmp_path/'result.svg'
    assert cv2.imwrite(str(image_path), render(svg, 60, 50))
    svg_path.write_text(svg, encoding='utf-8')
    assert measure(image_path, svg_path)['metrics'] == {
        'error_per_pixel': 0., 'edge_alignment': 1., 'object_mask_iou': 1.,
        'semantic_score': 1., 'dimension_match': 1.}


@pytest.mark.parametrize('wrong', [
    lambda s: s.replace('<radialGradient ', '<linearGradient ').replace('</radialGradient>', '</linearGradient>'),
    lambda s: s.replace('<radialGradient ', '<radialGradient cx="20%" '),
    lambda s: s.replace('stop-color="#dddddd"', 'stop-color="#335577"'),
    lambda s: s.replace('<circle ', '<circle transform="translate(1 0)" '),
    lambda s: s.replace('r="18"', 'r="45"'),
    lambda s: s.replace('</svg>', '<image href="data:image/png;base64,AA=="/></svg>'),
    lambda s: s.replace('</svg>', '<circle cx="5" cy="5" r="3"/></svg>'),
])
def test_semantics_rejects_wrong_gradient_geometry_and_embedding(wrong):
    assert radial_disk_semantics(wrong(source_svg())) == 0
