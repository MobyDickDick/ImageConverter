from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class ImageBackend(Protocol):
    """Small backend contract for image loading primitives."""

    name: str

    def is_available(self) -> bool:
        """Return whether backend can be used in current runtime."""

    def load_grayscale(self, path: Path) -> list[list[int]]:
        """Load image and return grayscale matrix (0..255)."""


@dataclass(frozen=True)
class OpenCvImageBackend:
    """Backend that depends on numpy + cv2 style stack."""

    np_module: object | None
    cv2_module: object | None
    name: str = "opencv"

    def is_available(self) -> bool:
        return self.np_module is not None and self.cv2_module is not None

    def load_grayscale(self, path: Path) -> list[list[int]]:
        if not self.is_available():
            raise RuntimeError("OpenCV backend is not available.")
        cv2 = self.cv2_module
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"Could not read image via OpenCV: {path}")
        return [[int(value) for value in row] for row in image.tolist()]


@dataclass(frozen=True)
class PurePythonImageBackend:
    """Fallback backend that only needs PIL import hook."""

    import_with_vendored_fallback_fn: object
    name: str = "pure_python"

    def is_available(self) -> bool:
        try:
            self.import_with_vendored_fallback_fn("PIL.Image")
            return True
        except Exception:
            return False

    def load_grayscale(self, path: Path) -> list[list[int]]:
        image_module = self.import_with_vendored_fallback_fn("PIL.Image")
        gray = image_module.open(path).convert("L")
        w, h = gray.size
        px = gray.load()
        return [[int(px[x, y]) for x in range(w)] for y in range(h)]


def pickImageBackendImpl(*, np_module, cv2_module, import_with_vendored_fallback_fn) -> ImageBackend:
    """Prefer OpenCV backend and fall back to pure-python backend."""

    cv_backend = OpenCvImageBackend(np_module=np_module, cv2_module=cv2_module)
    if cv_backend.is_available():
        return cv_backend
    return PurePythonImageBackend(
        import_with_vendored_fallback_fn=import_with_vendored_fallback_fn,
    )
