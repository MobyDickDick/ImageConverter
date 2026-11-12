"""Process-owned Windows power requests, scoped to active conversion work.

No display request, power-plan changes, input simulation or background service.
Windows policy and explicit user sleep still take precedence.
"""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
import os


def _load_kernel():
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.PowerCreateRequest.argtypes = [ctypes.c_void_p]
    kernel.PowerCreateRequest.restype = wintypes.HANDLE
    for name in ('PowerSetRequest', 'PowerClearRequest'):
        function = getattr(kernel, name)
        function.argtypes = [wintypes.HANDLE, ctypes.c_int]
        function.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return kernel


class _WindowsPowerRequest:
    def __init__(self):
        self.kernel = _load_kernel()
        self.handle = None
        self.active = []

    def acquire(self):
        from ctypes import wintypes

        class Detailed(ctypes.Structure):
            _fields_ = [('module', wintypes.HMODULE), ('reason_id', wintypes.ULONG),
                        ('count', wintypes.ULONG), ('strings', ctypes.POINTER(wintypes.LPWSTR))]

        class Reason(ctypes.Union):
            _fields_ = [('detailed', Detailed), ('simple', wintypes.LPWSTR)]

        class Context(ctypes.Structure):
            _fields_ = [('version', wintypes.ULONG), ('flags', wintypes.DWORD), ('reason', Reason)]

        context = Context(0, 1, Reason(simple='ImageConverter: aktive Bildkonvertierung'))
        handle = self.kernel.PowerCreateRequest(ctypes.byref(context))
        if not handle or handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        self.handle = handle
        # SYSTEM prevents idle sleep; EXECUTION also covers process suspension
        # on Modern Standby. Neither requests that the display remain on.
        for request_type in (1, 3):
            if not self.kernel.PowerSetRequest(self.handle, request_type):
                raise ctypes.WinError(ctypes.get_last_error())
            self.active.append(request_type)

    def close(self):
        errors = []
        if self.handle is not None:
            try:
                for request_type in reversed(self.active):
                    if not self.kernel.PowerClearRequest(self.handle, request_type):
                        errors.append(ctypes.get_last_error())
            finally:
                if not self.kernel.CloseHandle(self.handle):
                    errors.append(ctypes.get_last_error())
                self.handle = None
                self.active.clear()
        return errors


@contextmanager
def conversion_awake(*, event_fn=None):
    """Keep only active work awake; failures are visible, never conversion errors.

    Each invocation owns its handle, including nested/concurrent invocations.
    The OS also closes it if the owning process is terminated.
    """
    def emit(status, **details):
        record = dict(status=status, platform=os.name, **details)
        if event_fn is not None:
            event_fn('power_request', **record)
        elif status != 'unsupported':
            print(f'[POWER] {record}', flush=True)

    request = None
    acquired = False
    try:
        if os.name == 'nt':
            try:
                request = _WindowsPowerRequest()
                request.acquire()
                acquired = True
            except (OSError, AttributeError) as exc:
                # Release partial acquisition before doing unprotected work.
                errors = request.close() if request is not None else []
                emit('unavailable', error=str(exc), cleanup_errors=errors)
            else:
                emit('acquired', request_types=['system', 'execution'], display_required=False)
        else:
            emit('unsupported')
        yield
    finally:
        if request is not None:
            errors = request.close()
            if acquired:
                emit('released' if not errors else 'release_failed', cleanup_errors=errors)
