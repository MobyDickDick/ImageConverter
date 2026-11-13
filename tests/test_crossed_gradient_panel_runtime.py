from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import pytest

from src.iCCModules.imageCompositeConverterCrossedGradientPanel import fit_crossed_gradient_panel
from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
from tools.review_conversion_quality import normalized_mse
from tools.run_plan_b_variations import measure_quality, render

ROOT = Path(__file__).resolve().parents[1]
NS = {'s':'http://www.w3.org/2000/svg'}
DESCRIPTION = ('Graues Rechteck hochkant mit grauem Rand, Kreuz aus den beiden Diagonalen, '
    'an den Ecken abgeschnitten. Oben in der Mitte ein Minuszeichen. Horizontaler Farbverlauf '
    'dunkel-hell-dunkel. Das Helligkeitsmaximum liegt leicht links der Mittellinie. '
    'Der Hintergrund ist immer heller als der Rand.')


def drawing(width=40,height=80,peak=.4,*,minus=True,second=True,gap=False,flat=False):
    shade = '#c8c8c8' if flat else '#fafafa'
    first = ('M 1.5 1 L 15.8 31 M 24.2 49 L 38.5 79' if gap else 'M 1.5 1 L 38.5 79')
    return (f'<svg xmlns="{NS["s"]}" width="{width}" height="{height}" viewBox="0 0 40 80">'
        f'<defs><linearGradient id="paint"><stop offset="0" stop-color="#c8c8c8"/>'
        f'<stop offset="{peak}" stop-color="{shade}"/><stop offset="1" stop-color="#c8c8c8"/>'
        '</linearGradient><clipPath id="clip"><rect x="1.5" y="1" width="37" height="78"/></clipPath></defs>'
        '<rect width="40" height="80" fill="white"/>'
        '<rect x="1.5" y="1" width="37" height="78" fill="url(#paint)"/>'
        f'<g clip-path="url(#clip)"><path d="{first}" stroke="#858585" stroke-width="3"/>'
        + ('<path d="M 38.5 1 L 1.5 79" stroke="#858585" stroke-width="3"/>' if second else '')
        + ('<rect x="15" y="7.5" width="10" height="2.5" fill="#666666"/>' if minus else '')
        + '</g><rect x="1.5" y="1" width="37" height="78" fill="none" stroke="#999999" stroke-width="1.4"/></svg>')


def fit(image,description=DESCRIPTION,**kwargs):
    height,width = image.shape[:2]
    return fit_crossed_gradient_panel(width,height,description=description,image=image,
        render_fn=kwargs.get('render_fn',render),
        error_fn=kwargs.get('error_fn',lambda a,b: normalized_mse(a,b)[0]))


def assert_structure(svg):
    root = ET.fromstring(svg)
    group = root.find('s:g',NS)
    clip = root.find('s:defs/s:clipPath',NS)
    assert group.get('clip-path') == f'url(#{clip.get("id")})'
    lines = group.findall('s:line',NS)
    assert len(lines) == 2
    assert float(lines[0].get('x1')) < float(lines[0].get('x2'))
    assert float(lines[1].get('x1')) > float(lines[1].get('x2'))
    minus = group.find('s:rect',NS)
    assert float(minus.get('width')) > 2.5*float(minus.get('height'))
    gradient = root.find('s:defs/s:linearGradient',NS)
    stops = gradient.findall('s:stop',NS)
    assert gradient.get('y1') == gradient.get('y2') and len(stops) == 3
    assert .2 < float(stops[1].get('offset')) < .5
    shade = lambda color: int(color[1:3],16)
    rim = shade(root.findall('s:rect',NS)[-1].get('stroke'))
    paints = [shade(stop.get('stop-color')) for stop in stops]
    assert paints[1] > max(paints[0],paints[2]) and min(paints) > rim
    assert not root.findall('.//s:image',NS)


@pytest.mark.parametrize('width,height,peak',[(30,60,.39),(40,80,.43),(60,120,.46)])
def test_independent_sizes_and_highlights_keep_complete_diagonals_and_minus(width,height,peak):
    image = render(drawing(width,height,peak),width,height)
    result = fit(image)
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']
    assert_structure(result['svg'])


@pytest.mark.parametrize('size',['L','M','S'])
def test_real_jpeg_variants_keep_their_own_description_and_observed_geometry(size):
    mapping = loadDescriptionMappingImpl(str(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'),
        get_base_name_from_file_fn=getBaseNameFromFileImpl)
    assert 'drei graue horizontale Linien' in mapping['AC0110.jpg']
    name = f'AC0110_{size}.jpg'
    assert 'Minuszeichen' in mapping[name] and 'Diagonalen' in mapping[name]
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/name))
    result = fit(image,mapping[name])
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']
    assert_structure(result['svg'])


@pytest.mark.parametrize('kwargs',[dict(minus=False),dict(second=False),dict(gap=True),dict(flat=True),dict(peak=.65)])
def test_missing_arms_minus_gradient_or_incorrect_highlight_are_rejected(kwargs):
    assert fit(render(drawing(**kwargs),40,80)) is None


@pytest.mark.parametrize('description',[DESCRIPTION.replace('Horizontaler','Vertikaler'),
    DESCRIPTION.replace('Minuszeichen','Pluszeichen'),DESCRIPTION+' ohne Kreuz',DESCRIPTION+' Kreis'])
def test_conflicting_descriptions_are_rejected(description):
    assert fit(render(drawing(),40,80),description) is None


def test_failed_renderer_or_nonfinite_error_is_not_accepted():
    image = render(drawing(),40,80)
    assert fit(image,render_fn=lambda *args:None) is None
    assert fit(image,error_fn=lambda *args:float('nan')) is None


def test_original_gui_description_selects_the_same_model_without_rewriting_user_text():
    description = (ROOT/'tests/fixtures/descriptions/crossed_gradient_panel_user.txt').read_text(encoding='utf-8').strip()
    original = description
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0110_L.jpg'))
    result = fit(image,description)
    assert result is not None
    assert description == original and 'Minnus-Zeichen' in description and 'horizonalen' in description
    assert measure_quality(image,result['svg'])['satisfactory']
    assert_structure(result['svg'])
