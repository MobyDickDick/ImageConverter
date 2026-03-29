def _load_optional_module(module_name: str):
    """Import optional dependencies, including repo-vendored site-packages."""
    attempted_paths: list[Path] = []
    try:
        return importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exercised only in dependency-missing envs
        last_exc: BaseException = exc
        _clear_partial_module_import(module_name)

    for site_packages in _vendored_site_packages_dirs():
        attempted_paths.append(site_packages)
        path_str = str(site_packages)
        added = False
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            added = True
        try:
            return importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - exercised only in dependency-missing envs
            last_exc = exc
            _clear_partial_module_import(module_name)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(path_str)

    OPTIONAL_DEPENDENCY_ERRORS[module_name] = _describe_optional_dependency_error(module_name, last_exc, attempted_paths)
    return None


def _import_with_vendored_fallback(module_name: str):
    """Import a module, retrying with repo-vendored site-packages on sys.path."""
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        last_exc: BaseException = exc
        _clear_partial_module_import(module_name)

    for site_packages in _vendored_site_packages_dirs():
        path_str = str(site_packages)
        added = False
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            added = True
        try:
            return importlib.import_module(module_name)
        except Exception as exc:
            last_exc = exc
            _clear_partial_module_import(module_name)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(path_str)

    raise last_exc


# Load numpy before cv2: OpenCV's Python bindings import numpy at module-import
# time and can fail permanently for this process if cv2 is attempted first while
# numpy is available only via repo-vendored site-packages.
np = _load_optional_module("numpy")
cv2 = _load_optional_module("cv2")
fitz = _load_optional_module("fitz")  # PyMuPDF for native SVG rendering



def _clip(value, low, high):
    """Clip scalar/array values without hard-requiring numpy at runtime."""
    if np is not None:
        return np.clip(value, low, high)
    if isinstance(value, (int, float)):
        return Action._clip_scalar(float(value), float(low), float(high))
    raise RuntimeError("numpy is required for non-scalar clip operations")





@dataclass(frozen=True)
class RGBWert:
    """RGB value constrained to Nummer(256) semantics (0..255)."""

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        for channel_name, channel in (("r", self.r), ("g", self.g), ("b", self.b)):
            if not isinstance(channel, int):
                raise TypeError(f"RGB channel '{channel_name}' must be an integer.")
            if channel < 0 or channel >= 256:
                raise ValueError(f"RGB channel '{channel_name}' must satisfy 0 <= x < 256.")

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


@dataclass(frozen=True)
class Punkt:
    x: float
