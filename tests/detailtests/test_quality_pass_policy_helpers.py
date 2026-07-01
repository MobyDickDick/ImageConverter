from __future__ import annotations

from src.iCCModules import imageCompositeConverterQualityPassPolicy as policy_helpers


def test_configured_focused_batch_skips_blanket_quality_retry() -> None:
    max_passes, reason = policy_helpers.resolveMaxQualityPassesImpl(
        default_max_quality_passes=4,
        base_names={"ZZRISK"},
        initial_pass_only_base_names={"ZZRISK"},
    )

    assert max_passes == 0
    assert reason == "focused_initial_pass_only"


def test_regular_single_base_keeps_structured_retry_window() -> None:
    max_passes, reason = policy_helpers.resolveMaxQualityPassesImpl(
        default_max_quality_passes=4,
        base_names={"ZZREGULAR"},
    )

    assert max_passes == 2
    assert reason == "single_base_structured_retry_window"


def test_quality_pass_policy_env_override_wins() -> None:
    max_passes, reason = policy_helpers.resolveMaxQualityPassesImpl(
        default_max_quality_passes=4,
        base_names={"ZZRISK"},
        override_quality_passes="2",
        initial_pass_only_base_names={"ZZRISK"},
    )

    assert max_passes == 2
    assert reason == "env_override"


def test_base_names_from_filenames_uses_converter_base_parser() -> None:
    bases = policy_helpers.baseNamesFromFilenamesImpl(
        ["ZZRISK_L.jpg", "ZZRISK_M.jpg", "ZZBASE_S.jpg"],
        get_base_name_from_file_fn=lambda filename: filename.split("_", 1)[0],
    )

    assert bases == {"ZZRISK", "ZZBASE"}


def test_multi_base_batch_keeps_structured_retry_window_by_default() -> None:
    max_passes, reason = policy_helpers.resolveMaxQualityPassesImpl(
        default_max_quality_passes=4,
        base_names={"ZZBASE", "ZZOTHER"},
    )

    assert max_passes == 2
    assert reason == "multi_base_structured_retry_window"
