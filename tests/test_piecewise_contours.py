from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterPiecewiseContours import fit_paint_boundary
from src.iCCModules.imageCompositeConverterPiecewiseScene import (
    align_piecewise_companions, fit_piecewise_scene, load_piecewise_companions, piecewise_contract,
    piecewise_details,
    validate_piecewise_refinement,
)
from tools.run_plan_b_variations import measure_quality, render

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Im Hintergrund liegt ein Kreis mit grauem Rand und einem blaugrauen Farbverlauf. '
    'Davor liegt eine farbige Hand mit dunkler Kontur. '
    'Daumen und Zeigefinger bilden eine fast geschlossene Schlaufe. '
    'Keine Beschriftung oder weiteren Zeichen.')


def synthetic(size=90, angle=1.2, shift=0):
    # Independent supersampled OpenCV shape with a hole and narrow branches.
    # It is an organic test silhouette, not a hand template supplied to fitting.
    scale = 6
    n = size*scale
    yy, xx = np.indices((n,n), dtype=float)
    x, y = (xx+.5)/n, (yy+.5)/n
    r = np.hypot(x-.5,y-.5)
    pixels = np.full((n,n,3),255., dtype=float)
    t = (x-.5)*np.cos(angle)+(y-.5)*np.sin(angle)+.5
    bg = np.stack((233-35*t,219-57*t,191-78*t),axis=2)
    pixels[r < .475] = [225,225,225]
    pixels[r < .45] = bg[r < .45]
    mask = np.zeros((n,n), np.uint8)
    def pt(x,y):
        return round((x+shift)*n), round(y*n)
    cv2.ellipse(mask,pt(.49,.57),(round(.23*n),round(.15*n)),-20,0,360,255,-1)
    cv2.line(mask,pt(.38,.54),pt(.50,.23),255,round(.065*n))
    cv2.line(mask,pt(.46,.49),pt(.64,.28),255,round(.065*n))
    cv2.ellipse(mask,pt(.60,.57),(round(.075*n),round(.04*n)),0,0,360,0,-1)
    inside = cv2.erode(mask,np.ones((max(3,round(.025*n)),)*2,np.uint8))
    pixels[mask > 0] = [130,151,175]
    pixels[inside > 0] = [188,214,240]
    return np.rint(pixels.reshape(size,scale,size,scale,3).mean(axis=(1,3))).astype('uint8')


def fit(image, **kwargs):
    h,w = image.shape[:2]
    return fit_piecewise_scene(w,h,description=kwargs.pop('description',DESCRIPTION),image=image,
        render_fn=kwargs.pop('render_fn',render),
        error_fn=lambda a,b:float(np.mean((a.astype(float)-b)**2)), **kwargs)


def test_shared_joins_are_exact_smooth_and_close_with_holes():
    yy,xx = np.indices((90,90))
    alpha = ((np.hypot(xx-45,yy-45)<30) & (np.hypot(xx-45,yy-45)>11)).astype(float)
    result = fit_paint_boundary(alpha,tolerance=.3)
    assert result is not None and result.holes == 1
    assert result.segments < 120 and result.max_error <= .3
    for loop in result.curves:
        for a,b in zip(loop,loop[1:]+loop[:1]):
            np.testing.assert_array_equal(a[3],b[0])
            u,v = a[3]-a[2], b[1]-b[0]
            assert u@v > 0
            assert abs(u[0]*v[1]-u[1]*v[0]) < 1e-9
    assert result.path().count('M ') == 2 and result.path().count('Z') == 2
    assert fit_paint_boundary(alpha,max_segments=4) is None
    assert fit_paint_boundary(alpha,cancelled=lambda:True) is None
    assert fit_paint_boundary(np.zeros((0,0))) is None
    assert fit_paint_boundary(np.full((10,10),np.nan)) is None


@pytest.mark.parametrize('size,angle', [(70,1.2),(90,.9),(110,1.7)])
def test_unseen_organic_shapes_retain_holes_and_gradient_direction(size,angle):
    image = synthetic(size,angle)
    result = fit(image)
    assert result is not None
    assert result['quality']['passed'] and result['details']['passed']
    assert measure_quality(image,result['svg'])['satisfactory']
    assert abs(result['gradient_angle_degrees']-np.degrees(angle)) < 8
    assert len(result['rounds']) >= 2
    root = ET.fromstring(result['svg'])
    assert len(root.findall('{*}circle')) == 1
    assert len(root.findall('{*}path')) == 2
    assert all(p.get('stroke') == 'none' for p in root.findall('{*}path'))
    assert not root.findall('.//{*}image')


def test_original_variants_and_consensus_does_not_regress_single():
    for size in ('L','M','S'):
        path = ROOT/f'artifacts/images_to_convert/GE0023_1_{size}.jpg'
        image = cv2.imread(str(path))
        single = fit(image)
        result = fit(image,companion_images=load_piecewise_companions(path))
        assert single is not None and result is not None
        assert result['error'] <= single['error']
        assert all(a['accepted'] for a in result['alignment'])
        assert result['details']['passed']
        assert measure_quality(image,result['svg'])['satisfactory']


def test_alignment_recovers_zoom_and_translation_and_rejects_different_motif():
    image = synthetic(100)
    warped = cv2.warpAffine(image,np.array([[1.,0.,2.],[0.,1.,-1.]],np.float32),(100,100),borderValue=(255,255,255))
    small = cv2.resize(warped,(80,80),interpolation=cv2.INTER_AREA)
    aligned, report = align_piecewise_companions(image,[('shifted',small),('unrelated',np.full_like(image,255))])
    assert len(aligned) == 1 and report[0]['accepted'] and not report[1]['accepted']
    assert report[0]['initial_zoom'] == [1.25,1.25]
    assert abs(report[0]['affine'][0][2]-2) < .5
    assert abs(report[0]['affine'][1][2]+1) < .5
    assert np.mean((image.astype(float)-aligned[0])**2) < np.mean((image.astype(float)-cv2.resize(small,(100,100)))**2)


def test_palette_and_topology_damage_fail_local_validation():
    image = synthetic()
    result = fit(image)
    assert result is not None
    from src.iCCModules.imageCompositeConverterPiecewiseScene import _matte
    background = render(result['background_svg'],90,90).astype(float)
    paints = np.array(result['paints'])
    masks = _matte(image.astype(float),background,paints)
    damaged = result['rendered'].copy()
    damaged[48:54,50:58] = paints[1]
    assert not piecewise_details(image,damaged,background,paints,masks)['passed']


def test_closed_description_and_expired_budget():
    assert piecewise_contract(DESCRIPTION)
    assert piecewise_contract('Im Hintergrund liegt ein Kreis mit grauem Rand und einem farbigen Farbverlauf. '
        'Davor liegt eine farbige Freiform mit dunkler Kontur. '
        'Die Vordergrundform kann Öffnungen und schmale Ausläufer besitzen. '
        'Keine Beschriftung oder weiteren Zeichen.')
    assert not piecewise_contract(DESCRIPTION+' Ein roter Pfeil liegt davor.')
    assert fit(synthetic(),description='Ein Kreis.') is None
    session = ImageSearch(SearchPolicy(),clock=lambda:0)
    session.spent = 121
    with image_search(session):
        assert fit(synthetic(),render_fn=lambda *args:pytest.fail('must not render')) is None


def test_followup_polish_must_preserve_local_topology_and_object_inventory():
    image = synthetic()
    result = fit(image)
    assert result is not None
    assert validate_piecewise_refinement(result,image,result,render)
    moved = dict(result,rendered=np.roll(result['rendered'],8,axis=1))
    assert not validate_piecewise_refinement(moved,image,result,render)
    extra = dict(result,svg=result['svg'].replace('</svg>','<circle cx="3" cy="3" r="2"/></svg>'))
    assert not validate_piecewise_refinement(extra,image,result,render)


def test_size_siblings_do_not_mix_numbered_variants(tmp_path):
    for name in ('shape_1_L.jpg','shape_1_M.jpg','shape_M.jpg','shape_2_S.jpg'):
        cv2.imwrite(str(tmp_path/name),synthetic(70))
    companions = load_piecewise_companions(tmp_path/'shape_1_L.jpg')
    assert [name for name,_ in companions] == ['shape_1_M.jpg']
