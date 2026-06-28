from __future__ import annotations

from src.iCCModules import imageCompositeConverterRemaining as remaining_helpers


def test_exact_same_family_range_does_not_match_shorter_numeric_alias() -> None:
    """AC0100..AC0100 must not also select AC100_* by numeric equality."""

    assert remaining_helpers._inRequestedRange("AC0100_L.jpg", "AC0100", "AC0100")
    assert remaining_helpers._inRequestedRange("AC0100_M.jpg", "AC0100", "AC0100")
    assert remaining_helpers._inRequestedRange("AC0100_S.jpg", "AC0100", "AC0100")
    assert not remaining_helpers._inRequestedRange("AC100_1_M.jpg", "AC0100", "AC0100")
    assert not remaining_helpers._inRequestedRange("AC0100_from_sample.jpg", "AC0100", "AC0100")
