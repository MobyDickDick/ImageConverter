"""User-guided square/handle/joint redraw and image-specific descriptions."""
from pathlib import Path
from xml.etree import ElementTree as ET
import math
import re

import cv2
import pytest

from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
from tools.run_plan_b_variations import measure_quality

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT/'artifacts/images_to_convert/AC0501_S_sia.jpg'
VECTOR = ROOT/'artifacts/converted_images/converted_svgs/AC0501_S_sia.svg'


def test_redraw_preserves_square_diagonals_handle_circle_and_diagonal_order():
    root = ET.parse(VECTOR).getroot()
    assert (root.get('width'), root.get('height')) == ('20', '40')
    elements = {e.get('id'):e for e in root}
    assert len(elements) == 5
    square, cross, stem, blade, circle = (elements[k] for k in
        ('square', 'square_diagonals', 'stem', 'damper', 'joint'))
    assert square.tag.endswith('rect') and circle.tag.endswith('circle')
    x,y,s = map(float, (square.get('x'),square.get('y'),square.get('width')))
    cx,cy,r = map(float, (circle.get('cx'),circle.get('cy'),circle.get('r')))
    assert s == float(square.get('height')) and r > 0
    assert cross.get('stroke') == square.get('stroke')
    numbers = lambda e:list(map(float, re.findall(r'-?\d+(?:\.\d+)?', e.get('d'))))
    assert numbers(cross) == pytest.approx([x,y,x+s,y+s,x+s,y,x,y+s], abs=1e-4)
    assert numbers(stem) == pytest.approx([cx,y+s,cx,cy-r],abs=1e-4)
    assert math.isclose(cx,x+s/2,abs_tol=1e-4)
    a,b,c,d = numbers(blade)
    assert a < cx < c and b < cy < d
    assert math.isclose((cy-b)*(c-a),(cx-a)*(d-b),abs_tol=1e-3)
    assert list(root).index(blade) < list(root).index(circle)


def test_redraw_passes_original_pixel_gate():
    result = measure_quality(cv2.imread(str(IMAGE)), VECTOR.read_text())
    assert result['satisfactory'], result


@pytest.mark.parametrize('folder', ['descriptions','images_to_convert'])
def test_only_sia_variant_descriptions_replace_the_conflicting_family_text(folder):
    descriptions = loadDescriptionMappingImpl(str(ROOT/'artifacts'/folder/'Finale_Wurzelformen_V3.xml'),
                                             get_base_name_from_file_fn=getBaseNameFromFileImpl)
    for variant in ('AC0501_S_sia','AC0501_M_sia','AC0501_L_sia','AC0501_1S_sia','AC0501_2S_sia'):
        assert 'quadratischem Kopf' in descriptions[variant]
        assert 'links oben nach rechts unten' in descriptions[variant]
        assert 'Rechteck hochkant' not in descriptions[variant]
    assert 'Rechteck hochkant' in descriptions['AC0501_S']
    assert 'Rechteck hochkant' in descriptions['AC0501']


def test_image_description_override_does_not_leak_to_other_images(tmp_path):
    source = tmp_path/'descriptions.xml'
    source.write_text('''<root><entry key="family"><beschreibung>Alte Gruppe.</beschreibung><bilder>
      <bild beschreibung="Ergaenzung.">first.jpg</bild>
      <bild beschreibung_modus="ersetzen" beschreibung="Neue eigenstaendige Form.">second.jpg</bild>
      </bilder></entry></root>''')
    descriptions = loadDescriptionMappingImpl(str(source), get_base_name_from_file_fn=getBaseNameFromFileImpl)
    assert descriptions['first'] == 'Alte Gruppe. Ergaenzung.'
    assert descriptions['second'] == 'Neue eigenstaendige Form.'
    assert descriptions['family'] == 'Alte Gruppe.'
