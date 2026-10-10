"""Labeled-square acceptance with independent geometry and unchanged quality gates."""
from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules.imageCompositeConverterLabeledSquare import fit_labeled_square
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_labeled_square_recheck import evaluate, labeled_square_semantics
from tools.run_plan_b_variations import make_variations, measure_quality

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'artifacts/evaluation/labeled_t_square_recheck_v1'
MANIFEST = json.loads((PACKAGE / 'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION):
    h, w = image.shape[:2]
    result = fit_labeled_square(geometry.buildGeometryIrFromDescriptionImpl(description), image=image,
        render_fn=lambda ir: render(geometry.renderGeometryIrToSvgImpl(w, h, ir), w, h),
        error_fn=lambda raster: calculateErrorImpl(image, raster, cv2_module=cv2, np_module=np))
    return None if result is None else geometry.renderGeometryIrToSvgImpl(w, h, result['geometry_ir'])


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_real_rasters_reproduce_accepted_vector_and_explicit_label(case):
    image = cv2.imread(str(PACKAGE / case['image']))
    svg = fit(image)
    assert labeled_square_semantics(svg, 'T') == 1
    assert svg.replace('\r\n', '\n') == (PACKAGE / case['after_svg']).read_text(encoding='utf-8')


def synthetic(phase=0, scale=1, fill='#327aad', text='#f4eddf', label='T', stem_offset=0):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{56*scale}" height="{80*scale}" viewBox="0 0 56 80">'
           f'<path d="M {25+phase+stem_offset} 42 L {25+phase+stem_offset} 75" stroke="#777777" stroke-width="1.5"/>'
           f'<rect x="{9+phase}" y="10" width="32" height="32" fill="{fill}" stroke="#959595" stroke-width="1.5"/>'
           f'<text x="{25+phase}" y="35" font-size="22" font-weight="700" font-family="Arial, Helvetica, sans-serif" text-anchor="middle" fill="{text}">{label}</text></svg>')
    return svg, render(svg, 56*scale, 80*scale)


@pytest.mark.parametrize('phase, scale, fill, text', [
    (0, 1, '#327aad', '#f4eddf'), (.25, 1, '#28743a', '#eeedd8'),
    (.5, 2, '#973971', '#f8efed'), (.75, 2, '#f2f2f2', '#444444'),
])
def test_independent_geometry_color_polarity_resolution_and_pixel_phase(phase, scale, fill, text):
    _, image = synthetic(phase, scale, fill, text)
    svg = fit(image)
    assert svg is not None
    assert labeled_square_semantics(svg, 'T') == 1
    assert measure_quality(image, svg)['satisfactory']


def test_fractional_rescale_and_translation_preserve_contour_evidence():
    source, _ = synthetic()
    variation = make_variations(source, DESCRIPTION, 20261010)[8]
    image = render(variation['svg'], variation['width'], variation['height'])
    assert measure_quality(image, fit(image))['satisfactory']


P_PACKAGE = ROOT / 'artifacts/evaluation/labeled_square_recheck_v1'
P_MANIFEST = json.loads((P_PACKAGE / 'manifest.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', P_MANIFEST['cases'], ids=lambda c: Path(c['image']).stem)
def test_previously_accepted_labels_keep_their_exact_vector(case):
    image = cv2.imread(str(P_PACKAGE / case['image']))
    assert fit(image, P_MANIFEST['description']) == (P_PACKAGE / case['after_svg']).read_text(encoding='utf-8')


@pytest.mark.parametrize('label, offset', [('', 0), ('T', 12)])
def test_missing_label_or_disconnected_stem_is_rejected(label, offset):
    _, image = synthetic(label=label, stem_offset=offset)
    assert fit(image) is None


def test_semantic_gate_rejects_wrong_label_extra_shapes_and_wrong_stem_direction():
    svg, _ = synthetic()
    assert labeled_square_semantics(svg, 'T') == 1
    assert labeled_square_semantics(svg.replace('>T</text>', '>P</text>'), 'T') == 0
    assert labeled_square_semantics(svg.replace('</svg>', '<circle cx="48" cy="10" r="3"/></svg>'), 'T') == 0
    assert labeled_square_semantics(svg.replace('L 25 75', 'L 25 35'), 'T') == 0


def test_both_catalogs_use_the_same_self_contained_description():
    for folder in ('images_to_convert', 'descriptions'):
        root = ET.parse(ROOT / 'artifacts' / folder / 'Finale_Wurzelformen_V3.xml')
        entry = next(e for e in root.findall('.//entry') if e.get('key') == 'AC0721')
        assert entry.findtext('beschreibung') == DESCRIPTION
        assert 'AC0701' not in DESCRIPTION and '"T"' in DESCRIPTION


def test_saved_cli_pairs_pass_both_gates_without_metric_regression():
    report = evaluate(MANIFEST, PACKAGE)
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])


def test_description_runner_rejects_stale_output(tmp_path, monkeypatch):
    import sys
    from tools.run_labeled_description_recheck import main
    monkeypatch.setattr(sys, 'argv', ['recheck', str(PACKAGE / 'manifest.json'), '--output-dir', str(tmp_path)])
    with pytest.raises(ValueError, match='fresh output directory'):
        main()


def test_description_runner_rejects_changed_source(tmp_path, monkeypatch):
    import sys
    from tools.run_labeled_description_recheck import main
    source = tmp_path / 'input.jpg'
    source.write_bytes(b'changed input')
    manifest = {'cases': [{'case_id': 'neutral', 'image': 'input.jpg', 'source_sha256': 'old hash'}]}
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    monkeypatch.setattr(sys, 'argv', ['recheck', str(path), '--output-dir', str(tmp_path / 'fresh')])
    with pytest.raises(ValueError, match='Source hash mismatch'):
        main()
