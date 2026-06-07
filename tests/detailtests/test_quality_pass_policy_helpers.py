from __future__ import annotations

from src.iCCModules import imageCompositeConverterQualityPassPolicy as policy_helpers


def test_ac0811_focused_batch_skips_blanket_quality_retry() -> None:
    max_passes, reason = policy_helpers.resolveMaxQualityPassesImpl(
        default_max_quality_passes=4,
        base_names={"AC0811"},
    )

    assert max_passes == 0
    assert reason == "focused_ac0811_initial_pass_only"


def test_non_ac0811_single_base_keeps_one_refinement_pass() -> None:
    max_passes, reason = policy_helpers.resolveMaxQualityPassesImpl(
        default_max_quality_passes=4,
        base_names={"AC0800"},
    )

    assert max_passes == 1
    assert reason == "single_base_one_refinement_pass"


def test_quality_pass_policy_env_override_wins() -> None:
    max_passes, reason = policy_helpers.resolveMaxQualityPassesImpl(
        default_max_quality_passes=4,
        base_names={"AC0811"},
        override_quality_passes="2",
    )

    assert max_passes == 2
    assert reason == "env_override"


def test_base_names_from_filenames_uses_converter_base_parser() -> None:
    bases = policy_helpers.baseNamesFromFilenamesImpl(
        ["AC0811_L.jpg", "AC0811_M.jpg", "AC0800_S.jpg"],
        get_base_name_from_file_fn=lambda filename: filename.split("_", 1)[0],
    )

    assert bases == {"AC0811", "AC0800"}


def test_multi_base_batch_keeps_one_refinement_pass_by_default() -> None:
    max_passes, reason = policy_helpers.resolveMaxQualityPassesImpl(
        default_max_quality_passes=4,
        base_names={"AC0800", "AC0838"},
    )

    assert max_passes == 1
    assert reason == "multi_base_one_refinement_pass"
