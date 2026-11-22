from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterHollowCrossPanel import fit_hollow_cross_panel, observe_hollow_cross
from tools.run_plan_b_variations import render, measure_quality

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Graues Rechteck hochkant mit grauem Rand und horizontalem Farbverlauf. '
               'Die beiden Diagonalen sind am Rand beschnitten. Bei der Diagonale von oben rechts '
               'nach unten links ist die Mitte ausgeschnitten. Im Zentrum ein Quadrat '
               'mit grauem Rand und ohne Füllung.')


def drawing(width=60,height=400,*,diamond=True,slit=True,filled=False,open_edge=False):
    # Keep the square square in displayed coordinates, also on nonuniform
    # canvases. The previous fixture silently stretched the named square.
    ry = 26*(width/60)/(height/400)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 60 400" preserveAspectRatio="none">'
            '<defs><linearGradient id="p" gradientUnits="userSpaceOnUse" x1="0" x2="60" y1="0" y2="0">'
            '<stop stop-color="#c4c4c4"/><stop offset=".38" stop-color="#f9f9f9"/>'
            '<stop offset="1" stop-color="#c9c9c9"/></linearGradient></defs>'
            '<rect width="60" height="400" fill="url(#p)"/>'
            '<path d="M 60 0 L 0 400" stroke="#898989" stroke-width="8"/>'
            +('<polygon points="59.2,0 60,0 60,5.333333 .8,400 0,400 0,394.666667" fill="url(#p)"/>' if slit else '')
            +'<path d="M 0 0 L 60 400" stroke="#868686" stroke-width="7"/>'
            +(f'<path d="M 30 {200-ry} L 56 200 L 30 {200+ry} L 4 200 {"" if open_edge else "Z"}" '
              f'fill="{"#888888" if filled else "none"}" stroke="#888888" stroke-width="2.6"/>' if diamond else '')
            +'<rect x=".5" y=".5" width="59" height="399" fill="none" stroke="#aaaaaa" stroke-width=".8"/></svg>')


@pytest.mark.parametrize('width,height',[(40,260),(60,400),(90,540)])
def test_independent_native_scenes_keep_four_edges_and_light_slit(width,height):
    image = render(drawing(width,height),width,height)
    result = fit_hollow_cross_panel(width,height,description=DESCRIPTION,image=image,
        render_fn=render,error_fn=lambda a,b: float(((a.astype(float)-b.astype(float))**2).mean()/255**2))
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']
    validate_svg_assertions(result['svg'],description_assertions(DESCRIPTION))
    root = ET.fromstring(result['svg'])
    assert not any(e.tag.endswith('image') for e in root.iter())


@pytest.mark.parametrize('damage',[dict(diamond=False),dict(slit=False),dict(filled=True),dict(open_edge=True)])
def test_missing_or_filled_details_cannot_receive_semantic_acceptance(damage):
    svg = drawing(**damage)
    assert observe_hollow_cross(render(svg,60,400)) is None
    with pytest.raises(ValueError,match='hollow_cross_panel'):
        validate_svg_assertions(svg,description_assertions(DESCRIPTION))


@pytest.mark.parametrize('filename', ['AC0140_L.jpg', 'AC0140_M.jpg'])
def test_real_jpeg_and_unedited_user_description(filename):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/filename))
    height,width = image.shape[:2]
    description = ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').find(
        f".//bild[.='{filename}']").get('beschreibung')
    result = fit_hollow_cross_panel(width,height,description=description,image=image,
        render_fn=render,error_fn=lambda a,b: float(((a.astype(float)-b.astype(float))**2).mean()/255**2))
    assert result is not None
    assert result['quality']['normalized_mse'] < .001
    assert result['quality']['edge_alignment'] > .9
    validate_svg_assertions(result['svg'],description_assertions(description))


@pytest.mark.parametrize('width,height', [(50,230), (68,315)])
def test_occluded_vertices_do_not_define_the_outline_center(width,height):
    # Independent twin strokes, rather than a thick diagonal with a painted
    # middle. Their overlap hides the top and bottom of the small diamond.
    cx,cy,radius = width*.5,height*.5,width*.43
    dx = width/height
    body = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            '<defs><linearGradient id="p"><stop stop-color="#c5c5c5"/>'
            '<stop offset=".4" stop-color="#fafafa"/><stop offset="1" stop-color="#c5c5c5"/></linearGradient></defs>'
            f'<rect width="{width}" height="{height}" fill="url(#p)"/>')
    for offset in (-width*.055,width*.055):
        body += (f'<line x1="{width+offset+dx*10}" y1="-10" x2="{offset-dx*10}" '
                 f'y2="{height+10}" stroke="#888888" stroke-width="{width*.05}"/>')
    body += (f'<line x1="{-dx*10}" y1="-10" x2="{width+dx*10}" y2="{height+10}" '
             f'stroke="#888888" stroke-width="{width*.12}"/>'
             f'<polyline points="{cx},{cy-radius} {cx+radius},{cy} {cx},{cy+radius} {cx-radius},{cy} {cx},{cy-radius}" '
             f'fill="none" stroke="#888888" stroke-width="{width*.045}"/>'
             f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" fill="none" stroke="#aaaaaa"/></svg>')
    observed = observe_hollow_cross(render(body,width,height))
    assert observed is not None
    assert np.max(abs(np.asarray(observed['diamond'])-[cx,cy,radius,radius])) < 1.1


@pytest.mark.parametrize('spelling', ['Linien', 'Linen'])
def test_parallel_pair_wording_and_cutout_wording_have_the_same_structure(spelling):
    parallel = DESCRIPTION.replace('Bei der Diagonale von oben rechts nach unten links ist die Mitte ausgeschnitten.',
        f'Die Diagonale von oben rechts nach unten links wird durch zwei parallele {spelling} gebildet.')
    claims = description_assertions(parallel)
    assert claims.get('hollow_cross_panel')
    validate_svg_assertions(drawing(),claims)
    with pytest.raises(ValueError,match='hollow_cross_panel'):
        validate_svg_assertions(drawing(slit=False),claims)


def test_parallel_diagonal_uses_two_clipped_strokes_without_a_background_patch():
    image = render(drawing(50,230),50,230)
    fitted = fit_hollow_cross_panel(50,230,description=DESCRIPTION,image=image,
        render_fn=render,error_fn=lambda a,b: float(((a.astype(float)-b.astype(float))**2).mean()/255**2))
    assert fitted is not None
    root = ET.fromstring(fitted['svg'])
    filled = [node for node in root if node.tag.endswith('polygon') and node.get('fill') != 'none']
    assert len(filled) == 3  # two rails and the other diagonal
    bounds = observe_hollow_cross(image)['bounds']
    for node in filled:
        assert 'url(' not in node.get('fill','')
        points = np.fromstring(node.get('points').replace(',',' '),sep=' ').reshape(-1,2)
        assert np.all(points >= np.array(bounds[:2])-.01)
        assert np.all(points <= np.array(bounds[2:])+.01)


def test_wrong_template_can_switch_to_a_fresh_construction_from_its_own_raster(tmp_path):
    from src.imageConverterSample import refine
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
    source = ROOT/'artifacts/images_to_convert/AC0140_M.jpg'
    image = cv2.imread(str(source)); height,width = image.shape[:2]
    description = ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').find(
        ".//bild[.='AC0140_M.jpg']").get('beschreibung')
    neutral = tmp_path/'unrelated.png'
    cv2.imwrite(str(neutral),image)
    # Wrong aspect ratio is a construction error; moving its existing parts
    # together cannot recover the central square's independent proportions.
    template = tmp_path/'old.svg'
    template.write_text(drawing(50,230),encoding='utf-8')
    output = tmp_path/'new.svg'
    before = pixel_quality(image,render(template.read_text(),width,height))
    report = refine(neutral,template,output,description,15.,seed=17)
    assert report['passed'] and report['restarted_from_description']
    final = render(output.read_text(),width,height)
    assert pixel_quality(image,final)['normalized_mse'] < before['normalized_mse']*.6
    observed = observe_hollow_cross(final)
    assert observed is not None
    _,_,rx,ry = observed['diamond']
    assert abs(rx-ry) < 2.


def test_bad_renderer_and_error_are_rejected():
    image = render(drawing(),60,400)
    kwargs = dict(description=DESCRIPTION,image=image)
    assert fit_hollow_cross_panel(60,400,**kwargs,render_fn=lambda *args:None,error_fn=lambda a,b:0) is None
    assert fit_hollow_cross_panel(60,400,**kwargs,render_fn=render,error_fn=lambda a,b:float('nan')) is None


def test_globally_passing_sample_requires_real_detail_repair_before_acceptance(tmp_path):
    from src.imageConverterSample import refine
    source,sample,output = (tmp_path/name for name in ('source.png','old.svg','result.svg'))
    cv2.imwrite(str(source),render(drawing(),60,400))
    sample.write_text(drawing(diamond=False,slit=False),encoding='utf-8')
    report = refine(source,sample,output,DESCRIPTION,1.)
    assert report['initial_quality']['passed']
    with pytest.raises(ValueError, match='hollow_cross_panel'):
        validate_svg_assertions(sample.read_text(), description_assertions(DESCRIPTION))
    if report['passed']:
        assert report['improved'] and report['restarted_from_description']
        validate_svg_assertions(output.read_text(), description_assertions(DESCRIPTION))
    else:
        assert 'hollow_cross_panel' in report['description_error']


@pytest.mark.parametrize('width,height,dx,dy',[(48,320,3,17),(75,450,21,31)])
def test_panel_bounds_and_gradient_are_independent_of_translated_canvas(width,height,dx,dy):
    image = np.full((height+65,width+35,3),255,dtype=np.uint8)
    image[dy:dy+height,dx:dx+width] = render(drawing(width,height),width,height)
    h,w = image.shape[:2]
    result = fit_hollow_cross_panel(w,h,description=DESCRIPTION,image=image,
        render_fn=render,error_fn=lambda a,b:float(((a.astype(float)-b.astype(float))**2).mean()/255**2))
    assert result is not None
    validate_svg_assertions(result['svg'],description_assertions(DESCRIPTION))
    assert measure_quality(image,result['svg'])['satisfactory']
    observed = observe_hollow_cross(result['rendered'])
    assert np.max(abs(np.asarray(observed['bounds'])-[dx,dy,dx+width,dy+height])) <= 1
    # Enlarging the panel into the white canvas can pass broad global gates.
    # These local strips must remain background in the delivered vector.
    assert result['rendered'][:dy-1].min() >= 245
    assert result['rendered'][dy+height+1:].min() >= 245
