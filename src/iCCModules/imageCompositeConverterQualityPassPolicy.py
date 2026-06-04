"""Quality-pass policy helpers for focused conversion batches."""

from __future__ import annotations


def baseNamesFromFilenamesImpl(
    filenames: list[str] | tuple[str, ...],
    *,
    get_base_name_from_file_fn,
) -> set[str]:
    """Return normalized base names for a batch of image filenames."""
    base_names: set[str] = set()
    for filename in filenames:
        base_names.add(str(get_base_name_from_file_fn(str(filename))).strip().upper())
    return {base for base in base_names if base}


def resolveMaxQualityPassesImpl(
    *,
    default_max_quality_passes: int,
    base_names: set[str],
    override_quality_passes: str = "",
) -> tuple[int, str]:
    """Resolve quality-pass count and explain the selected policy.

    AC0811 is a documented runtime-risk batch. Its semantic fit is deterministic
    enough after the initial pass, while the generic middle/lower-tercile retry
    re-queues M/S variants without improving the accepted bestlist. For focused
    AC0811-only batches, skip that blanket retry and keep the command suitable
    as a quick before/after repro. Explicit ``ICC_MAX_QUALITY_PASSES`` still wins.
    """
    max_quality_passes = max(0, int(default_max_quality_passes))
    normalized_bases = {str(base).strip().upper() for base in base_names if str(base).strip()}
    reason = "default"

    if len(normalized_bases) == 1:
        only_base = next(iter(normalized_bases))
        if only_base == "AC0811":
            max_quality_passes = 0
            reason = "focused_ac0811_initial_pass_only"
        else:
            max_quality_passes = min(max_quality_passes, 1)
            reason = "single_base_one_refinement_pass"

    override = str(override_quality_passes or "").strip()
    if override:
        try:
            max_quality_passes = max(0, int(override))
            reason = "env_override"
        except ValueError:
            reason = f"{reason}_invalid_env_override_ignored"

    return max_quality_passes, reason
