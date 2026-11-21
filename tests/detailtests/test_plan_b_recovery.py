"""Plan-B workers preserve the first-stage result and never reconstruct again."""
import json
import time

import pytest

from tools import run_plan_b_variations as battery
from src import imageConverterRecovery as recovery
from src.iCCModules import imageCompositeConverterCli as cli


@pytest.mark.parametrize('deadline', [0, 5, 240])
def test_remaining_time_never_authorizes_second_stage(tmp_path, monkeypatch, deadline):
    target = tmp_path/'failed.svg'
    target.write_text('<svg><circle r="5"/></svg>')
    before = target.read_bytes()
    def forbidden(*args, **kwargs):
        pytest.fail('second-stage recovery was called')
    monkeypatch.setattr(recovery, 'recover', forbidden)
    assert not battery.recover_case_output(tmp_path, [], time.time()+deadline)
    assert target.read_bytes() == before
    assert not (tmp_path/'recovery').exists()


@pytest.mark.parametrize('first_stage_exit', [0, 1])
def test_audited_worker_returns_first_stage_outcome_without_recovery(tmp_path, monkeypatch, first_stage_exit):
    conversion = tmp_path/'conversion'
    conversion.mkdir()
    monkeypatch.setattr(cli, 'main', lambda args: first_stage_exit)
    monkeypatch.setattr(battery, 'recover_case_output', lambda *args: pytest.fail('second stage'))
    monkeypatch.setenv('ICC_PLAN_B_DEADLINE', str(time.time()+240))
    # Installing the process-wide audit hook is exercised by the existing
    # reference-access tests; keep this unit test's hook local.
    monkeypatch.setattr(battery.sys, 'addaudithook', lambda hook: None)
    assert battery.converter_worker([str(conversion)]) == first_stage_exit
    assert not (conversion/'recovery').exists()
    assert json.loads((tmp_path/'reference_access.json').read_text()) == {'blocked_svg_reads': []}
