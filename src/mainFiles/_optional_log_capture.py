from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _optional_log_capture(log_path: str):
    """Duplicate stdout/stderr into ``log_path`` if configured."""
    if not log_path:
        yield
        return

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as logfile:
        tee_stdout = _TeeTextIO(sys.stdout, logfile)
        tee_stderr = _TeeTextIO(sys.stderr, logfile)
        with contextlib.redirect_stdout(tee_stdout), contextlib.redirect_stderr(tee_stderr):
            print(f"[INFO] Schreibe Konsolen-Output nach: {path}")
            yield
