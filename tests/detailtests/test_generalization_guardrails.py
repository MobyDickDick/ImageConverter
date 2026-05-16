from __future__ import annotations

from pathlib import Path


def test_non_composite_runtime_contains_no_image_specific_alias_table() -> None:
    runtime_module = Path("src/iCCModules/imageCompositeConverterNonCompositeRuntime.py")
    content = runtime_module.read_text(encoding="utf-8")
    assert "_PLAN_B_SAMPLE_ALIASES" not in content
