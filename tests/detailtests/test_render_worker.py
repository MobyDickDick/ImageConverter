"""Exercise real process death, timeout and renderer-state retirement."""
import os
import time
from pathlib import Path

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterRenderWorker import RenderWorker
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess


def _controlled_worker(connection, max_requests):
    for _ in range(max_requests):
        command, width, height = connection.recv()
        if command == 'crash':
            os._exit(23)
        if command.startswith('recover:'):
            marker = Path(command.partition(':')[2])
            if not marker.exists():
                marker.write_text('first process crashed', encoding='utf-8')
                os._exit(23)
        if command == 'hang':
            time.sleep(60)
        if command == 'invalid':
            connection.send(None)
        else:
            connection.send(((height, width, 3), bytes([17]) * height * width * 3))
    connection.close()


@pytest.fixture
def worker():
    renderer = RenderWorker(max_requests=2, worker_fn=_controlled_worker)
    yield renderer
    renderer.close()


def _render(worker, command, statuses=None, timeout=10):
    return worker.render(command, 4, 3, np_module=np, timeout_sec=timeout,
                         status_callback=None if statuses is None else statuses.append)


def test_native_process_exit_is_bounded_and_next_request_recovers(worker, capsys):
    statuses = []
    assert _render(worker, 'crash', statuses) is None
    assert statuses == ['error', 'error']
    assert worker.process is None
    assert 'renderer exited with code 23' in capsys.readouterr().err
    assert np.all(_render(worker, 'ok') == 17)


def test_fresh_process_retry_recovers_a_transient_crash(worker, tmp_path):
    statuses = []
    image = _render(worker, f'recover:{tmp_path / "crashed"}', statuses)
    assert image.shape == (3, 4, 3)
    assert np.all(image == 17)
    assert statuses == ['error']


def test_timeout_terminates_worker_and_next_request_recovers(worker):
    _render(worker, 'ok')  # Do not measure interpreter startup as a hung render.
    statuses = []
    started = time.monotonic()
    assert _render(worker, 'hang', statuses, timeout=.1) is None
    assert time.monotonic() - started < 3
    assert worker.process is None
    assert statuses == ['timeout']
    assert np.all(_render(worker, 'ok') == 17)


def test_worker_retires_after_configured_request_count(worker):
    first = _render(worker, 'ok')
    process = worker.process
    first[:] = 99
    assert np.all(_render(worker, 'ok') == 17)
    assert worker.process is process
    assert np.all(_render(worker, 'ok') == 17)
    assert worker.process is not process
    assert worker.requests == 1


def test_invalid_render_reports_error_without_poisoning_next_request(worker):
    statuses = []
    assert _render(worker, 'invalid', statuses) is None
    assert statuses == ['error']
    assert np.all(_render(worker, 'ok') == 17)


def test_isolated_real_render_matches_inprocess_pixels():
    import cv2
    import fitz
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="30">'
           '<rect width="40" height="30" fill="white"/>'
           '<circle cx="20" cy="15" r="12" fill="#abcdef"/>'
           '<text x="10" y="20" font-size="12">VOC</text></svg>')
    expected = render_svg_to_numpy_inprocess(svg, 40, 30,
        np_module=np, cv2_module=cv2, fitz_module=fitz)
    assert expected is not None
    renderer = RenderWorker(max_requests=2)
    try:
        for _ in range(3):  # Check pixels across retirement as well.
            actual = renderer.render(svg, 40, 30, np_module=np, timeout_sec=20)
            np.testing.assert_array_equal(actual, expected)
    finally:
        renderer.close()
