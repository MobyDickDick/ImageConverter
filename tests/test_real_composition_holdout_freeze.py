"""Reserved families cannot silently turn into development trials or successes."""
import json
from pathlib import Path
import shutil

from PIL import Image
import pytest

from tools.evaluate_real_scene import prepare_real
from tools.freeze_real_composition_holdouts import digest, freeze, validate_annotations, verify

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/real_composition_holdout_freeze_v1/freeze'
ANNOTATIONS = ROOT/'config/real_composition_holdout_families.json'


def inventory(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()}


def test_reserved_historical_evidence_is_read_only_and_unrun():
    before = inventory(EVIDENCE)
    # Runtime development may proceed after sealing. The historical snapshot
    # stays immutable; checking it must not silently rebase or release families.
    result = verify(EVIDENCE/'manifest.json')
    assert result == dict(status='sealed_unrun', families=2, converter_executed=False,
                          accepted=None, current_runtime_checked=False)
    assert inventory(EVIDENCE) == before
    assert (EVIDENCE/'annotations.json').read_bytes() == ANNOTATIONS.read_bytes()


def test_standard_real_preparation_cannot_consume_reserved_families(tmp_path):
    output = tmp_path/'accidental-trial'
    with pytest.raises(ValueError, match='Sealed real families'):
        prepare_real(output, ANNOTATIONS)
    assert not output.exists()


def test_existing_real_annotation_preparation_remains_supported(tmp_path):
    import cv2
    import numpy as np
    output = tmp_path/'known-development-inputs'
    annotations = ROOT/'config/real_scene_transfer_families.json'
    prepare_real(output, annotations)
    cases = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    assert len(cases) == 2
    for case in cases:
        original = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['file']))
        decoded = cv2.imread(str(output/case['case_id']/'input'/(case['case_id']+'.png')))
        assert np.array_equal(original, decoded)


@pytest.mark.parametrize('damage', [
    'source', 'pixels', 'description', 'annotation', 'runtime', 'audit', 'missing',
    'extra_trial', 'hidden_manifest', 'accepted', 'executed', 'escape',
])
def test_changed_or_falsely_successful_freeze_fails(tmp_path, damage):
    root = tmp_path/'evidence'
    shutil.copytree(EVIDENCE, root)
    path = root/'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if damage in ('accepted', 'executed'):
        manifest['accepted' if damage == 'accepted' else 'converter_executed'] = True
    elif damage == 'escape':
        manifest['files']['../outside'] = 'fake'
    elif damage == 'missing':
        (root/'runtime.json').unlink()
    elif damage in ('extra_trial', 'hidden_manifest'):
        folder = root/'trial'
        folder.mkdir()
        (folder/('result.svg' if damage == 'extra_trial' else 'manifest.json')).write_text('unexpected')
    else:
        names = dict(source='family_00/original.jpg', pixels='family_00/input.png',
                     description='family_00/description.txt', annotation='annotations.json',
                     runtime='runtime.json', audit='source_audit.json')
        with (root/names[damage]).open('ab') as f:
            f.write(b'changed')
    path.write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError):
        verify(path)


def test_pixel_corruption_fails_even_with_updated_file_seal(tmp_path):
    root = tmp_path/'evidence'
    shutil.copytree(EVIDENCE, root)
    image_path = root/'family_00/input.png'
    with Image.open(image_path) as im:
        pixels = im.convert('RGB')
    pixels.putpixel((0, 0), (1, 2, 3))
    pixels.save(image_path)
    path = root/'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    manifest['files']['family_00/input.png'] = digest(image_path)
    path.write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError, match='Decoded pixels changed'):
        verify(path)


@pytest.mark.parametrize('damage', ['duplicate_family', 'renamed_original', 'shared_descendant', 'development', 'missing_member',
                                    'bad_box', 'bad_relation', 'no_gaps', 'trial_count'])
def test_invalid_family_or_annotation_contract_fails(damage):
    data = json.loads(ANNOTATIONS.read_text(encoding='utf-8'))
    case = data['cases'][0]
    if damage == 'duplicate_family':
        data['cases'][1]['family'] = case['family']
    elif damage == 'renamed_original':
        data['cases'][1]['source_sha256'] = case['source_sha256']
    elif damage == 'shared_descendant':
        data['cases'][1]['family_members'].append(case['file'])
    elif damage == 'development':
        case['split'] = 'development'
    elif damage == 'missing_member':
        case['family_members'] = ['wrong.jpg']
    elif damage == 'bad_box':
        case['expected_objects'][0]['visible_bbox'][2] = 9999
    elif damage == 'bad_relation':
        case['relations'][0]['objects'] = ['missing']
    elif damage == 'no_gaps':
        case['acceptance_gaps'] = []
    else:
        data['evaluation_policy']['converter_trials'] = 1
    with pytest.raises(ValueError):
        validate_annotations(data)


def test_new_freeze_preserves_existing_evidence_and_refuses_overwrite(tmp_path, monkeypatch):
    # Stub the slow historical search; the stored production audit is tested above.
    import tools.freeze_real_composition_holdouts as module
    monkeypatch.setattr(module, 'audit_sources', lambda data, revision:
                        dict(revision=revision, searches=[], limitation='Test audit stub'))
    output = tmp_path/'fresh-freeze'
    result = freeze(ANNOTATIONS, output)
    assert result['converter_executed'] is False
    assert result['current_runtime_checked'] is True
    assert all(b'\r\n' not in path.read_bytes() for path in output.rglob('*')
               if path.suffix in ('.json', '.txt'))
    before = inventory(output)
    with pytest.raises(FileExistsError):
        freeze(ANNOTATIONS, output)
    assert inventory(output) == before
    # An explicit current-runtime comparison must still reject source drift;
    # only the historical integrity mode may ignore subsequent development.
    original_digest = digest
    with monkeypatch.context() as changed:
        changed.setattr(module, 'digest', lambda path:
                        '0'*64 if path.is_relative_to(ROOT/'src') else original_digest(path))
        with pytest.raises(ValueError, match='Runtime changed since freeze'):
            verify(output/'manifest.json', check_current=True)
        assert verify(output/'manifest.json')['status'] == 'sealed_unrun'
    assert inventory(output) == before
