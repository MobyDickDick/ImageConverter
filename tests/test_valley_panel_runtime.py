from pathlib import Path
from xml.etree import ElementTree as ET
import json

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterChevronPanel import fit_chevron_panel
from tools.run_plan_b_variations import render, measure_quality, make_variations, select_task

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Rechteckiges Feld mit dünnem grauem Rahmen und vertikalem grünem Farbverlauf. '
               'Eine weiße offene V-Linie besteht aus zwei geraden Schenkeln, die sich unten in einer Spitze treffen.')


def drawing(width=100, height=60, color='#409951', peak=51, extra='', mark=True):
    light = '#'+''.join(f'{round(int(color[i:i+2],16)*.6+255*.4):02x}' for i in (1,3,5))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 100 60">'
            '<defs><linearGradient id="foreign_paint" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}"/><stop offset=".4" stop-color="{light}"/>'
            f'<stop offset="1" stop-color="{color}"/></linearGradient></defs>'
            '<rect x="8" y="6" width="84" height="48" fill="url(#foreign_paint)" stroke="#999999" stroke-width="1.2"/>'
            + (f'<polyline points="8,28 47,{peak} 92,28" fill="none" stroke="#ffffff" stroke-width="2.5"/>' if mark else '')
            + extra+'</svg>')


def fit(image, description=DESCRIPTION, render_fn=render, error_fn=None):
    return fit_chevron_panel(image.shape[1], image.shape[0], description=description, image=image,
        render_fn=render_fn, error_fn=error_fn or (lambda a,b:float(cv2.absdiff(a,b).mean())))


def assert_native_valley(result, image):
    root = ET.fromstring(result['svg'])
    assert [e.tag.rsplit('}',1)[-1] for e in root] == ['defs','rect','polyline']
    assert not any(e.get('transform') for e in root.iter())
    mark = root.find('{*}polyline')
    points = np.array([list(map(float,pair.split(','))) for pair in mark.get('points').split()])
    assert len(points) == 3 and points[0,0] < points[1,0] < points[2,0]
    assert points[1,1] > max(points[0,1],points[2,1])
    assert 2 <= len(root.findall('.//{*}stop')) <= 9
    assert measure_quality(image,result['svg'])['satisfactory']
    np.testing.assert_array_equal(render(result['svg'],image.shape[1],image.shape[0]),result['rendered'])


@pytest.mark.parametrize('width,height,color,paint', [(100,60,'#409951','grünem'),
    (150,90,'#285ba0','blauem'), (120,72,'#b94030','rotem')])
def test_native_valley_generalizes_resolution_color_and_asymmetric_geometry(width,height,color,paint):
    image = render(drawing(width,height,color),width,height)
    result = fit(image,DESCRIPTION.replace('grünem',paint))
    assert result is not None
    assert_native_valley(result,image)
    assert result['error'] < result['initial_error']


@pytest.mark.parametrize('number,index', [(1909,4),(1909,6),(1909,14),(1999,5),(1999,12),(1999,16)])
def test_original_failed_probes_keep_the_v_line_and_pass_unchanged_gates(number,index):
    manifest = json.loads((ROOT/'artifacts/evaluation/valley_panel_issue_v1/manifest.json').read_text(encoding='utf-8'))
    entry = next(row for row in manifest['replays'] if row['issue'] == number)
    case = make_variations((ROOT/entry['source_svg']).read_text(encoding='utf-8'),DESCRIPTION,entry['seed'])[index-1]
    image = render(case['svg'],case['width'],case['height'])
    calls = []
    def counted(svg,width,height):
        calls.append(svg)
        return render(svg,width,height)
    result = fit(image,case['description'],render_fn=counted)
    assert result is not None
    assert_native_valley(result,image)
    assert result['evaluations'] == len(calls) == len(set(calls)) <= 1800


@pytest.mark.parametrize('kind', ['roof','missing','extra','white_extra','color','direction','axis','negation','unconsumed','frame','mark'])
def test_contradictory_or_incomplete_scene_is_rejected(kind):
    svg = drawing(peak=12 if kind=='roof' else 51,mark=kind!='missing',
                  extra=f'<circle cx="50" cy="20" r="3" fill="{"#ffffff" if kind=="white_extra" else "#111111"}"/>'
                  if kind in {'extra','white_extra'} else '')
    description = DESCRIPTION
    if kind == 'color':
        description = description.replace('grünem','blauem')
    if kind == 'direction':
        description = description.replace('unten','oben')
    if kind == 'axis':
        description = description.replace('vertikalem','horizontalem')
    if kind == 'negation':
        description += ' Keine V-Linie.'
    if kind == 'unconsumed':
        description += ' Ein kleiner Punkt steht oben.'
    if kind == 'frame':
        svg = svg.replace('stroke="#999999"','stroke="#ff0000"')
    if kind == 'mark':
        svg = svg.replace('stroke="#ffffff"','stroke="#111111"')
    assert fit(render(svg,100,60),description) is None


def test_real_jpeg_sizes_have_their_own_description_and_native_geometry():
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    mapping = loadDescriptionMappingImpl(str(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'),
                                        get_base_name_from_file_fn=getBaseNameFromFileImpl)
    for size in ('L','M','S'):
        name = f'AC0552_2_{size}'
        assert mapping[name] == DESCRIPTION
        assert mapping[f'AC0552_1_{size}'] != DESCRIPTION
        assert mapping[f'AC0552_{size}'] != DESCRIPTION
        image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/{name}.jpg'))
        result = fit(image,mapping[name])
        assert result is not None
        assert_native_valley(result,image)
    source = ROOT/'artifacts/samples/AC0552_2_L.svg'
    assert not source.with_suffix('.txt').exists()
    selected,description,_ = select_task(source.parent,ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml',0,
        excluded_svg_paths={p.resolve() for p in source.parent.rglob('*.svg') if p != source})
    assert selected == source.resolve() and description == DESCRIPTION


def test_deadline_render_failures_and_nonfinite_errors_are_rejected(monkeypatch):
    from src.iCCModules import imageCompositeConverterChevronPanel as module
    image = render(drawing(),100,60)
    assert fit(image,render_fn=lambda *args:None) is None
    assert fit(image,error_fn=lambda *args:float('nan')) is None
    class Expired:
        evaluations = 0
        def time_reason(self):
            return 'time_limit'
    monkeypatch.setattr(module,'current_search',lambda:Expired())
    assert fit(image,render_fn=lambda *args:pytest.fail('render after deadline')) is None


@pytest.mark.parametrize('mutation',['reverse','missing','extra','transform'])
def test_independent_saved_shape_verifier_rejects_wrong_topology(mutation):
    from tools.verify_valley_panel_acceptance import check_native
    svg=drawing()
    # Use native output with a pixel coordinate viewport for this audit.
    result=fit(render(svg,100,60))
    assert check_native(result['svg'])
    root=ET.fromstring(result['svg'])
    mark=root.find('{*}polyline')
    if mutation=='reverse':
        points=[list(map(float,p.split(','))) for p in mark.get('points').split()]
        points[1][1]=0
        mark.set('points',' '.join(f'{x},{y}' for x,y in points))
    elif mutation=='missing':
        root.remove(mark)
    elif mutation=='extra':
        ET.SubElement(root,'circle',cx='50',cy='20',r='2')
    else:
        mark.set('transform','translate(1 0)')
    with pytest.raises(AssertionError):
        check_native(ET.tostring(root,encoding='unicode'))
