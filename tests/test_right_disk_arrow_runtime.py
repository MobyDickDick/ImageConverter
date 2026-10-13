"""A described horizontal direction must agree with measured arrow evidence."""
from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterDiskArrow import fit_disk_arrow
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from tools.evaluate_disk_arrow_recheck import symbol_semantics
from tools.run_plan_b_variations import render, measure_quality
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/right_disk_arrow_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    h, w = image.shape[:2]
    return fit_disk_arrow(w, h, description=description, image=image,
                          render_fn=kwargs.get('render_fn', render),
                          error_fn=kwargs.get('error_fn', lambda a, b: normalized_mse(a, b)[0]))


def test_actual_raster_passes_both_direction_and_strict_pixel_contract():
    image = cv2.imread(str(EVIDENCE/MANIFEST['cases'][0]['image']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert symbol_semantics(result['svg'], 'right') == 1
    assert symbol_semantics(result['svg'], 'left') == 0
    assert measure_quality(image, result['svg'])['satisfactory']
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale,shift,reverse', [(.5, 0, False), (1, -4, False),
                                                (2, 5, False), (1, 0, True)])
def test_independent_geometry_resolution_and_gradient_direction(scale, shift, reverse):
    root = ET.fromstring(INDEPENDENT)
    root.set('width', str(104*scale)); root.set('height', str(92*scale))
    disk, arrow = list(root)[-2:]
    disk.set('cx', str(49+shift))
    points = [tuple(map(float, p.split(','))) for p in arrow.get('points').split()]
    arrow.set('points', ' '.join(f'{x+shift},{y}' for x, y in points))
    if reverse:
        stops = list(root)[0][0]
        a, b = list(stops)
        ca, cb = a.get('stop-color'), b.get('stop-color')
        a.set('stop-color', cb); b.set('stop-color', ca)
    image = render(ET.tostring(root, encoding='unicode'), int(104*scale), int(92*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg'], 'right') == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('description', [DESCRIPTION.replace('nach rechts', 'nach links'),
    DESCRIPTION.replace('nach rechts', 'nach oben'), DESCRIPTION+' Zusätzlich eine Linie.',
    DESCRIPTION+' Ohne Pfeil.', DESCRIPTION+' Ein Pfeil nach links.',
    DESCRIPTION.replace('Pfeil nach rechts', 'Pfeil')])
def test_conflicting_or_missing_direction_is_rejected(description):
    assert fit(render(INDEPENDENT, 104, 92), description) is None


@pytest.mark.parametrize('direction', ['links', 'rechts', 'oben', 'unten'])
def test_whole_motif_placement_does_not_override_arrow_direction(direction):
    result = fit(render(INDEPENDENT, 104, 92), DESCRIPTION+f' Das Motiv ist nach {direction} verschoben.')
    assert result is not None
    assert symbol_semantics(result['svg'], 'right') == 1


@pytest.mark.parametrize('mutation', ['missing', 'left', 'extra', 'gap', 'square'])
def test_incompatible_raster_evidence_is_rejected(mutation):
    root = ET.fromstring(INDEPENDENT)
    disk, arrow = list(root)[-2:]
    if mutation == 'missing':
        root.remove(arrow)
    elif mutation == 'left':
        arrow.set('points', '24,46 46,24 46,35 71,35 71,57 46,57 46,68')
    elif mutation == 'extra':
        ET.SubElement(root, 'rect', x='2', y='2', width='6', height='6', fill='#000000')
    elif mutation == 'gap':
        ET.SubElement(root, 'rect', x='40', y='33', width='5', height='27', fill='#90b69a')
    else:
        root.remove(disk)
        root.insert(len(root)-1, ET.Element('rect', x='12', y='9', width='74', height='74', fill='url(#color)'))
    assert fit(render(ET.tostring(root, encoding='unicode'), 104, 92)) is None


def test_runtime_uses_pixels_and_description_under_anonymous_names(monkeypatch):
    image = render(INDEPENDENT, 104, 92)
    def forbidden(*args, **kwargs):
        pytest.fail('Disk-arrow fitting must bypass reference vectors and embedding')
    monkeypatch.setattr(runtime, '_try_load_sample_svg', forbidden)
    outputs = []
    for name in ('anonymous_direction', 'different_name'):
        logs = []
        runtime.runNonCompositeIterationImpl(mode='non_composite', params={}, stripe_strategy=None,
            semantic_mode_visual_override=False, width=104, height=92, base_name=name,
            description=DESCRIPTION, perc_img=image, img_path=name+'.png', print_fn=lambda *args: None,
            render_embedded_raster_svg_fn=forbidden, build_gradient_stripe_svg_fn=forbidden,
            build_gradient_stripe_validation_log_lines_fn=forbidden, write_validation_log_fn=logs.append,
            render_svg_to_numpy_fn=render, record_render_failure_fn=forbidden,
            write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
            calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])
        assert logs == [['status=non_composite_raster_disk_arrow']]
    assert outputs[0] == outputs[1]


def test_catalog_arrow_override_does_not_relabel_bell_images():
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    for directory in ('descriptions', 'images_to_convert'):
        path = ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml'
        mapping = loadDescriptionMappingImpl(str(path), get_base_name_from_file_fn=getBaseNameFromFileImpl)
        assert mapping['GE0022'] == DESCRIPTION
        assert mapping['GE0022_L'] == MANIFEST['baseline_description']
        table = ET.parse(path)
        images = [e.text for e in table.iter('bild')]
        assert images.count('GE0022.jpg') == 1


def test_semantic_contract_requires_supported_direction():
    assert symbol_semantics(INDEPENDENT, 'right') == 1
    assert symbol_semantics(INDEPENDENT, 'left') == 0
    assert symbol_semantics(INDEPENDENT, 'unknown') == 0
