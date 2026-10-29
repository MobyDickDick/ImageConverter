"""Independent label models must preserve text, geometry and reject false matches."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterShortLabelDisk import fit_short_label_disk
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration
from tools.run_plan_b_variations import render, measure_quality

DESCRIPTION = 'Eine einfarbige Kreisscheibe mit dunkler Randkontur. Die dunkle serifenlose Beschriftung "rF" steht mittig. Keine Anschlüsse.'


def synthetic(label='rF', size=64, weight=400):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
            f'<rect width="{size}" height="{size}" fill="#ffffff"/>'
            f'<circle cx="{size/2}" cy="{size/2}" r="{size*.4}" fill="#d7e8db" stroke="#445a51" stroke-width="{size*.035}"/>'
            f'<text x="{size/2}" y="{size*.65}" font-family="Arial" font-weight="{weight}" font-size="{size*.4}" text-anchor="middle" fill="#283b33">{label}</text></svg>')


def fit(image, description=DESCRIPTION):
    h,w = image.shape[:2]
    return fit_short_label_disk(w,h,description=description,image=image,render_fn=render,
                               error_fn=lambda a,b:float(np.mean((a.astype(float)-b.astype(float))**2)))


@pytest.mark.parametrize('label,size,weight',[('rF',48,400),('AB',64,700),('pH',96,400),('42',80,700)])
def test_unseen_labels_colors_and_sizes(label,size,weight):
    image = render(synthetic(label,size,weight),size,size)
    with search_configuration(mode='portfolio',seed=13,budget=96):
        result = fit(image,DESCRIPTION.replace('rF',label))
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']
    texts = [e.text for e in ET.fromstring(result['svg']).iter() if e.tag.endswith('text')]
    assert ''.join(texts) == label
    assert len(result['model_attempts']) == 4


@pytest.mark.parametrize('description',[DESCRIPTION.replace('rF','XX'),DESCRIPTION+' Zusätzlich ein Punkt.',
                                      DESCRIPTION.replace('Kreisscheibe','Quadrat'),DESCRIPTION.replace('rF','rf')])
def test_wrong_label_or_extra_content_cannot_claim_success(description):
    assert fit(render(synthetic(),64,64),description) is None


@pytest.mark.parametrize('size',['S','M','L'])
def test_catalog_disk_has_validated_saved_variants(size,tmp_path):
    image = cv2.imread(str(Path(__file__).resolve().parents[1]/f'artifacts/images_to_convert/AC0840_{size}.jpg'))
    with search_configuration(mode='portfolio',seed=20261017,directory=tmp_path):
        result = fit(image)
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']
    assert list((tmp_path/'validated').rglob('*.svg'))


@pytest.mark.parametrize('size', ['L', 'M', 'S'])
def test_three_character_catalog_label_preserves_case_and_strict_pixels(size):
    image = cv2.imread(str(Path(__file__).resolve().parents[1]/f'artifacts/images_to_convert/AC0910_{size}.jpg'))
    with search_configuration(mode='portfolio',seed=20261017):
        result = fit(image, DESCRIPTION.replace('rF', 'Lux'))
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']
    assert ''.join(e.text for e in ET.fromstring(result['svg']).iter() if e.tag.endswith('text')) == 'Lux'
    if size == 'L':
        assert any(attempt['model'].startswith('glyph_offsets_') and attempt['accepted']
                   for attempt in result['model_attempts'])


@pytest.mark.parametrize('label', ['LUX', 'Luz', 'XXX'])
def test_glyph_refinement_rejects_wrong_three_character_label(label):
    image = cv2.imread(str(Path(__file__).resolve().parents[1]/'artifacts/images_to_convert/AC0910_L.jpg'))
    with search_configuration(mode='portfolio',seed=20261017):
        assert fit(image, DESCRIPTION.replace('rF', label)) is None


@pytest.mark.parametrize('size', ['L', 'M', 'S'])
def test_plain_circle_description_uses_raster_colors_and_font(size):
    # No magic words such as "einfarbig", "Kreisscheibe" or "serifenlos".
    description = ('Grauer Kreis mit grauem Rand und hellgrauem Hintergrund. '
                   'Text im Kreis: "VOC". Kein Griff, keine Kelle und keine weiteren Anbauteile.')
    image = cv2.imread(str(Path(__file__).resolve().parents[1]/f'artifacts/images_to_convert/AC0835_{size}.jpg'))
    with search_configuration(mode='portfolio', seed=42):
        result = fit(image, description)
    assert result is not None
    assert measure_quality(image, result['svg'])['satisfactory']
    assert ''.join(e.text for e in ET.fromstring(result['svg']).iter() if e.tag.endswith('text')) == 'VOC'


def test_condensed_unseen_label_fits_width_separately_from_height():
    source = synthetic('NO', 80, 700).replace('<text ', '<text transform="translate(40 0) scale(.75 1) translate(-40 0)" ')
    image = render(source, 80, 80)
    with search_configuration(mode='portfolio', seed=42):
        result = fit(image, DESCRIPTION.replace('rF', 'NO'))
    assert result is not None
    assert measure_quality(image, result['svg'])['satisfactory']
