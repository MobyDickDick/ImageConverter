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
EVIDENCE = ROOT/'artifacts/evaluation/disk_arrow_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_disk_arrow(width, height, description=description, image=image,
                          render_fn=kwargs.get('render_fn', render),
                          error_fn=kwargs.get('error_fn', lambda a, b: normalized_mse(a, b)[0]))


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_catalog_and_independent_rasters_pass_unchanged_gates(case):
    image = cv2.imread(str(EVIDENCE/case['image']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    assert result['evaluations'] <= 1+16*len(result['parameters'])
    assert '<image' not in result['svg']
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale,shift,color', [(1, 0, '#164f48'), (1, -6, '#594123'), (2, 3, '#254757')])
def test_independent_position_resolution_and_color(scale, shift, color):
    root = ET.fromstring(INDEPENDENT)
    root.set('width', str(96*scale)); root.set('height', str(84*scale))
    disk, arrow = list(root)[-2:]
    disk.set('cx', str(51+shift))
    points = [tuple(map(float, p.split(','))) for p in arrow.get('points').split()]
    arrow.set('points', ' '.join(f'{x+shift},{y}' for x, y in points))
    arrow.set('fill', color)
    image = render(ET.tostring(root, encoding='unicode'), 96*scale, 84*scale)
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('mutation', ['missing', 'right', 'detached', 'internal_mark', 'gap', 'disk_shape'])
def test_incompatible_evidence_is_rejected(mutation):
    root = ET.fromstring(INDEPENDENT)
    disk, arrow = list(root)[-2:]
    if mutation == 'missing':
        root.remove(arrow)
    elif mutation == 'right':
        arrow.set('points', '73,40 54,21 54,30 32,30 32,50 54,50 54,59')
    elif mutation == 'detached':
        ET.SubElement(root, 'rect', x='2', y='2', width='6', height='6', fill='#000000')
    elif mutation == 'internal_mark':
        ET.SubElement(root, 'rect', x='48', y='13', width='6', height='5', fill='#000000')
    elif mutation == 'gap':
        ET.SubElement(root, 'rect', x='49', y='29', width='3', height='22', fill='#a0c5bd')
    else:
        root.remove(disk)
        ET.SubElement(root, 'rect', x='17', y='6', width='68', height='68', fill='url(#color)')
        root.remove(arrow); root.append(arrow)
    assert fit(render(ET.tostring(root, encoding='unicode'), 96, 84)) is None


@pytest.mark.parametrize('description', ['Ein Kreis.', DESCRIPTION+' Zusätzlich eine Linie.',
                                       DESCRIPTION+' ohne Pfeil.', DESCRIPTION.replace('nach links', 'nach rechts')])
def test_description_conflicts_do_not_register(description):
    assert fit(render(INDEPENDENT, 96, 84), description) is None


@pytest.mark.parametrize('direction', ['links', 'rechts', 'oben', 'unten'])
def test_whole_motif_placement_keeps_arrow_direction(direction):
    result = fit(render(INDEPENDENT, 96, 84), DESCRIPTION+f' Das Motiv ist nach {direction} verschoben.')
    assert result is not None
    assert symbol_semantics(result['svg']) == 1


@pytest.mark.parametrize('failure', ['render', 'nan', 'infinity', 'dimensions'])
def test_invalid_measurements_are_rejected(failure):
    image = render(INDEPENDENT, 96, 84)
    if failure == 'dimensions':
        image = image[:, :, :2]
        kwargs = {}
    elif failure == 'render':
        kwargs = {'render_fn': lambda *args: None}
    else:
        kwargs = {'error_fn': lambda *args: float('nan' if failure == 'nan' else 'inf')}
    assert fit(image, **kwargs) is None


def test_runtime_rename_invariance_and_reference_precedence(monkeypatch):
    image = render(INDEPENDENT, 96, 84)
    def forbidden(*args, **kwargs):
        pytest.fail('Disk-arrow registration must bypass reference SVGs and embedding')
    monkeypatch.setattr(runtime, '_try_load_sample_svg', forbidden)
    outputs = []
    for name in ('anonymous_input', 'renamed_input'):
        logs = []
        runtime.runNonCompositeIterationImpl(mode='non_composite', params={}, stripe_strategy=None,
            semantic_mode_visual_override=False, width=96, height=84, base_name=name,
            description=DESCRIPTION, perc_img=image, img_path=name+'.png', print_fn=lambda *args: None,
            render_embedded_raster_svg_fn=forbidden, build_gradient_stripe_svg_fn=forbidden,
            build_gradient_stripe_validation_log_lines_fn=forbidden, write_validation_log_fn=logs.append,
            render_svg_to_numpy_fn=render, record_render_failure_fn=forbidden,
            write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
            calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])
        assert logs == [['status=non_composite_raster_disk_arrow']]
    assert outputs[0] == outputs[1]


def test_semantic_check_rejects_direction_and_missing_elements():
    assert symbol_semantics(INDEPENDENT) == 1
    assert symbol_semantics(INDEPENDENT.replace('29,40', '75,40')) == 0
    root = ET.fromstring(INDEPENDENT)
    root.remove(list(root)[-1])
    assert symbol_semantics(ET.tostring(root, encoding='unicode')) == 0


def test_both_catalogs_describe_observed_topology():
    for directory in ('descriptions', 'images_to_convert'):
        table = ET.parse(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml')
        entry = next(e for e in table.iter('entry') if e.get('key') == 'GE0039')
        assert entry.findtext('beschreibung') == DESCRIPTION
