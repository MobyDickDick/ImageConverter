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
    initial_pass_only_base_names: set[str] | None = None,
) -> tuple[int, str]:
    """Resolve quality-pass count and explain the selected policy.

    Focused runtime-risk batches may be supplied by the caller as normalized
    base-name metadata. Those batches are deterministic enough after the initial
    pass, while the generic middle/lower-tercile retry can re-queue variants
    without improving the accepted bestlist. Explicit ``ICC_MAX_QUALITY_PASSES``
    still wins.
    """
    max_quality_passes = max(0, int(default_max_quality_passes))
    normalized_bases = {str(base).strip().upper() for base in base_names if str(base).strip()}
    initial_pass_only_bases = {
        str(base).strip().upper()
        for base in (initial_pass_only_base_names or set())
        if str(base).strip()
    }
    reason = "default"

    if len(normalized_bases) == 1:
        only_base = next(iter(normalized_bases))
        if only_base in initial_pass_only_bases:
            max_quality_passes = 0
            reason = "focused_initial_pass_only"
        else:
            max_quality_passes = min(max_quality_passes, 1)
            reason = "single_base_one_refinement_pass"
    elif len(normalized_bases) > 1:
        # A broad batch used to retry the lower two terciles up to four times,
        # multiplying end-to-end runtime even when only marginal gains remained.
        # Keep one targeted refinement pass by default; ICC_MAX_QUALITY_PASSES
        # remains available for deliberate deep-quality runs.
        max_quality_passes = min(max_quality_passes, 1)
        reason = "multi_base_one_refinement_pass"

    override = str(override_quality_passes or "").strip()
    if override:
        try:
            max_quality_passes = max(0, int(override))
            reason = "env_override"
        except ValueError:
            reason = f"{reason}_invalid_env_override_ignored"

    return max_quality_passes, reason
