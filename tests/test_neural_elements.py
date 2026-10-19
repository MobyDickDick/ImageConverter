"""The optional detector must reach scenes without weakening acceptance."""
import json
from pathlib import Path
import time

import cv2
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNeuralElements as neural
from src.iCCModules import imageCompositeConverterPrimitiveScene as scene
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, settings
from tools import train_neural_elements as training
from tools.run_plan_b_variations import render, measure_quality
from tools.run_neural_elements import detection_check, decision


def constant_model(path, kind='circle'):
    weights={k:np.zeros(s).tolist() for k,s in neural.SHAPES.items()}
    weights['offset'][neural.CLASSES.index(kind)]=20.
    path.write_text(json.dumps(dict(schema='tiny_elements_cnn_v1',classes=list(neural.CLASSES),weights=weights)))
    return path


def circle_image():
    return render('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="80"><rect width="100" height="80" fill="white"/><circle cx="50" cy="40" r="24" fill="none" stroke="#333333" stroke-width="3"/></svg>',100,80)


def fitted(image):
    h,w=image.shape[:2]
    return scene.fit_primitive_scene(w,h,description='Ein Kreis. Keine Beschriftung.',image=image,
        render_fn=render,error_fn=lambda a,b:float(np.mean((a.astype(float)-b.astype(float))**2)))


def test_default_never_loads_a_model(monkeypatch):
    def forbidden(*a):
        raise AssertionError('Default loaded the experimental model')
    monkeypatch.setattr(neural,'load_model',forbidden)
    with search_configuration():
        assert fitted(circle_image()) is not None
        assert settings()['neural_observations']==[]


def test_neural_positions_actually_seed_a_missing_analytic_scene(tmp_path,monkeypatch):
    # Remove the analytic seed; an actual fitted, independently checked output
    # must still be produced from the CNN class and region location.
    monkeypatch.setattr(scene,'_alternatives',lambda *a:[])
    path=constant_model(tmp_path/'model.json')
    image=circle_image()
    with search_configuration(neural_model=path):
        result=fitted(image)
        assert result is not None
        assert measure_quality(image,result['svg'])['satisfactory']
        observation=settings()['neural_observations'][0]
        assert observation['model_sha256']
        assert any(d['kind']=='circle' for d in observation['detections'])


def test_high_confidence_wrong_class_cannot_override_description_or_pixels(tmp_path,monkeypatch):
    path=constant_model(tmp_path/'model.json','rectangle')
    with search_configuration(neural_model=path):
        assert fitted(circle_image()) is not None  # analytic alternative survives
    monkeypatch.setattr(scene,'_alternatives',lambda *a:[])
    with search_configuration(neural_model=path):
        assert fitted(circle_image()) is None


def test_invalid_model_is_observed_and_falls_back(tmp_path):
    path=tmp_path/'model.json'
    path.write_text('{"schema":"executable_pickle"}')
    with search_configuration(neural_model=path):
        assert fitted(circle_image()) is not None
        assert settings()['neural_observations'][0]['error'].startswith('ValueError')


def test_predictions_cached_per_image_and_loaded_once(tmp_path,monkeypatch):
    path=constant_model(tmp_path/'model.json')
    image=circle_image()
    loaded=[]
    load=neural.load_model
    def counted(path):
        loaded.append(path)
        return load(path)
    monkeypatch.setattr(neural,'load_model',counted)
    with search_configuration(neural_model=path):
        first=neural.runtime_proposals(image)
        assert neural.runtime_proposals(image.copy()) is first
        changed=image.copy()
        changed[0,0]=0
        neural.runtime_proposals(changed)
        assert len(loaded)==1
        assert len(settings()['neural_observations'])==2
        assert not settings()['neural_observations'][1]['initialized']


@pytest.mark.parametrize('damage',['shape','nan','large','classes','not_a_mapping'])
def test_untrusted_weight_files_are_bounded_and_validated(tmp_path,damage):
    path=constant_model(tmp_path/'model.json')
    data=json.loads(path.read_text())
    if damage=='shape':
        data['weights']['head']=[]
    elif damage=='nan':
        data['weights']['offset'][0]=float('nan')
    elif damage=='classes':
        data['classes'].reverse()
    elif damage=='not_a_mapping':
        data=[]
    else:
        data['padding']=' '*200001
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        neural.load_model(path)


def test_family_partition_precedes_all_augmentations_and_training_learns():
    data=training.dataset()
    groups=[set(g['families']) for g in data.values()]
    assert all(not a.intersection(b) for i,a in enumerate(groups) for b in groups[i+1:])
    assert all(len(g['families'])==2*len(set(g['families'])) for g in data.values())
    weights,_=training.fit(data,17,epochs=15)
    result=training.classification(weights,data['development'])
    assert result['accuracy']>.85


def test_missed_instances_and_false_confidence_cannot_be_hidden_by_classification():
    target=[dict(kind='circle',bbox=[10,10,20,20]),dict(kind='circle',bbox=[60,10,8,8])]
    predictions=[dict(kind='circle',bbox=[10,10,20,20],confidence=.99),
                 dict(kind='text',bbox=[60,10,8,8],confidence=.99)]
    check=detection_check(predictions,target)
    assert check['matched']==1 and check['missing']==1
    assert check['small_expected']==1 and check['small_matched']==0
    assert check['unmatched_high_confidence']==1


def test_region_deduplication_keeps_separate_small_instances():
    image=np.full((90,170,3),255,np.uint8)
    cv2.circle(image,(40,40),25,(40,40,40),2)
    cv2.circle(image,(130,40),5,(40,40,40),2)
    boxes=neural.region_boxes(image)
    assert len(boxes)==2
    assert min(b[2]*b[3] for b in boxes)<250


def test_repeated_seeds_do_not_create_independent_families_or_establish_equivalence():
    cases=[dict(case_id='one',family='one')]
    records=[dict(case_id='one',family='one',split='real_holdout',mode=mode,seed=seed,
        satisfactory=True,svg_sha256='same') for seed in range(100) for mode in ('analytic','neural')]
    result=decision(records,cases)
    assert result['real_families']==1 and result['paired_real_trials']==100
    assert not result['promote_to_default'] and not result['time_equivalence_established']
    assert result['gained']==result['lost']==0


def blocked_inference_worker(connection,payload):
    import src.iCCModules.imageCompositeConverterNeuralElements as detector
    def blocked(*args):
        (Path(payload['spec']['folder_path'])/'entered-neural').write_text('inference entered')
        time.sleep(30)
    detector.detect=blocked
    with search_configuration(neural_model=payload['action']['model']):
        detector.runtime_proposals(np.full((32,32,3),255,np.uint8))


def test_blocked_real_inference_is_inside_the_process_deadline(tmp_path):
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import SearchPolicy
    from src.iCCModules.imageCompositeConverterDeadline import ImageDeadline
    path=constant_model(tmp_path/'model.json')
    (tmp_path/'input.png').write_bytes(b'source identity')
    spec=dict(filename='input.png',folder_path=str(tmp_path))
    for name in ('svg_out_dir','diff_out_dir','png_out_dir','reports_out_dir'):
        spec[name]=str(tmp_path/name)
        Path(spec[name]).mkdir()
    deadline=ImageDeadline(SearchPolicy(seconds=2.,max_seconds=2.))
    started=time.monotonic()
    (row,failed),failures=deadline.run(spec,config={},action={'model':str(path)},worker=blocked_inference_worker)
    assert time.monotonic()-started<4.
    assert (tmp_path/'entered-neural').exists()
    assert row is None and failed and failures[0]['reason']=='TimeoutError'
    assert not list(Path(spec['svg_out_dir']).glob('*.svg'))
