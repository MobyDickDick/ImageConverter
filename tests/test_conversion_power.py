"""Power requests must end with the work, including failure and cancellation."""
from types import SimpleNamespace

import pytest

from src.iCCModules import imageCompositeConverterPower as power


class Kernel:
    def __init__(self, *, handle=0x123456789, fail_set=None, fail_clear=False):
        self.handle = handle
        self.fail_set = fail_set
        self.fail_clear = fail_clear
        self.calls = []

    def PowerCreateRequest(self, pointer):
        context = pointer._obj
        assert context.version == 0 and context.flags == 1
        assert 'ImageConverter' in context.reason.simple
        self.calls.append(('create',))
        return self.handle

    def PowerSetRequest(self, handle, kind):
        self.calls.append(('set', handle, kind))
        return kind != self.fail_set

    def PowerClearRequest(self, handle, kind):
        self.calls.append(('clear', handle, kind))
        return not self.fail_clear

    def CloseHandle(self, handle):
        self.calls.append(('close', handle))
        return True


@pytest.fixture
def install(monkeypatch):
    monkeypatch.setattr(power, 'os', SimpleNamespace(name='nt'))
    monkeypatch.setattr(power.ctypes, 'get_last_error', lambda: 5, raising=False)
    monkeypatch.setattr(power.ctypes, 'WinError', lambda code: OSError(code, 'denied'), raising=False)

    def use(kernel):
        monkeypatch.setattr(power, '_load_kernel', lambda: kernel)
        return kernel
    return use


def test_system_and_execution_requests_are_scoped_without_display(install):
    kernel = install(Kernel())
    events = []
    with power.conversion_awake(event_fn=lambda phase, **data: events.append((phase, data))):
        assert kernel.calls == [('create',), ('set', kernel.handle, 1), ('set', kernel.handle, 3)]
    assert kernel.calls[-3:] == [('clear', kernel.handle, 3), ('clear', kernel.handle, 1),
                                 ('close', kernel.handle)]
    assert [data['status'] for _, data in events] == ['acquired', 'released']
    assert events[0][1]['display_required'] is False


@pytest.mark.parametrize('error', [ValueError, KeyboardInterrupt, SystemExit])
def test_cancellation_and_errors_release_handle_without_masking_error(install, error):
    kernel = install(Kernel())
    with pytest.raises(error):
        with power.conversion_awake():
            raise error('cancelled')
    assert kernel.calls[-1] == ('close', kernel.handle)
    assert len([call for call in kernel.calls if call[0] == 'clear']) == 2


@pytest.mark.parametrize('kind', [1, 3])
def test_partial_acquisition_is_cleaned_before_unprotected_work(install, kind):
    kernel = install(Kernel(fail_set=kind))
    events = []
    with power.conversion_awake(event_fn=lambda _, **data: events.append(data)):
        assert kernel.calls[-1] == ('close', kernel.handle)
        assert events[-1]['status'] == 'unavailable'
    assert len([call for call in kernel.calls if call[0] == 'close']) == 1
    assert [call[2] for call in kernel.calls if call[0] == 'clear'] == ([1] if kind == 3 else [])


@pytest.mark.parametrize('handle', [None, power.ctypes.c_void_p(-1).value])
def test_create_failure_never_closes_invalid_handle(install, handle):
    kernel = install(Kernel(handle=handle))
    with power.conversion_awake():
        pass
    assert kernel.calls == [('create',)]


def test_clear_failure_still_closes_handle_and_retains_body_error(install):
    kernel = install(Kernel(fail_clear=True))
    events = []
    with pytest.raises(ValueError, match='body'):
        with power.conversion_awake(event_fn=lambda _, **data: events.append(data)):
            raise ValueError('body')
    assert kernel.calls[-1] == ('close', kernel.handle)
    assert events[-1]['status'] == 'release_failed'
    assert events[-1]['cleanup_errors'] == [5, 5]


def test_nested_requests_do_not_release_each_other(install):
    kernel = install(Kernel())
    with power.conversion_awake():
        with power.conversion_awake():
            assert len([c for c in kernel.calls if c[0] == 'create']) == 2
        assert len([c for c in kernel.calls if c[0] == 'close']) == 1
    assert len([c for c in kernel.calls if c[0] == 'close']) == 2


def test_other_platforms_do_not_load_windows_api(monkeypatch):
    monkeypatch.setattr(power, 'os', SimpleNamespace(name='posix'))
    monkeypatch.setattr(power, '_load_kernel', lambda: pytest.fail('Windows API loaded'))
    events = []
    with power.conversion_awake(event_fn=lambda _, **data: events.append(data)):
        pass
    assert events == [dict(status='unsupported', platform='posix')]


def test_acquisition_diagnostic_failure_still_releases_request(install):
    kernel = install(Kernel())
    def diagnostic(*args, **kwargs):
        if kwargs['status'] == 'acquired':
            raise ValueError('diagnostic')
    with pytest.raises(ValueError, match='diagnostic'):
        with power.conversion_awake(event_fn=diagnostic):
            pytest.fail('body should not run')
    assert kernel.calls[-1] == ('close', kernel.handle)


def test_range_entry_point_releases_on_input_error(install, tmp_path):
    from src import imageCompositeConverter as app
    kernel = install(Kernel())
    # Exercise the public API and the synchronized legacy range function.
    (tmp_path/'out').write_text('blocked output directory', encoding='utf-8')
    with pytest.raises(OSError):
        app.convertRange(str(tmp_path), 'unused', 1, output_root=str(tmp_path/'out'))
    assert kernel.calls[-1] == ('close', kernel.handle)
