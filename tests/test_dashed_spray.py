"""Every mist ray needs visible gaps; preserve the already accepted geometry."""
import json
from xml.etree import ElementTree as ET

import cv2
import pytest

from tools.evaluate_dashed_spray import EVIDENCE,annotation,inspect,controls
from tools.check_dashed_spray_scene import check_scene


def delivered():
    return (EVIDENCE/'AC0130_L.svg').read_text(encoding='utf-8')


def test_saved_cli_has_fifteen_dashed_rays_with_real_internal_gaps():
    svg=delivered()
    checked=check_scene(svg,annotation())
    assert checked['complete'],checked
    assert len(checked['rays'])==15
    assert all(len(r['gaps'])>=2 for r in checked['rays'])
    image=cv2.imread(str(EVIDENCE.parent/'spray_panel_v1/inputs/AC0130_L.jpg'))
    assert inspect(svg,image,annotation())['complete']


def test_housing_rail_frame_nozzles_and_ray_coordinates_remain_identical():
    old=ET.fromstring((EVIDENCE/'before.svg').read_text(encoding='utf-8'))
    new=ET.fromstring(delivered())
    non_rays=lambda root:[ET.tostring(n) for n in root.iter() if n.tag.rsplit('}',1)[-1] in {'rect','polygon'}]
    assert non_rays(old)==non_rays(new)
    coords=lambda root:[[n.get(k) for k in ('x1','y1','x2','y2')] for n in root.iter() if n.tag.rsplit('}',1)[-1]=='line']
    assert coords(old)==coords(new)


def test_solid_rays_are_rejected_even_with_the_same_correct_geometric_inventory():
    result=check_scene((EVIDENCE/'before.svg').read_text(encoding='utf-8'),annotation())
    assert not result['complete']


def test_each_missing_component_and_each_individual_solid_ray_is_rejected():
    variants=list(controls(delivered()))
    assert len(variants)==48
    for name,svg in variants:
        assert not check_scene(svg,annotation())['complete'],name


@pytest.mark.parametrize('value',['nan 1','-1 2','0 2','100 1','1 .001','1% 2'])
def test_invalid_or_invisible_gap_patterns_cannot_supply_acceptance(value):
    root=ET.fromstring(delivered())
    line=next(n for n in root.iter() if n.tag.rsplit('}',1)[-1]=='line')
    line.set('stroke-dasharray',value)
    assert not check_scene(ET.tostring(root,encoding='unicode'),annotation())['complete']


def test_forged_labels_cannot_replace_missing_paint():
    root=ET.fromstring(delivered())
    for n in root.iter():
        if n.tag.rsplit('}',1)[-1] in {'g','line'}:
            n.set('id','dashed-mist-claimed')
            n.set('data-part','perfect-dashes')
    assert check_scene(ET.tostring(root,encoding='unicode'),annotation())['complete']
    line=next(n for n in root.iter() if n.tag.rsplit('}',1)[-1]=='line')
    line.attrib.pop('stroke-dasharray')
    assert not check_scene(ET.tostring(root,encoding='unicode'),annotation())['complete']


def test_inputs_contract_and_saved_result_are_hash_bound():
    from tools.evaluate_spray_panel import digest
    for name,sha in json.loads((EVIDENCE/'input_seal.json').read_text(encoding='utf-8')).items():
        assert digest(EVIDENCE/'inputs'/name)==sha
    seal=json.loads((EVIDENCE/'source_seal.json').read_text(encoding='utf-8'))
    for name,sha in seal['files'].items():
        assert digest(EVIDENCE/name)==sha
