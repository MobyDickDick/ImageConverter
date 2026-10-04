import cv2
import fitz
import numpy as np

from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_nested_panel_recheck import measure, nested_rectangle_semantics
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


PERFECT = ('<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40">'
           '<rect width="80" height="40" fill="#345599"/>'
           '<rect x="4" y="4" width="56" height="32" fill="#ffffff"/></svg>')


def test_nested_panel_metrics_calibrate_perfect_saved_svg_and_reject_missing_region(tmp_path):
    image = tmp_path / 'input.png'
    raster = render_svg_to_numpy_inprocess(PERFECT, 80, 40, fitz_module=fitz, np_module=np, cv2_module=cv2)
    assert cv2.imwrite(str(image), raster)
    perfect_svg, wrong_svg = tmp_path / 'perfect.svg', tmp_path / 'wrong.svg'
    perfect_svg.write_text(PERFECT, encoding='utf-8')
    wrong_svg.write_text('<svg width="80" height="40"><rect width="80" height="40" fill="#ffffff"/></svg>', encoding='utf-8')
    ideal, wrong = measure(image, perfect_svg), measure(image, wrong_svg)
    assert ideal['metrics'] == {'error_per_pixel': 0., 'edge_alignment': 1., 'object_mask_iou': 1.,
                                'semantic_score': 1., 'dimension_match': 1.}
    assert wrong['metrics']['semantic_score'] == 0.
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {'commit': 'test', 'seed': 0, 'toolchain': 'test', 'input_hashes': {}},
        'cases': {'panel': {'metrics': wrong['metrics'], 'dimensions': wrong['dimensions']}}})
    assert evaluate_satisfaction(baseline, {'panel': ideal})['cases'][0]['satisfactory']
    assert not evaluate_satisfaction(baseline, {'panel': wrong})['cases'][0]['satisfactory']


def test_nested_panel_semantics_rejects_wrong_containment_and_embedded_raster():
    assert nested_rectangle_semantics(PERFECT.replace('x="4"', 'x="40"')) == 0.
    assert nested_rectangle_semantics(PERFECT.replace('</svg>', '<image href="data:image/png;base64,AA=="/></svg>')) == 0.
    assert nested_rectangle_semantics(PERFECT.replace('<rect x=', '<rect transform="translate(5 0)" x=')) == 0.
