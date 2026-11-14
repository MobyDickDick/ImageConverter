"""Explicit text absence survives badge dispatch, defaults and draft output."""
from pathlib import Path

import pytest

from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from src.iCCModules.imageCompositeConverterSemanticBadgeRuntime import _generic_description_badge_params


DESCRIPTION = ('Wie AC0811: Kelle, ohne Text Kreis oben, Griff nach links '
               '(dunkelgraue Liine). Der Griff liegt auf einer Symmetrieachse des Kreises.')
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('absence', ['ohne Text', 'ohne Beschriftung', 'ohne Schriftzeichen',
                                   'kein Text', 'keine Schriftzeichen', 'ohne Buchstabe'])
@pytest.mark.parametrize('name', ['UPLOAD', 'AC0812_L', 'AC0835_L'])
def test_explicit_absence_overrides_generic_and_family_labels(absence, name):
    _, params = Reflection({name: DESCRIPTION.replace('ohne Text', absence)}).parse_description(name, name+'.png')
    assert params['label'] == ''
    assert 'SEMANTIC: Kreis ohne Buchstabe' in params['elements']
    badge = _generic_description_badge_params(45, 25, params)
    assert badge is not None and not badge['draw_text'] and badge['label'] == ''
    assert badge['connector_direction'] == 'left'


def test_no_text_does_not_disable_explicitly_requested_text_in_another_image():
    reflection = Reflection({'plain': DESCRIPTION,
                             'marked': 'Kelle mit Kreis und Griff nach links. Text "P".'})
    reflection.parse_description('plain', 'plain.png')
    _, params = reflection.parse_description('marked', 'marked.png')
    badge = _generic_description_badge_params(45, 25, params)
    assert badge['draw_text'] and badge['label'] == 'P'


def test_no_text_contract_applies_to_failed_drafts():
    from types import SimpleNamespace
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import DescriptionRejected, description_assertions
    from src.iCCModules.imageCompositeConverterIterationInitialization import prepareIterationRuntimeImpl

    saved = []
    setup = SimpleNamespace(emitIterationDescriptionHeaderImpl=lambda **kw: None,
        ensureIterationOutputDirsImpl=lambda **kw: None,
        buildIterationBaseAndLogPathImpl=lambda **kw: ('neutral', 'unused.log'))
    runtime = SimpleNamespace(buildIterationArtifactCallbacksImpl=lambda **kw: dict(
        write_attempt_artifacts=lambda *args, **kw: saved.append(args)))
    state = prepareIterationRuntimeImpl(filename='neutral.png', params=dict(
        language_assertions=description_assertions(DESCRIPTION)),
        reports_out_dir=None, svg_out_dir='unused', diff_out_dir='unused', target_img=None,
        width=45, height=25, run_seed=0, pass_seed_offset=0, iteration_setup_helpers=setup,
        iteration_runtime_helpers=runtime, time_ns_fn=lambda: 0,
        render_svg_to_numpy_fn=lambda *args: None, create_diff_image_fn=None, cv2_module=None)
    writer = state['artifact_callbacks']['write_attempt_artifacts']
    for failed in (False, True):
        with pytest.raises(DescriptionRejected, match='unexpected_text_in_svg'):
            writer('<svg><circle r="10"/><text>M</text></svg>', failed=failed)
    assert saved == []
    writer('<svg><circle r="10"/></svg>', failed=True)
    assert len(saved) == 1


def test_uploaded_original_converts_without_text(tmp_path):
    import os
    import subprocess
    import sys
    from xml.etree import ElementTree as ET
    from PIL import Image
    from src.imageConverterGui import collect_result, write_description_table

    inputs = tmp_path/'input'
    inputs.mkdir()
    # Use the GUI's neutral filename so catalog defaults cannot hide the bug.
    with Image.open(ROOT/'artifacts/images_to_convert/AC0812_L.jpg') as image:
        image.save(inputs/'UPLOAD.png')
        image.save(tmp_path/'source.png')
    write_description_table(tmp_path/'description.csv', DESCRIPTION, {})
    environment = os.environ.copy()
    environment.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='1', IMAGE_CONVERTER_REUSE_RENDER_WORKER='1',
                       ICC_MAX_QUALITY_PASSES='0', ICC_CONVERSION_TIMEOUT_SEC='45')
    completed = subprocess.run([sys.executable, '-m', 'src.imageCompositeConverter', str(inputs),
        '--descriptions-path', str(tmp_path/'description.csv'), '--output-dir', str(tmp_path/'output'),
        '--start', 'UPLOAD', '--end', 'UPLOAD', '--execution-mode', 'semantic-only',
        '--search-seconds', '35', '--search-max-seconds', '45', '--search-seed', '75231',
        '--log-file', str(tmp_path/'converter.local.log'), '--fail-on-batch-failures'],
        cwd=ROOT, env=environment, capture_output=True, timeout=70)
    job = dict(description=DESCRIPTION)
    collect_result(tmp_path, job, completed.returncode)
    assert job['result'], completed.stdout.decode(errors='replace') + completed.stderr.decode(errors='replace')
    assert completed.returncode == 0 and job['pixel_quality']['passed'], job
    root = ET.fromstring((tmp_path/'result.svg').read_text(encoding='utf-8'))
    assert not root.findall('.//{http://www.w3.org/2000/svg}text')
    assert len(root.findall('.//{http://www.w3.org/2000/svg}circle')) == 1
