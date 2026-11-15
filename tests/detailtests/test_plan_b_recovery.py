"""Shared recovery stays inside the audited worker and original time budget."""
import time
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools import run_plan_b_variations as battery
from src import imageConverterRecovery as recovery

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
       '<rect width="40" height="40" fill="white"/><circle cx="20" cy="20" r="12" fill="gray"/></svg>')


@pytest.fixture
def case(tmp_path):
    c = battery.make_original_case(SVG, 'Ein grauer Kreis auf weissem Hintergrund.')
    battery.write_cases([c], tmp_path)
    conversion = tmp_path/'original/conversion'
    target = conversion/'converted_svgs/original.svg'
    target.parent.mkdir(parents=True)
    target.write_text(SVG.replace('r="12"', 'r="3"'))
    args = [str(tmp_path/'original/input'), '--start', 'original',
            '--descriptions-path', str(tmp_path/'original/input/descriptions.xml'), '--search-seed', '42']
    return conversion, target, args


@pytest.mark.parametrize('improves', [True, False])
def test_failed_draft_recovers_from_only_pixels_wording_and_own_svg(case, monkeypatch, improves):
    conversion, target, args = case
    old = target.read_bytes()
    def recover(source, output, description, seconds, **kwargs):
        assert source == Path(args[0])/'original.png'
        assert description == 'Ein grauer Kreis auf weissem Hintergrund.'
        assert kwargs['candidate'] == target and kwargs['seed'] == 42
        assert 0 < seconds <= 5
        output.parent.mkdir(parents=True)
        output.write_text(SVG if improves else SVG.replace('cx="20"', 'cx="0"'))
        return dict(passed=improves)
    monkeypatch.setattr(recovery, 'recover', recover)
    assert battery.recover_case_output(conversion, args, time.time()+5) is improves
    assert target.read_text() == SVG if improves else target.read_bytes() == old


@pytest.mark.parametrize('accurate,remaining', [(True, 5), (False, -1)])
def test_good_result_or_exhausted_deadline_never_starts_recovery(case, monkeypatch, accurate, remaining):
    conversion, target, args = case
    if accurate:
        target.write_text(SVG)
    def forbidden(*args, **kwargs):
        pytest.fail('No recovery needed or no time remaining')
    monkeypatch.setattr(recovery, 'recover', forbidden)
    assert not battery.recover_case_output(conversion, args, time.time()+remaining)


def test_real_audited_worker_recovers_a_failed_first_stage(case):
    conversion, target, args = case
    # Substitute only the first CLI stage. Real native recovery, rendering,
    # assertions and the worker's reference-access audit remain in force.
    bootstrap = ('import sys; from src.iCCModules import imageCompositeConverterCli as cli; '
                 'cli.main=lambda args:0; from tools.run_plan_b_variations import converter_worker; '
                 'raise SystemExit(converter_worker(sys.argv[1:]))')
    environment = dict(os.environ, ICC_PLAN_B_DEADLINE=str(time.time()+8))
    environment.pop('PYTEST_CURRENT_TEST', None)
    completed = subprocess.run([sys.executable, '-c', bootstrap, str(conversion), *args],
                               cwd=battery.ROOT, env=environment, capture_output=True, timeout=12)
    assert completed.returncode == 0, completed.stderr.decode(errors='replace')[-2000:]
    assert (conversion/'recovery/original.json').is_file()
    access = json.loads((conversion.parent/'reference_access.json').read_text())
    assert not access['blocked_svg_reads']
    import cv2
    image = cv2.imread(str(Path(args[0])/'original.png'))
    assert battery.measure_quality(image, target.read_text())['satisfactory']
