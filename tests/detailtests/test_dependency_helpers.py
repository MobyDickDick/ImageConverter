from __future__ import annotations

import subprocess

import pytest

from src.iCCModules import imageCompositeConverterDependencies as dependency_helpers


def test_missing_required_image_dependencies_impl() -> None:
    assert dependency_helpers.missingRequiredImageDependenciesImpl(cv2_module=None, np_module=None) == [
        "opencv-python-headless",
        "numpy",
    ]
    assert dependency_helpers.missingRequiredImageDependenciesImpl(cv2_module=object(), np_module=None) == ["numpy"]
    assert dependency_helpers.missingRequiredImageDependenciesImpl(cv2_module=object(), np_module=object()) == []


def test_bootstrap_required_image_dependencies_impl_runs_install_and_sets_modules() -> None:
    installed_commands: list[list[str]] = []
    assigned: dict[str, object | None] = {"cv2": None, "np": None}
    printed: list[str] = []

    def _run(cmd, check):
        assert check is True
        installed_commands.append(list(cmd))

    def _set_modules(*, cv2_module, np_module):
        assigned["cv2"] = cv2_module
        assigned["np"] = np_module

    loaded = dependency_helpers.bootstrapRequiredImageDependenciesImpl(
        missing=["opencv-python-headless", "numpy"],
        sys_executable="pythonX",
        run_fn=_run,
        print_fn=printed.append,
        load_cv2_fn=lambda: "cv2-module",
        load_np_fn=lambda: "np-module",
        set_modules_fn=_set_modules,
    )

    assert loaded == ["opencv-python-headless", "numpy"]
    assert installed_commands == [["pythonX", "-m", "pip", "install", "opencv-python-headless", "numpy"]]
    assert assigned == {"cv2": "cv2-module", "np": "np-module"}
    assert any("Fehlende Bild-Abhängigkeiten" in line for line in printed)
    assert any("Installiere via:" in line for line in printed)


def test_bootstrap_required_image_dependencies_impl_raises_runtime_error_on_pip_failure() -> None:
    def _run(*_args, **_kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=["pip", "install"])

    with pytest.raises(RuntimeError):
        dependency_helpers.bootstrapRequiredImageDependenciesImpl(
            missing=["numpy"],
            sys_executable="pythonX",
            run_fn=_run,
        )


def test_ensure_conversion_runtime_dependencies_impl_requires_cv2_numpy_and_fitz() -> None:
    with pytest.raises(RuntimeError, match="Required image dependencies are missing: cv2, numpy"):
        dependency_helpers.ensureConversionRuntimeDependenciesImpl(
            cv2_module=None,
            np_module=None,
            fitz_module=object(),
        )

    with pytest.raises(RuntimeError, match="Required SVG renderer dependency is missing: fitz"):
        dependency_helpers.ensureConversionRuntimeDependenciesImpl(
            cv2_module=object(),
            np_module=object(),
            fitz_module=None,
        )

    dependency_helpers.ensureConversionRuntimeDependenciesImpl(
        cv2_module=object(),
        np_module=object(),
        fitz_module=object(),
    )
