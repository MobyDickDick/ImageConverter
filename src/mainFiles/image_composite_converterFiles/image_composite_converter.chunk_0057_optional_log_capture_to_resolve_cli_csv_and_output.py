""" End move to File mainFiles/parse_args.py """


class _TeeTextIO(io.TextIOBase):
    """Mirror text writes to multiple streams."""

    def __init__(self, *streams: io.TextIOBase):
        self._streams = streams

    def write(self, s: str) -> int:
        for stream in self._streams:
            stream.write(s)
        return len(s)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


""" Start move to File mainFiles/_optional_log_capture.py
import src
"""
@contextlib.contextmanager
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
""" End move to File mainFiles/_optional_log_capture.py """


""" Start move to File mainFiles/_resolve_cli_csv_and_outputFiles/_auto_detect_csv_path.py
import src
"""
def _auto_detect_csv_path(folder_path: str) -> str | None:
    """Best-effort table lookup for CLI compatibility mode.

    Priority:
    1) CSV/TSV/XML files directly inside ``folder_path``
    2) CSV/TSV/XML files in the parent directory of ``folder_path``
    """
    candidates: list[str] = []
    roots = [folder_path, os.path.dirname(folder_path)]
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            lower = name.lower()
            if lower.endswith(".csv") or lower.endswith(".tsv") or lower.endswith(".xml"):
                candidates.append(os.path.join(root, name))
        if candidates:
            break

    if not candidates:
        return None

    # Prefer obvious mapping files if several exist.
    preferred = [
        p
        for p in candidates
        if any(tag in os.path.basename(p).lower() for tag in ("reference", "roundtrip", "export", "mapping"))
    ]
    return preferred[0] if preferred else candidates[0]
""" End move to File mainFiles/_resolve_cli_csv_and_outputFiles/_auto_detect_csv_path.py """


""" Start move to File mainFiles/_resolve_cli_csv_and_output.py
import src
"""
def _resolve_cli_csv_and_output(args: argparse.Namespace) -> tuple[str, str | None]:
    """Resolve effective table path and output directory from mixed CLI styles."""
    csv_path = args.csv_path
    output_dir = args.output_dir
    if args.csv_or_output:
        c = str(args.csv_or_output)
        looks_like_csv = c.lower().endswith(".csv") or c.lower().endswith(".tsv") or c.lower().endswith(".xml")
        if csv_path is None and looks_like_csv:
            csv_path = c
        elif output_dir is None and not looks_like_csv:
            output_dir = c
        elif csv_path is None:
            csv_path = c

    if csv_path is None:
        csv_path = _auto_detect_csv_path(args.folder_path) or ""
    elif str(csv_path).lower().endswith(".xml"):
        csv_path = _resolve_description_xml_path(csv_path) or csv_path

    return csv_path, output_dir
""" End move to File mainFiles/_resolve_cli_csv_and_output.py """
