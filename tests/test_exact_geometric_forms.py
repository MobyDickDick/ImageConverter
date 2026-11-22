"""Named forms remain mathematical primitives throughout shared validation."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterHollowCrossPanel import fit_hollow_cross_panel
from src.iCCModules.imageCompositeConverterRepresentation import straight_strip
from tests.test_hollow_cross_panel_runtime import DESCRIPTION, drawing
from tools.run_plan_b_variations import render, measure_quality

ROOT = Path(__file__).resolve().parents[1]


def scene(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80">{body}</svg>'


@pytest.mark.parametrize('description,body', [
    ('Ein Quadrat.', '<rect x="10" y="10" width="30" height="30.1"/>'),
    ('Ein Quadrat.', '<rect x="10" y="10" width="30" height="30" rx="1"/>'),
    ('Ein Quadrat.', '<polygon points="10,10 40,10 40.1,40 10,40"/>'),
    ('Ein Quadrat.', '<polygon points="40,10 60,40 40,70 20,40"/>'),
    ('Ein Rechteck.', '<polygon points="10,10 40,10 40.1,60 10,60"/>'),
    ('Ein Rechteck.', '<g transform="matrix(1 0 .0087 1 0 0)"><rect x="10" y="10" width="30" height="40"/></g>'),
    ('Ein Kreis.', '<ellipse cx="40" cy="40" rx="20" ry="20.05"/>'),
    ('Ein Kreis.', '<g transform="scale(1.001 1)"><circle cx="40" cy="40" r="20"/></g>'),
    ('Eine Gerade.', '<polyline points="10,40 40,40.01 70,40" fill="none" stroke="gray"/>'),
    ('Eine diagonale Gerade.', '<polygon points="10,10 13,10 70,70 67,70 30,33 27,32"/>'),
    ('Eine Gerade.', '<line x1="40" y1="40" x2="40" y2="40"/>'),
    ('Ein Rechteck.', '<rect width="0" height="40"/>'),
    ('Eine Ellipse.', '<ellipse cx="40" cy="40" rx="20" ry="0"/>'),
    ('Eine Raute.', '<polygon points="10,10 40,10 40,60 10,60"/>'),
])
def test_pixel_close_deformations_do_not_prove_the_requested_form(description,body):
    with pytest.raises(ValueError,match='logical_object_count'):
        validate_svg_assertions(scene(body),description_assertions(description))


@pytest.mark.parametrize('description,body', [
    ('Ein Quadrat.', '<g transform="translate(5 2) rotate(13) scale(.7)"><rect x="10" y="10" width="30" height="30"/></g>'),
    ('Ein Kreis.', '<g transform="scale(2 1)"><ellipse cx="20" cy="40" rx="10" ry="20"/></g>'),
    ('Ein Rechteck.', '<polygon points="10,10 40,10 40,60 10,60"/>'),
    ('Eine Gerade.', '<path d="M 10 40 L 30 40 L 70 40" fill="none" stroke="gray"/>'),
    ('Ein Dreieck.', '<polygon points="10,10 70,30 20,60"/>'),
    ('Eine Ellipse.', '<ellipse cx="40" cy="40" rx="20" ry="30"/>'),
    ('Eine Raute.', '<polygon points="40,10 60,40 40,70 20,40"/>'),
])
def test_legitimate_primitive_transforms_and_encodings_remain_valid(description,body):
    validate_svg_assertions(scene(body),description_assertions(description))


def test_an_appendage_is_not_a_clipped_straight_band():
    clean = np.array([[0.,0.],[3.,0.],[60.,380.],[60.,400.],[57.,400.],[0.,20.]])
    assert straight_strip(clean)
    angle = .37
    rotation = np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    assert straight_strip(clean @ rotation.T)
    damaged = np.insert(clean,2,[[6.,3.],[4.,4.]],axis=0)
    assert not straight_strip(damaged)


def test_small_kink_on_an_otherwise_matching_diagonal_is_rejected():
    svg = drawing().replace('M 60 0 L 0 400','M 60 0 L 52.5 50 L 53 50 L 0 400')
    original = render(drawing(),60,400)
    assert measure_quality(original,svg)['satisfactory']
    with pytest.raises(ValueError,match='hollow_cross_panel'):
        validate_svg_assertions(svg,description_assertions(DESCRIPTION))


@pytest.mark.parametrize('description,body', [
    ('Ein Kreis.','<circle cx="40" cy="40" r="20"/>'),
    ('Ein Quadrat.','<rect x="20" y="20" width="40" height="40"/>'),
])
def test_viewport_stretching_cannot_bypass_form_constraints(description,body):
    svg = scene(body).replace('width="80"','width="120"',1).replace(
        'height="80"','height="80" viewBox="0 0 80 80" preserveAspectRatio="none"',1)
    with pytest.raises(ValueError,match='logical_object_count'):
        validate_svg_assertions(svg,description_assertions(description))
    validate_svg_assertions(svg.replace('preserveAspectRatio="none"','preserveAspectRatio="xMidYMid meet"'),
                            description_assertions(description))


def circle_drawing(width,height):
    # Independent native circle, with the same surrounding panel as the square.
    root = ET.fromstring(drawing(width,height))
    outline = root.findall('{*}path')[-1]
    index = list(root).index(outline)
    root.remove(outline)
    root.insert(index,ET.Element('{http://www.w3.org/2000/svg}ellipse',
        cx='30',cy='200',rx='23',ry=str(23*(width/60)/(height/400)),
        fill='none',stroke='#888888',attrib={'stroke-width':'2.6'}))
    return ET.tostring(root,encoding='unicode')


@pytest.mark.parametrize('width,height',[(60,400),(50,230),(80,420)])
def test_circle_panel_reconstructs_a_true_unfilled_circle(width,height):
    description = DESCRIPTION.replace('ein Quadrat','einen Kreis')
    image = render(circle_drawing(width,height),width,height)
    fitted = fit_hollow_cross_panel(width,height,description=description,image=image,render_fn=render,
        error_fn=lambda a,b:float(((a.astype(float)-b.astype(float))**2).mean()/255**2))
    assert fitted is not None
    validate_svg_assertions(fitted['svg'],description_assertions(description))
    assert measure_quality(image,fitted['svg'])['satisfactory']
    circle = ET.fromstring(fitted['svg']).find('{*}circle')
    assert circle is not None and float(circle.get('r')) > 0 and circle.get('fill') == 'none'
    with pytest.raises(ValueError):
        validate_svg_assertions(fitted['svg'],description_assertions(DESCRIPTION))


def test_reported_original_keeps_its_circle_with_its_unchanged_description():
    source = ROOT/'artifacts/images_to_convert/AC0150_L.jpg'
    image = cv2.imread(str(source));height,width = image.shape[:2]
    description = ET.parse(source.parent/'Finale_Wurzelformen_V3.xml').find(
        ".//bild[.='AC0150_L.jpg']").get('beschreibung')
    fitted = fit_hollow_cross_panel(width,height,description=description,image=image,render_fn=render,
        error_fn=lambda a,b:float(((a.astype(float)-b.astype(float))**2).mean()/255**2))
    assert fitted is not None and fitted['quality']['normalized_mse'] < .0005
    validate_svg_assertions(fitted['svg'],description_assertions(description))
    assert ET.fromstring(fitted['svg']).find('{*}circle') is not None


def test_wrong_square_template_is_reconstructed_as_circle_from_a_neutral_source(tmp_path):
    from src.imageConverterSample import refine
    image = render(circle_drawing(60,400),60,400)
    source,sample,output = (tmp_path/name for name in ('neutral.png','wrong.svg','result.svg'))
    cv2.imwrite(str(source),image)
    sample.write_text(drawing(),encoding='utf-8')
    description = DESCRIPTION.replace('ein Quadrat','einen Kreis')
    report = refine(source,sample,output,description,15.,seed=17)
    assert report['passed'] and report['restarted_from_description']
    validate_svg_assertions(output.read_text(),description_assertions(description))
    assert ET.parse(output).find('.//{*}circle') is not None
