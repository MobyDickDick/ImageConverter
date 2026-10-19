"""Real regions must not leak into training or bypass independent acceptance."""
import json

import cv2
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNeuralElements as neural
from src.iCCModules import imageCompositeConverterPrimitiveScene as scene
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration
from tools import run_real_neural_elements as study
from tools.run_plan_b_variations import render, measure_quality


def cases():
    return json.loads(study.ANNOTATIONS.read_text(encoding='utf-8'))['cases']


def test_frozen_real_families_are_disjoint_and_previous_six_are_development_only():
    rows = cases()
    study.validate_cases(rows)
    assert {c['variant'] for c in rows if c['split']=='development'} == study.OLD_FAMILIES
    assert len({c['family'] for c in rows if c['split']=='real_holdout'}) == 10


@pytest.mark.parametrize('damage', ['family', 'pixels', 'old_family', 'too_few', 'invalid_box'])
def test_annotation_contract_rejects_leakage_and_invalid_regions(damage):
    rows = cases()
    target = next(c for c in rows if c['split']=='real_holdout')
    if damage=='family':
        target['family'] = rows[0]['family']
    elif damage=='pixels':
        target['input_sha256'] = rows[0]['input_sha256']
    elif damage=='old_family':
        next(c for c in rows if c['variant'] in study.OLD_FAMILIES)['split']='train'
    elif damage=='too_few':
        rows=[c for c in rows if c['split']!='real_holdout']
    else:
        target['elements'][0]['bbox'][2]=-1
    with pytest.raises(ValueError):
        study.validate_cases(rows)


def test_real_augmentation_never_opens_development_or_holdout_rasters(tmp_path, monkeypatch):
    path=tmp_path/'train.png'
    cv2.imwrite(str(path), np.full((20,20,3), 90, np.uint8))
    rows=[dict(split='train', image=path.name, family='training',
               elements=[dict(kind='rectangle',bbox=[1,1,18,18])]),
          dict(split='development', image='forbidden-dev.png'),
          dict(split='real_holdout', image='forbidden-holdout.png')]
    read=cv2.imread
    opened=[]
    def checked(name, *args):
        opened.append(name)
        assert name==str(path)
        return read(name, *args)
    monkeypatch.setattr(cv2,'imread',checked)
    data=study.real_training_data(tmp_path, rows)
    assert opened==[str(path)]
    assert data['train']['families'].count('training')==16
    assert len(data['train']['images'])==len(data['train']['labels'])


def test_multilevel_regions_recover_bright_nested_letter_and_keep_small_object():
    image=np.full((100,160,3),255,np.uint8)
    cv2.rectangle(image,(15,15),(90,90),(40,40,160),-1)
    cv2.putText(image,'T',(35,66),cv2.FONT_HERSHEY_SIMPLEX,1.3,(255,255,255),3)
    cv2.circle(image,(132,50),5,(60,60,60),2)
    target=[34,36,25,33]
    old=neural.region_boxes(image)
    new=neural.region_boxes_v2(image)
    assert max(neural.box_iou(target,b) for b in new)>.5
    assert max(neural.box_iou(target,b) for b in old)<.5
    assert any(b[2]<18 and b[3]<18 and b[0]>110 for b in new)
    assert len(new)<=128 and len(set(new))==len(new)


def test_local_regions_reject_erased_small_interior_that_global_average_can_hide():
    good=('<svg xmlns="http://www.w3.org/2000/svg" width="150" height="150">'
          '<rect width="150" height="150" fill="white"/>'
          '<circle cx="75" cy="75" r="55" fill="#bbbbbb"/>'
          '<rect x="71" y="71" width="8" height="8" fill="#222222"/></svg>')
    bad=good.replace('<rect x="71" y="71" width="8" height="8" fill="#222222"/>','')
    image=render(good,150,150)
    case=dict(elements=[dict(kind='rectangle',bbox=[71,71,8,8])])
    assert measure_quality(image,bad)['satisfactory']
    assert study.check_regions(case,good,image)['passed']
    assert not study.check_regions(case,bad,image)['passed']


def test_v2_model_reaches_actual_scene_fitting_and_independent_pixel_gate(tmp_path,monkeypatch):
    weights={k:np.zeros(s).tolist() for k,s in neural.SHAPES.items()}
    weights['offset'][neural.CLASSES.index('circle')]=20.
    path=tmp_path/'model.json'
    path.write_text(json.dumps(dict(schema='tiny_elements_cnn_v2',classes=list(neural.CLASSES),weights=weights)))
    image=render('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="80"><rect width="100" height="80" fill="white"/><circle cx="50" cy="40" r="24" fill="none" stroke="#333333" stroke-width="3"/></svg>',100,80)
    monkeypatch.setattr(scene,'_alternatives',lambda *args:[])
    with search_configuration(neural_model=path):
        result=scene.fit_primitive_scene(100,80,description='Ein Kreis. Keine Beschriftung.',image=image,
            render_fn=render,error_fn=lambda a,b:float(np.mean((a.astype(float)-b.astype(float))**2)))
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']


def test_search_seeds_never_inflate_the_number_of_independent_families():
    case=[dict(case_id='one',family='one')]
    rows=[dict(case_id='one',family='one',split='real_holdout',mode=mode,seed=(training,search),
               satisfactory=True,svg_sha256='same')
          for training in study.SEEDS for search in study.SEEDS for mode in ('analytic','neural')]
    decision=study.first.decision(rows,case)
    assert decision['paired_real_trials']==9 and decision['real_families']==1
    assert not decision['promote_to_default']


def censored_row():
    return dict(observation_censored=True, search_control=dict(stop_reason='time_limit',isolated=True),
        image_seconds=600., budget_seconds=5., components=dict(path=None,sha256=None,events=[]),
        observed_controls=[], satisfactory=False, runtime_satisfactory=False, quality=None, structure=None)


def test_unobserved_startup_is_retained_only_as_an_explicit_failure():
    assert study.first.censored_startup(censored_row())


def test_unobserved_baseline_cannot_manufacture_a_positive_promotion():
    cases=[dict(case_id=f'case_{i}',family=f'family_{i}') for i in range(10)]
    rows=[dict(case_id=c['case_id'], family=c['family'], split='real_holdout', mode=mode, seed=17,
               satisfactory=mode=='neural') for c in cases for mode in ('analytic','neural')]
    assert study.first.decision(rows,cases)['promote_to_default']
    rows[0].update(censored_row())
    result=study.decision(rows,cases)
    assert not result['promote_to_default'] and not result['quality_benefit_demonstrated']
    assert result['unobserved_startup_timeouts']==1


@pytest.mark.parametrize('damage', ['svg','acceptance','quality','controls','not_isolated','early','missing_flag'])
def test_unobserved_startup_cannot_hide_outputs_or_invent_model_execution(damage):
    row=censored_row()
    if damage=='svg':
        row['svg']='unchecked.svg'
    elif damage=='acceptance':
        row['satisfactory']=True
    elif damage=='quality':
        row['quality']={'satisfactory':True}
    elif damage=='controls':
        row['observed_controls']=[{'model':True}]
    elif damage=='not_isolated':
        row['search_control']['isolated']=False
    elif damage=='early':
        row['image_seconds']=1.
    else:
        row.pop('observation_censored')
    assert not study.first.censored_startup(row)
