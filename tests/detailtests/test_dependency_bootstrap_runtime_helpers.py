from __future__ import annotations

from src.iCCModules import imageCompositeConverterDependencyBootstrapRuntime as helpers


def test_bootstrap_required_image_dependencies_for_runtime_impl_installs_and_sets_modules() -> None:
    calls: dict[str, object] = {}

    def missing_dependencies_fn() -> list[str]:
        return ["opencv-python-headless", "numpy"]

    def bootstrap_dependencies_fn(**kwargs):
        calls["bootstrap"] = kwargs
        loaded_cv2 = kwargs["load_cv2_fn"]()
        loaded_np = kwargs["load_np_fn"]()
        kwargs["set_modules_fn"](cv2_module=loaded_cv2, np_module=loaded_np)
        return kwargs["missing"]

    imported: list[str] = []

    def import_module_fn(module_name: str):
        imported.append(module_name)
        return f"module:{module_name}"

    assigned: dict[str, object] = {}

    def set_modules_fn(*, cv2_module, np_module) -> None:
        assigned["cv2"] = cv2_module
        assigned["np"] = np_module

    result = helpers.bootstrapRequiredImageDependenciesForRuntimeImpl(
        missing_dependencies_fn=missing_dependencies_fn,
        bootstrap_dependencies_fn=bootstrap_dependencies_fn,
        import_module_fn=import_module_fn,
        set_modules_fn=set_modules_fn,
    )

    assert result == ["opencv-python-headless", "numpy"]
    assert calls["bootstrap"]["missing"] == ["opencv-python-headless", "numpy"]
    assert imported == ["cv2", "numpy"]
    assert assigned == {"cv2": "module:cv2", "np": "module:numpy"}


def test_bootstrap_required_image_dependencies_for_runtime_impl_uses_custom_module_names() -> None:
    imported: list[str] = []

    def bootstrap_dependencies_fn(**kwargs):
        kwargs["load_cv2_fn"]()
        return kwargs["missing"]

    result = helpers.bootstrapRequiredImageDependenciesForRuntimeImpl(
        missing_dependencies_fn=lambda: ["opencv-python-headless"],
        bootstrap_dependencies_fn=bootstrap_dependencies_fn,
        cv2_module_name="custom_cv2",
        np_module_name="custom_np",
        import_module_fn=lambda module_name: imported.append(module_name) or module_name,
        set_modules_fn=lambda **_: None,
    )

    assert result == ["opencv-python-headless"]
    assert imported == ["custom_cv2"]
