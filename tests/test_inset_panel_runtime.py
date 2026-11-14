from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterInsetPanel import fit_inset_panel, inset_panel_contract, inset_details
from tools.run_plan_b_variations import render, measure_quality

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Im Hintergrund liegt ein waagerechtes Rechteck mit abgerundeten Ecken und einem '
    'vertikalen Graustufenverlauf: oben leicht heller, unten etwas dunkler. '
    'Davor liegt ein etwas kleineres weisses Rechteck, dessen linke Ecken abgerundet sind. '
    'Das weisse Vordergrundrechteck ist rechts bei ungefähr 90 Prozent der Breite des '
    'Hintergrundrechtecks senkrecht abgeschnitten. Dadurch bleiben oben, unten und links '
    'schmale graue Ränder sowie rechts ein breiterer grauer Bereich sichtbar. '
    'Keine Beschriftung oder weiteren Zeichen.')


def independent_raster(width, height, margin=0, cut=.88):
    # Supersampled OpenCV ellipses/boxes form the source, independently of SVG
    # paths, SVG renderers and the fitter's geometry generation.
    scale = 8
    shape = (height*scale, width*scale)
    x, y, X, Y = margin, margin, width-margin, height-margin
    rx, ry = 4, 4
    a, b, A, B = x+2, y+2, x+(X-x)*cut, Y-2
    def rounded(bounds, radius):
        l, t, r, d = [int(v*scale) for v in bounds]
        u, v = [int(z*scale) for z in radius]
        mask = np.zeros(shape, np.uint8)
        cv2.rectangle(mask, (l+u, t), (r-u-1, d-1), 255, -1)
        cv2.rectangle(mask, (l, t+v), (r-1, d-v-1), 255, -1)
        for cx, cy in ((l+u,t+v), (r-u-1,t+v), (l+u,d-v-1), (r-u-1,d-v-1)):
            cv2.ellipse(mask, (cx,cy), (u,v), 0, 0, 360, 255, -1)
        return mask.astype(float)/255
    outer = rounded((x,y,X,Y), (rx,ry))
    inner = rounded((a,b,X-2,B), (3,2))
    inner[:, int(A*scale):] = 0
    t = np.clip((np.arange(shape[0])+.5-y*scale)/((Y-y)*scale),0,1)
    grey = 230-20*t[:,None]
    pixels = 255*(1-outer)+grey*outer
    pixels = pixels*(1-inner)+255*inner
    pixels = pixels.reshape(height,scale,width,scale).mean(axis=(1,3))
    return np.repeat(np.rint(pixels).astype(np.uint8)[:,:,None],3,axis=2)


def fit(image, description=DESCRIPTION, render_fn=render):
    h,w = image.shape[:2]
    return fit_inset_panel(w,h,description=description,image=image,render_fn=render_fn,
        error_fn=lambda a,b:float(np.mean((a.astype(float)-b)**2)))


@pytest.mark.parametrize('size,margin,cut', [((180,25),0,.87), ((240,32),3,.89), ((150,30),2,.84)])
def test_independent_pixels_keep_rounding_gradient_and_square_cut(size,margin,cut):
    image = independent_raster(*size,margin,cut)
    result = fit(image)
    assert result is not None
    assert result['details']['passed']
    assert measure_quality(image,result['svg'])['satisfactory']
    root = ET.fromstring(result['svg'])
    assert len(root.findall('{*}rect')) == 1
    assert len(root.findall('{*}path')) == 1
    assert len(root.findall('.//{*}stop')) == 2
    assert 'image' not in result['svg']


def test_original_jpeg_and_both_description_sources():
    for folder in ('descriptions','images_to_convert'):
        xml = ET.parse(ROOT/f'artifacts/{folder}/Finale_Wurzelformen_V3.xml')
        description = next(e.findtext('beschreibung') for e in xml.iter('entry') if e.get('key')=='DLG0016')
        assert description == DESCRIPTION
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/DLG0016.JPG'))
    result = fit(image)
    assert result is not None
    assert result['details']['passed']
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('extra', [' Ein roter Pfeil liegt davor.', ' Keine Rundungen.', ' Ein Kreis ist sichtbar.'])
def test_unknown_and_contradictory_assertions_cannot_disappear(extra):
    assert not inset_panel_contract(DESCRIPTION+extra)
    assert fit(independent_raster(180,25), DESCRIPTION+extra) is None


@pytest.mark.parametrize('damage', ['mark','reverse','missing_inset','colour'])
def test_wrong_pixels_are_rejected(damage):
    image = independent_raster(180,25)
    if damage == 'mark':
        image[10:14,70:74] = 0
    elif damage == 'reverse':
        image = image[::-1].copy()
    elif damage == 'missing_inset':
        image[:,2:156] = image[:,165:166]
    else:
        image[:,:,0] = 100
    assert fit(image) is None


def test_missing_corners_and_gradient_fail_local_checks():
    image = independent_raster(180,25)
    result = fit(image)
    assert result is not None
    square = result['rendered'].copy()
    square[:4,:4] = 230
    square[-4:,:4] = 210
    assert not inset_details(image,square,result['parameters'])['passed']
    flat = result['rendered'].copy()
    flat[:,160:175] = 220
    assert not inset_details(image,flat,result['parameters'])['passed']


def test_expired_budget_does_not_render():
    session = ImageSearch(SearchPolicy(),clock=lambda:0)
    session.spent = 121
    def unexpected(*args):
        pytest.fail('expired search must not render')
    with image_search(session):
        assert fit(independent_raster(180,25),render_fn=unexpected) is None
