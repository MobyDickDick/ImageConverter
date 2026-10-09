"""Downward circle/triangle catalog descriptions and anonymous observations."""
import json
from pathlib import Path

import cv2
import pytest

from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
from test_pump_runtime import convert
from tools.evaluate_pump_recheck import circle_triangle_semantics
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / 'artifacts/evaluation/down_pump_recheck_v1/manifest.json'
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda case: case['source'])
def test_downward_triangle_variants_reconstruct_from_anonymous_raster(case, monkeypatch):
    image = cv2.imread(str((MANIFEST_PATH.parent / case['image']).resolve()))
    assert image is not None
    svg, raster = convert(image, 'independent_observation', monkeypatch, MANIFEST['description'])
    assert circle_triangle_semantics(svg, 'unten') == 1
    assert circle_triangle_semantics(svg, 'oben') == 0
    assert normalized_mse(image, raster)[1] < .003


@pytest.mark.parametrize('catalog', ['images_to_convert', 'descriptions'])
def test_catalog_describes_absolute_downward_topology_without_reference(catalog):
    mapping = loadDescriptionMappingImpl(
        str(ROOT / f'artifacts/{catalog}/Finale_Wurzelformen_V3.xml'),
        get_base_name_from_file_fn=getBaseNameFromFileImpl,
    )
    assert 'nach unten' in MANIFEST['description']
    assert 'Wie AC' not in MANIFEST['description']
    assert 'gedreht' not in MANIFEST['description']
    for case in MANIFEST['cases']:
        assert mapping[Path(case['source']).stem] == MANIFEST['description']
