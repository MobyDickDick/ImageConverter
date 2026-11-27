import sys
import threading
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "trace.log"

call_counts = defaultdict(int)
active_frames = {}
file_cache = {}

_log = None
_lock = threading.RLock()


def project_file(filename):
    if filename not in file_cache:
        try:
            path = Path(filename).resolve()
            relative = path.relative_to(ROOT)

            excluded = {
                ".venv", "venv", ".git",
                "site-packages", "__pycache__"
            }

            if (
                excluded.intersection(relative.parts)
                or path == Path(__file__).resolve()
            ):
                relative = None

            file_cache[filename] = relative

        except (ValueError, OSError):
            file_cache[filename] = None

    return file_cache[filename]


def trace_function(frame, event, arg):
    if event not in ("call", "return"):
        return

    filename = project_file(frame.f_code.co_filename)

    if filename is None:
        return

    name = getattr(frame.f_code, "co_qualname", frame.f_code.co_name)
    line = frame.f_code.co_firstlineno
    key = (str(filename), name, line)
    frame_id = id(frame)

    with _lock:
        if _log is None:
            return

        if event == "call":
            call_counts[key] += 1
            count = call_counts[key]

            depth = 0
            parent = frame.f_back

            while parent is not None:
                if id(parent) in active_frames:
                    depth += 1
                parent = parent.f_back

            active_frames[frame_id] = (count, depth)
            symbol = ">>>"

        else:
            entry = active_frames.pop(frame_id, None)

            if entry is None:
                return

            count, depth = entry
            symbol = "<<<"

        indent = "  " * depth

        _log.write(
            f"{indent}{symbol} {name}() #{count} "
            f"[{filename}:{line}] "
            f"[thread={threading.get_ident()}]\n"
        )
        _log.flush()


def start():
    global _log

    if _log is not None:
        return

    call_counts.clear()
    active_frames.clear()

    _log = open(
        LOG_FILE, "w", encoding="utf-8"
    )

    threading.setprofile(trace_function)
    sys.setprofile(trace_function)


def stop():
    global _log

    sys.setprofile(None)
    threading.setprofile(None)

    with _lock:
        if _log is not None:
            _log.close()
            _log = None


def current_call():
    frame = sys._getframe(1)

    with _lock:
        return active_frames.get(id(frame), (0, 0))[0]
