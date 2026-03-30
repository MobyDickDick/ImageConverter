AC08_ADAPTIVE_LOCK_PROFILES: dict[str, dict[str, float | bool]] = {
    # Known AC08 outlier families from the improvement plan. Profiles only relax
    # tightly bounded locks after validation stagnates or when the residual
    # error stays clearly above the "good enough" range.
    "AC0882": {
        "radius_floor_ratio": 0.84,
        "arm_min_ratio": 0.68,
        "color_corridor": 10.0,
    },
    "AC0837": {
        "radius_floor_ratio": 0.86,
        "arm_min_ratio": 0.70,
        "color_corridor": 10.0,
    },
    "AC0839": {
        "radius_floor_ratio": 0.86,
        "arm_min_ratio": 0.70,
        "text_scale_delta": 0.10,
        "color_corridor": 10.0,
    },
    "AC0820": {
        "radius_floor_ratio": 0.88,
        "text_scale_delta": 0.10,
        "color_corridor": 8.0,
    },
    "AC0831": {
        "radius_floor_ratio": 0.87,
        "stem_min_ratio": 0.58,
        "text_scale_delta": 0.10,
        "color_corridor": 10.0,
    },
}


@dataclass(frozen=True)
class RuntimeModules:
    """Dependency bundle passed explicitly to extracted helper functions."""

    cv2_module: object | None
    np_module: object | None


def _runtime_modules() -> RuntimeModules:
    """Resolve runtime image dependencies in one place for explicit parameter flow."""
    return RuntimeModules(cv2_module=cv2, np_module=np)


def detect_relevant_regions(img, *, runtime_modules: RuntimeModules) -> list[dict[str, object]]:
    return detect_relevant_regions_impl(
        img,
        cv2_module=runtime_modules.cv2_module,
        np_module=runtime_modules.np_module,
    )


def annotate_image_regions(img, regions: list[dict[str, object]], *, runtime_modules: RuntimeModules):
    return annotate_image_regions_impl(img, regions, cv2_module=runtime_modules.cv2_module)


""" Start move to File mainFiles/analyze_range.py
import src
"""
def analyze_range(
    folder_path: str,
    output_root: str | None = None,
    start_ref: str = "",
    end_ref: str = "ZZZZZZ",
    *,
    runtime_modules: RuntimeModules | None = None,
) -> str:
    modules = runtime_modules or _runtime_modules()

    def _detect_regions(img):
        return detect_relevant_regions(img, runtime_modules=modules)

    def _annotate_regions(img, regions):
        return annotate_image_regions(img, regions, runtime_modules=modules)

    return analyze_range_impl(
        folder_path=folder_path,
        output_root=output_root,
        start_ref=start_ref,
        end_ref=end_ref,
        default_output_root_fn=_default_converted_symbols_root,
        in_requested_range_fn=_in_requested_range,
        detect_regions_fn=_detect_regions,
        annotate_regions_fn=_annotate_regions,
        cv2_module=modules.cv2_module,
        np_module=modules.np_module,
    )
""" End move to File mainFiles/analyze_range.py """


# Load numpy before cv2: OpenCV's Python bindings import numpy at module-import
# time and can fail permanently for this process if cv2 is attempted first while
# numpy is available only via repo-vendored site-packages.
np = _load_optional_module("numpy")
cv2 = _load_optional_module("cv2")
fitz = _load_optional_module("fitz")  # PyMuPDF for native SVG rendering
