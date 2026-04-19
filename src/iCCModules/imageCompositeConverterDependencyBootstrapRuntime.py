"""Runtime helper for bootstrapping required image dependencies."""

from __future__ import annotations


def bootstrapRequiredImageDependenciesForRuntimeImpl(
    *,
    missing_dependencies_fn,
    bootstrap_dependencies_fn,
    cv2_module_name: str = "cv2",
    np_module_name: str = "numpy",
    import_module_fn,
    set_modules_fn,
) -> list[str]:
    """Install missing image dependencies and update runtime module globals."""
    missing = missing_dependencies_fn()

    loaded_cv2 = None
    loaded_np = None

    def _load_cv2_module():
        nonlocal loaded_cv2
        loaded_cv2 = import_module_fn(cv2_module_name)
        return loaded_cv2

    def _load_np_module():
        nonlocal loaded_np
        loaded_np = import_module_fn(np_module_name)
        return loaded_np

    def _set_modules(*, cv2_module, np_module) -> None:
        set_modules_fn(cv2_module=cv2_module, np_module=np_module)

    return bootstrap_dependencies_fn(
        missing=missing,
        load_cv2_fn=_load_cv2_module,
        load_np_fn=_load_np_module,
        set_modules_fn=_set_modules,
    )
