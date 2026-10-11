"""Bounded, reusable renderer processes for supervised catalog conversion."""
from __future__ import annotations

import atexit
import math
import multiprocessing
import sys
import threading
import time


def _render_worker(connection, max_requests):
    # MuPDF runs only on this process's main thread. No document objects cross
    # the pipe, and periodic retirement bounds accumulated native state.
    import cv2
    import fitz
    import numpy as np
    from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess

    try:
        for _ in range(max_requests):
            svg, width, height = connection.recv()
            try:
                raster = render_svg_to_numpy_inprocess(svg, width, height,
                    fitz_module=fitz, np_module=np, cv2_module=cv2)
                response = None if raster is None else (raster.shape, raster.tobytes())
            except Exception:
                response = None
            connection.send(response)
    except (EOFError, BrokenPipeError):
        pass
    finally:
        connection.close()


class RenderWorker:
    """Serialize requests, recycle native state and never render in the caller."""

    def __init__(self, max_requests=64, worker_fn=_render_worker):
        if max_requests < 1:
            raise ValueError('max_requests must be positive')
        self.max_requests = max_requests
        self.worker_fn = worker_fn
        self.process = None
        self.connection = None
        self.requests = 0
        self.lock = threading.RLock()

    def close(self):
        with self.lock:
            if self.connection is not None:
                self.connection.close()
                self.connection = None
            if self.process is not None:
                if self.process.is_alive():
                    self.process.terminate()
                self.process.join(timeout=1)
                if self.process.is_alive():
                    self.process.kill()
                    self.process.join(timeout=1)
                self.process.close()
                self.process = None
            self.requests = 0

    def _start(self):
        self.close()
        context = multiprocessing.get_context('spawn')
        parent, child = context.Pipe()
        self.process = context.Process(target=self.worker_fn, args=(child, self.max_requests), daemon=True)
        try:
            self.process.start()
        except Exception:
            parent.close()
            child.close()
            self.process = None
            raise
        child.close()
        self.connection = parent

    def render(self, svg, width, height, *, np_module, timeout_sec, status_callback=None):
        if np_module is None or not math.isfinite(timeout_sec) or timeout_sec <= 0:
            return None
        deadline = time.monotonic() + timeout_sec
        with self.lock:
            for attempt in range(2):
                try:
                    if time.monotonic() >= deadline:
                        raise TimeoutError
                    if (self.process is None or not self.process.is_alive()
                            or self.requests >= self.max_requests):
                        self._start()
                    self.connection.send((svg, int(width), int(height)))
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not self.connection.poll(remaining):
                        raise TimeoutError
                    response = self.connection.recv()
                    self.requests += 1
                    if response is None:
                        if status_callback is not None:
                            status_callback('error')
                        return None
                    shape, raw = response
                    if tuple(shape) != (int(height), int(width), 3):
                        raise ValueError('renderer returned wrong dimensions')
                    return np_module.frombuffer(raw, dtype=np_module.uint8).reshape(shape).copy()
                except TimeoutError:
                    self.close()
                    if status_callback is not None:
                        status_callback('timeout')
                    print('[ICC_RENDER_TIMEOUT] isolated render worker exceeded request budget',
                          file=sys.stderr, flush=True)
                    return None
                except (EOFError, BrokenPipeError, OSError):
                    if self.process is not None:
                        self.process.join(timeout=.1)
                    code = self.process.exitcode if self.process is not None else None
                    self.close()
                    if status_callback is not None:
                        status_callback('error')
                    print(f'[ICC_RENDER_WORKER_ERROR] renderer exited with code {code}; '
                          f'fresh-process retry={attempt == 0}', file=sys.stderr, flush=True)
                    # One fresh retry can recover accumulated native state.
                    # Deterministically invalid SVGs still fail visibly.
                except Exception:
                    self.close()
                    if status_callback is not None:
                        status_callback('error')
                    return None
        return None


_WORKER = RenderWorker()
atexit.register(_WORKER.close)


def render_svg_to_numpy_via_worker(svg, width, height, *, np_module, timeout_sec, status_callback=None):
    return _WORKER.render(svg, width, height, np_module=np_module,
                          timeout_sec=timeout_sec, status_callback=status_callback)
