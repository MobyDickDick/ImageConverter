"""Generated test data is disposable; seeds and genuine sources are not."""
import json
from pathlib import Path
import subprocess

import pytest

from tools import cleanup_test_data as cleanup
from tools import run_seeded_scene_check as checks
from tools import evaluate_layered_scene


def test_cleanup_preserves_nested_seeds_and_does_not_touch_sources(tmp_path):
    work = tmp_path/'.tmp/run/nested'
    work.mkdir(parents=True)
    (work/'report.json').write_text(json.dumps({'seed': 57, 'attempts': [{'search_seed': 17}]}))
    (work/'trial-settings.json').write_text('{"random_seed": 812}')
    (work/'replays.jsonl').write_text('{"seed": 923}\n{"search_seed": 17}\n')
    (work/'powershell.json').write_text('{"seed": 114}\n{"seed": 115}', encoding='utf-16')
    (work/'image.png').write_bytes(b'disposable')
    source = tmp_path/'artifacts/images_to_convert/source.png'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'original')
    archive = tmp_path/'artifacts/satisfactory_conversions/accepted.svg'
    archive.parent.mkdir(parents=True)
    archive.write_text('accepted')
    audit = tmp_path/'artifacts/evaluation/plan_b_ci_failure_audit_2026-10-10/failure_tasks.json'
    audit.parent.mkdir(parents=True)
    audit.write_text('{"tasks": []}')
    cleanup.clean(tmp_path)
    assert (work/'image.png').exists()
    assert not (tmp_path/'config/preserved_test_seeds.json').exists()
    cleanup.clean(tmp_path, apply=True)
    assert not (tmp_path/'.tmp').exists()
    seeds = json.loads((tmp_path/'config/preserved_test_seeds.json').read_text())
    assert seeds['.tmp/run/nested/report.json'] == {'seed': 57, 'attempts[0].search_seed': 17}
    assert seeds['.tmp/run/nested/trial-settings.json'] == {'random_seed': 812}
    assert seeds['.tmp/run/nested/replays.jsonl'] == {'[0].seed': 923, '[1].search_seed': 17}
    assert seeds['.tmp/run/nested/powershell.json'] == {'[0].seed': 114, '[1].seed': 115}
    assert source.read_bytes() == b'original'
    assert archive.read_text() == 'accepted'
    assert audit.read_text() == '{"tasks": []}'
    cleanup.clean(tmp_path, apply=True)
    assert json.loads((tmp_path/'config/preserved_test_seeds.json').read_text()) == seeds


def test_cleanup_refuses_a_workspace_link_to_outside_before_any_removal(tmp_path):
    project, outside = tmp_path/'project', tmp_path/'outside'
    project.mkdir()
    outside.mkdir()
    sentinel = outside/'important.txt'
    sentinel.write_text('keep')
    try:
        (project/'.tmp').symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip('Creating symlinks requires Windows developer privileges')
    with pytest.raises(ValueError, match='escapes project'):
        cleanup.clean(project, apply=True)
    assert sentinel.read_text() == 'keep'


def test_incomplete_metadata_preserves_its_entire_run_but_other_runs_are_cleaned(tmp_path):
    broken, good = tmp_path/'.tmp/broken', tmp_path/'.tmp/good'
    broken.mkdir(parents=True)
    good.mkdir()
    (broken/'report.json').write_text('{"seed": 17,')
    (broken/'source.png').write_bytes(b'keep until seed metadata is readable')
    (good/'report.json').write_text('{"seed": 19}')
    result = cleanup.clean(tmp_path, apply=True)
    assert (broken/'source.png').is_file()
    assert not good.exists()
    assert result['skipped'][0]['target'] == '.tmp/broken'
    seeds = json.loads((tmp_path/'config/preserved_test_seeds.json').read_text())
    assert seeds['.tmp/good/report.json'] == {'seed': 19}


@pytest.mark.parametrize('has_rg', [True, False])
def test_cleanup_protects_checkouts_and_runs_changed_after_inventory(tmp_path, monkeypatch, has_rg):
    if not has_rg:
        run_command = cleanup.subprocess.run

        def without_rg(command, **kwargs):
            if command[0] == 'rg':
                raise FileNotFoundError('rg is not installed')
            return run_command(command, **kwargs)

        monkeypatch.setattr(cleanup.shutil, 'which', lambda name: None)
        monkeypatch.setattr(cleanup.subprocess, 'run', without_rg)
    checkout, run = tmp_path/'.tmp/checkout', tmp_path/'.tmp/run'
    checkout.mkdir(parents=True)
    run.mkdir()
    (checkout/'.git').write_text('gitdir: protected')
    (checkout/'uncommitted.py').write_text('keep')
    (run/'report.json').write_text('{"seed": 17}')
    inventory = tmp_path/'inventory.json'
    cleanup.clean(tmp_path, inventory_path=inventory)
    (run/'new.png').write_bytes(b'added after review')
    result = cleanup.clean(tmp_path, apply=True, from_inventory=inventory)
    assert (checkout/'uncommitted.py').read_text() == 'keep'
    assert (run/'new.png').exists()
    assert any('Protected Git' in row['reason'] for row in result['skipped'])
    assert any('Files changed' in row['reason'] for row in result['skipped'])


def test_inventory_cleanup_without_rg_removes_reviewed_hidden_files_and_saves_seeds(tmp_path, monkeypatch):
    monkeypatch.setattr(cleanup.shutil, 'which', lambda name: None)
    run = tmp_path/'.tmp/run/.hidden'
    run.mkdir(parents=True)
    (run/'replays.jsonl').write_text('{"seed": 91}\n')
    (run/'image.png').write_bytes(b'generated')
    inventory = tmp_path/'inventory.json'
    cleanup.clean(tmp_path, inventory_path=inventory)
    result = cleanup.clean(tmp_path, apply=True, from_inventory=inventory)
    assert result['paths'] == 1 and result['skipped'] == []
    assert not (tmp_path/'.tmp').exists()
    seeds = json.loads((tmp_path/'config/preserved_test_seeds.json').read_text())
    assert seeds['.tmp/run/.hidden/replays.jsonl'] == {'seed': 91}


@pytest.mark.parametrize('failure', [None, 'prepare', 'evaluate', 'interrupt'])
def test_scene_check_removes_owned_data_on_every_exit_and_saves_seed_first(tmp_path, monkeypatch, failure):
    (tmp_path/'tools').mkdir()
    (tmp_path/'tools/evaluate_example.py').touch()
    monkeypatch.setattr(checks, 'ROOT', tmp_path)
    paths = []

    def prepare(command, **kwargs):
        work = Path(command[command.index('--prepare')+1])
        paths.append(work.parent)
        assert (tmp_path/'config/test_run_seeds.jsonl').is_file()
        work.mkdir()
        (work/'image.png').write_bytes(b'generated')
        if failure == 'prepare':
            raise subprocess.CalledProcessError(1, command)

    def evaluate(inputs, output, **kwargs):
        output.mkdir()
        (output/'output.svg').write_text('generated')
        if failure == 'evaluate':
            raise ValueError('Independent acceptance failed')
        if failure == 'interrupt':
            raise KeyboardInterrupt
        return {'accepted': 12, 'completed': 12}

    monkeypatch.setattr(checks.subprocess, 'run', prepare)
    monkeypatch.setattr(evaluate_layered_scene, 'evaluate_cases', evaluate)
    monkeypatch.setenv('ICC_SEARCH_SEED', '17')
    monkeypatch.setenv('IMAGE_CONVERTER_ISOLATE_SVG_RENDER', '0')
    if failure:
        with pytest.raises((subprocess.CalledProcessError, ValueError, KeyboardInterrupt)):
            checks.run('evaluate_example', 8123)
    else:
        assert checks.run('evaluate_example', 8123) == {'accepted': 12, 'completed': 12}
    assert paths and all(not p.exists() for p in paths)
    recipe = json.loads((tmp_path/'config/test_run_seeds.jsonl').read_text())
    assert recipe['seed'] == 8123 and recipe['search_seed'] == 17


@pytest.mark.parametrize('options', [('--output', 'elsewhere'), ('--prepare', 'elsewhere'), ('--inputs=elsewhere',)])
def test_scene_check_cannot_override_its_temporary_paths(tmp_path, options):
    with pytest.raises(ValueError, match='Unsupported generation'):
        checks.run('evaluate_overlap_composition', 17, options, journal=tmp_path/'seeds.jsonl')
    assert not (tmp_path/'seeds.jsonl').exists()
