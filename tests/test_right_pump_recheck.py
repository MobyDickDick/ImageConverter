"""Filled right-facing circles and independent two-source CLI rechecks."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
from xml.etree import ElementTree as ET

import cv2
import pytest

from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
from tools import run_pump_recheck as runner
from tools.evaluate_pump_recheck import circle_triangle_semantics
from tools.review_conversion_quality import normalized_mse
from test_pump_runtime import convert

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT/'artifacts/evaluation/right_pump_recheck_v1/manifest.json'
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda case: case['source'])
def test_filled_right_triangle_variants_pass_with_anonymous_runtime_input(case, monkeypatch):
    image = cv2.imread(str((MANIFEST_PATH.parent/case['image']).resolve()))
    assert image is not None
    svg, raster = convert(image, 'unrelated_observation', monkeypatch, MANIFEST['description'])
    assert circle_triangle_semantics(svg, 'rechts') == 1
    # The regular package accepts saved SVGs through both versioned gates.
    # JPEG threshold masks can differ from vector coverage; the separate
    # stricter Plan-B IoU requirement is evaluated and reported independently.
    assert normalized_mse(image, raster)[1] < .003


@pytest.mark.parametrize('catalog', ['images_to_convert', 'descriptions'])
def test_xml_separates_filled_and_outline_topologies_without_catalog_references(catalog):
    mapping = loadDescriptionMappingImpl(str(ROOT/f'artifacts/{catalog}/Finale_Wurzelformen_V3.xml'),
                                        get_base_name_from_file_fn=getBaseNameFromFileImpl)
    for case in MANIFEST['cases']:
        assert mapping[Path(case['source']).stem] == MANIFEST['description']
    for name in MANIFEST['excluded_topologies']['images']:
        description = mapping[Path(name).stem]
        assert 'Kontur eines nach rechts' in description
        assert 'keine kontrastierende Füllfläche' in description
        assert 'Wie AC' not in description


def test_recheck_preserves_measurement_inputs_and_uses_fresh_copies_for_each_cli(tmp_path, monkeypatch):
    source = tmp_path/'source.png'
    source.write_bytes(b'independent raster')
    manifest = {'description': 'new scene', 'baseline_description': 'old scene',
                'cases': [{'case_id': 'unrelated', 'image': source.name,
                           'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}]}
    manifest_path = tmp_path/'manifest.json'
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    output = tmp_path/'fresh'
    calls = []

    def fake_cli(command, **kwargs):
        worker = command.index('--_worker')
        mode, run_dir, inputs = command[worker+1:worker+4]
        inputs, run_dir = Path(inputs), Path(run_dir)
        assert command[command.index('--start')+1] == 'unrelated'
        assert command[command.index('--end')+1] == 'unrelated'
        assert command[command.index('--execution-mode')+1] == 'semantic-only'
        assert (inputs/'unrelated.png').read_bytes() == source.read_bytes()
        expected = 'old scene' if mode == 'baseline' else 'new scene'
        assert ET.parse(inputs/'descriptions.xml').findtext('entry/beschreibung') == expected
        # The real converter can archive a good/failed input. This must not
        # remove the immutable input or the following worker's input.
        (inputs/'archive').mkdir()
        shutil.move(str(inputs/'unrelated.png'), inputs/'archive/unrelated.png')
        (run_dir/'converted_svgs').mkdir(parents=True)
        (run_dir/'converted_svgs/unrelated.svg').write_text('<svg/>', encoding='utf-8')
        (output/'reference_access.json').write_text('{"blocked_svg_reads": []}', encoding='utf-8')
        calls.append(inputs)

    def fake_evaluate(measured_manifest, root):
        assert (root/measured_manifest['cases'][0]['image']).read_bytes() == source.read_bytes()
        return {'satisfaction_gate': {'summary': {}, 'cases': [{'satisfactory': True}]}}

    monkeypatch.setattr(runner.subprocess, 'run', fake_cli)
    monkeypatch.setattr(runner, 'evaluate', fake_evaluate)
    monkeypatch.setattr(sys, 'argv', ['recheck', str(manifest_path), '--output-dir', str(output)])
    assert runner.main() == 0
    assert calls[0] != calls[1]
    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    assert report['reference_access'] == {mode: {'blocked_svg_reads': []} for mode in ('before', 'after')}


@pytest.mark.parametrize('problem', ['hash', 'duplicate', 'empty'])
def test_recheck_rejects_invalid_provenance_before_starting_cli(problem, tmp_path, monkeypatch):
    image = tmp_path/'input.png'
    image.write_bytes(b'raster')
    cases = [{'case_id': 'scene', 'image': image.name, 'source_sha256': 'incorrect'}]
    if problem == 'duplicate':
        cases = [{'case_id': name, 'image': image.name} for name in ('scene', 'SCENE')]
    if problem == 'empty':
        cases = []
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'description': 'scene', 'cases': cases}), encoding='utf-8')
    monkeypatch.setattr(sys, 'argv', ['recheck', str(manifest), '--output-dir', str(tmp_path/'fresh')])
    monkeypatch.setattr(runner.subprocess, 'run', lambda *a, **k: pytest.fail('must not start CLI'))
    with pytest.raises(ValueError, match={'hash': 'hash mismatch', 'duplicate': 'unique', 'empty': 'At least one'}[problem]):
        runner.main()
