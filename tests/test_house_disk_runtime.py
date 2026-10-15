from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterHouseDisk import fit_house_disk
from tools.evaluate_house_disk_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/house_disk_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_house_disk(width,height,description=description,image=image,
        render_fn=kwargs.get('render_fn',render),
        error_fn=kwargs.get('error_fn',lambda a,b:normalized_mse(a,b)[0]))


def test_catalog_raster_passes_without_mutation():
    image = cv2.imread(str(EVIDENCE/MANIFEST['cases'][0]['image']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert result['evaluations'] <= 1+16*len(result['parameters'])
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image,result['svg'])['satisfactory']
    np.testing.assert_array_equal(image,original)


@pytest.mark.parametrize('scale,shift,color',[(.5,0,'#265944'),(1,-3,'#872f35'),(1,3,'#243972'),(2,2,'#704926')])
def test_independent_resolution_position_and_palette(scale,shift,color):
    root=ET.fromstring(INDEPENDENT)
    root.set('width',str(104*scale));root.set('height',str(98*scale))
    group=ET.Element('g',transform=f'translate({shift} 0)')
    for element in list(root)[2:]:
        root.remove(element);group.append(element)
        if element.get('fill')=='#473256':element.set('fill',color)
    root.append(group)
    image=render(ET.tostring(root,encoding='unicode'),round(104*scale),round(98*scale))
    result=fit(image)
    assert result is not None
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('case',make_variations(INDEPENDENT,DESCRIPTION,20261015),ids=lambda c:c['case_id'])
def test_independent_subpixel_variations(case):
    image=render(case['svg'],case['width'],case['height'])
    result=fit(image,case['description'])
    assert result is not None
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('mutation',['no_disk','no_house','no_door','no_window','no_vertical','no_horizontal','extra_mark','detached','chimney','door_right','clipped_disk'])
def test_incompatible_topology_is_rejected(mutation):
    root=ET.fromstring(INDEPENDENT)
    if mutation=='no_disk':root.remove(root[2])
    elif mutation=='no_house':root.remove(root[3])
    elif mutation=='no_door':root.remove(root[4])
    elif mutation=='no_window':root.remove(root[5])
    elif mutation=='no_vertical':root.remove(root[6])
    elif mutation=='no_horizontal':root.remove(root[7])
    elif mutation=='extra_mark':ET.SubElement(root,'rect',x='44',y='28',width='9',height='5',fill='#ffffff')
    elif mutation=='detached':ET.SubElement(root,'rect',x='1',y='1',width='5',height='5',fill='#000000')
    elif mutation=='chimney':ET.SubElement(root,'rect',x='63',y='23',width='7',height='15',fill='#473256')
    elif mutation=='clipped_disk':root[2].set('cy','35')
    else:root[4].set('x','58')
    assert fit(render(ET.tostring(root,encoding='unicode'),104,98)) is None


@pytest.mark.parametrize('description',['Ein Haus.',DESCRIPTION+' Zusätzlich eine Linie.',
    DESCRIPTION+' ohne Tür.',DESCRIPTION.replace('Satteldach','Flachdach'),
    DESCRIPTION.replace('Links in der Fassade','Rechts in der Fassade'),
    DESCRIPTION.replace('vertikal','horizontal')])
def test_conflicting_descriptions_are_rejected(description):
    assert fit(render(INDEPENDENT,104,98),description) is None


@pytest.mark.parametrize('failure',['render','nan_error','infinite_error','dimensions','nan_image'])
def test_invalid_inputs_and_measurements_are_rejected(failure):
    image=render(INDEPENDENT,104,98);kwargs={}
    if failure=='render':kwargs['render_fn']=lambda *args:None
    elif failure.endswith('_error'):kwargs['error_fn']=lambda *args:float('nan' if failure=='nan_error' else 'inf')
    elif failure=='dimensions':image=image[:,:,:2]
    else:image=image.astype(float);image[0,0,0]=np.nan
    assert fit(image,**kwargs) is None


def test_saved_cli_evidence_passes_unchanged_gates():
    report=evaluate(MANIFEST,EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in report['strict_pixel_gates'].values())


@pytest.mark.parametrize('mutation',['window','cross','roof','raster'])
def test_independent_semantics_reject_wrong_structure(mutation):
    assert symbol_semantics(INDEPENDENT)==1
    root=ET.fromstring(INDEPENDENT)
    if mutation=='window':root[5].set('x','12')
    elif mutation=='cross':root[6].set('height','1')
    elif mutation=='roof':root[3].set('d','M 19 44 L 49 44 L 83 44 L 75 44 L 75 73 L 27 73 L 27 44 Z')
    else:ET.SubElement(root,'image',href='fake.png')
    assert symbol_semantics(ET.tostring(root,encoding='unicode'))==0


def test_both_catalogs_supply_self_contained_description():
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    for directory in ('descriptions','images_to_convert'):
        descriptions=loadDescriptionMappingImpl(str(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml'),
                                               get_base_name_from_file_fn=getBaseNameFromFileImpl)
        assert descriptions['GE0346']==DESCRIPTION
