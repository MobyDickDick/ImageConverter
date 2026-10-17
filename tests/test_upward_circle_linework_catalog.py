"""Keep the catalog's upward chord/T family on its measured geometry path."""
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import pytest

from src.iCCModules.imageCompositeConverterCircleLinework import fit_circle_linework
from tools.evaluate_oriented_circle_linework_recheck import symbol_semantics
from tools.review_conversion_quality import normalized_mse
from tools.run_plan_b_variations import measure_quality, render


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'artifacts/evaluation/upward_circle_linework_recheck_v1'
MANIFEST = json.loads((FOLDER / 'manifest.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda case: case['source'])
def test_catalog_description_reconstructs_upward_chords_and_interior_t(case):
    descriptions = []
    for directory in ('images_to_convert', 'descriptions'):
        tree = ET.parse(ROOT / 'artifacts' / directory / 'Finale_Wurzelformen_V3.xml')
        entries = [entry for entry in tree.findall('.//entry')
                   if case['source'] in [image.text for image in entry.findall('.//bild')]]
        assert len(entries) == 1
        descriptions.append(entries[0].findtext('beschreibung'))
    assert descriptions == [case['description']] * 2
    assert 'unzugeordnet' not in descriptions[0].casefold()
    path = FOLDER / case['image']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == case['source_sha256']
    image = cv2.imread(str(path))
    height, width = image.shape[:2]
    result = fit_circle_linework(width, height, description=descriptions[0], image=image,
                                render_fn=render, error_fn=lambda a, b: normalized_mse(a, b)[0])
    assert result is not None
    assert symbol_semantics(result['svg'], 'up') == 1
    assert symbol_semantics(result['svg'], 'down') == 0
    quality = measure_quality(image, result['svg'])
    if case['source'].startswith('AC0411_1_') or case['source'].startswith('AC0411_2_'):
        assert quality['satisfactory']
    else:
        # Light JPEG fills cross the fixed foreground threshold. Keep this
        # stricter follow-up visible rather than relaxing a quality limit.
        assert quality['failures'] == ['foreground_iou_outside_limit']
