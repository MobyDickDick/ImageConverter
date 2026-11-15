"""The user's wording and straight-path SVG must reach the humidifier model."""
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterSprayPanel import spray_contract, _dashed_spray_rays, fit_spray_panel
from tools.evaluate_svg_text_baseline import render_librsvg
from tools.run_plan_b_variations import render, make_original_case, make_variations, measure_quality

FIXTURES = Path(__file__).parent/'fixtures'
DESCRIPTION = (FIXTURES/'descriptions/spray_panel_workbench_user.txt').read_text(encoding='utf-8')


@pytest.mark.parametrize('word', ['Queranschlüssen', 'Queranschluessen', 'Sprühdüsen', 'Spruehduesen'])
def test_workbench_wording_selects_humidifier_without_literal_nozzle_name(word):
    assert spray_contract(DESCRIPTION.replace('Queranschlüssen', word))


@pytest.mark.parametrize('extra', [' Ohne Queranschlüsse.', ' Keine Düsen.', ' Ohne Sprühnebel.',
                                  ' Eine Zickzacklinie.', ' Der Rahmen ist durchgezogen.'])
def test_contradictory_wording_still_declines_the_model(extra):
    assert not spray_contract(DESCRIPTION+extra)


@pytest.mark.parametrize('phrase', ['gestrichelte graue Sprühstrahlen',
                                   'gestrichelte hellgraue Linien', 'gestrichelte Spruehstrahlen'])
def test_gray_attribute_does_not_hide_ray_dashes(phrase):
    assert _dashed_spray_rays(phrase)


def test_dashed_inner_rectangle_alone_does_not_request_dashed_rays():
    assert not _dashed_spray_rays('Ein gestricheltes graues Rechteck neben drei grauen Sprühstrahlen.')


def test_actual_workbench_source_path_dashes_match_independent_renderer():
    svg = (FIXTURES/'spray_panel_workbench.svg').read_text(encoding='utf-8')
    reference = render_librsvg(svg,40,80)
    raster = render(svg,40,80)
    # Full-scene edge antialiasing differs between engines. The old solid-path
    # render has MSE .00128; preserving the dashes reduces it to .00028.
    assert np.square(reference.astype(float)-raster).mean()/255**2 < .0004


@pytest.mark.parametrize('index', [0, 1, 2])
def test_subpixel_variations_observe_all_five_nozzles_before_optimization(index):
    svg = (FIXTURES/'spray_panel_workbench.svg').read_text(encoding='utf-8')
    cases = [make_original_case(svg,DESCRIPTION),
             *make_variations(svg,DESCRIPTION,3935970335737749794,expand_canvas=True)]
    case = cases[index]
    image = render(case['svg'],case['width'],case['height'])
    class ObservedAllComponents(Exception):
        pass
    def inspect_initial(candidate,w,h):
        root = ET.fromstring(candidate)
        assert len(root.findall('.//{*}polygon')) == 5
        assert len(root.findall('.//{*}line')) == 15
        raise ObservedAllComponents
    with pytest.raises(ObservedAllComponents):
        fit_spray_panel(case['width'],case['height'],description=DESCRIPTION,image=image,
                        render_fn=inspect_initial,error_fn=lambda a,b:0)


def test_shifted_workbench_variant_passes_every_component_and_saved_vector_gate():
    svg = (FIXTURES/'spray_panel_workbench.svg').read_text(encoding='utf-8')
    case = make_variations(svg,DESCRIPTION,3935970335737749794,expand_canvas=True)[0]
    image = render(case['svg'],case['width'],case['height'])
    fitted = fit_spray_panel(case['width'],case['height'],description=case['description'],image=image,
                            render_fn=render,error_fn=lambda a,b:float(np.square(a.astype(float)-b).mean()))
    assert fitted is not None
    assert all(d['passed'] for d in fitted['details'])
    assert fitted['quality']['passed']
    assert measure_quality(image,fitted['svg'])['satisfactory']
    root = ET.fromstring(fitted['svg'])
    assert len(root.findall('.//{*}polygon')) == 5
    rays = root.findall('.//{*}line')
    assert len(rays) == 15 and all(ray.get('stroke-dasharray') for ray in rays)
