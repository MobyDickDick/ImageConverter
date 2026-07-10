from __future__ import annotations

from src.iCCModules import imageCompositeConverterRemaining as remaining_helpers


def test_exact_same_family_range_does_not_match_shorter_numeric_alias() -> None:
    """AC0100..AC0100 must not also select AC100_* by numeric equality."""

    assert remaining_helpers._inRequestedRange("AC0100_L.jpg", "AC0100", "AC0100")
    assert remaining_helpers._inRequestedRange("AC0100_M.jpg", "AC0100", "AC0100")
    assert remaining_helpers._inRequestedRange("AC0100_S.jpg", "AC0100", "AC0100")
    assert not remaining_helpers._inRequestedRange("AC100_1_M.jpg", "AC0100", "AC0100")
    assert not remaining_helpers._inRequestedRange("AC0100_from_sample.jpg", "AC0100", "AC0100")


def test_legacy_three_digit_family_filter_selects_padded_family_only() -> None:
    """Bare AC010 is a legacy spelling for AC0010, not for the AC0100 family."""

    assert remaining_helpers._inRequestedRange("AC0010.jpg", "AC010", "AC010")
    assert not remaining_helpers._inRequestedRange("AC0100_L.jpg", "AC010", "AC010")


def test_three_digit_size_variant_filter_selects_concrete_catalog_variant() -> None:
    """AC010_M is a shorthand for AC0100_M and must not collapse to AC0010."""

    assert remaining_helpers._inRequestedRange("AC0100_L.jpg", "AC010_L", "AC010_L")
    assert remaining_helpers._inRequestedRange("AC0100_M.jpg", "AC010_M", "AC010_M")
    assert remaining_helpers._inRequestedRange("AC0100_S.jpg", "AC010_S", "AC010_S")
    assert not remaining_helpers._inRequestedRange("AC0010.jpg", "AC010_M", "AC010_M")
    assert not remaining_helpers._inRequestedRange("AC0010_M.jpg", "AC010_M", "AC010_M")
    assert not remaining_helpers._inRequestedRange("AC0010_S.jpg", "AC010_S", "AC010_S")


def test_two_digit_partial_prefix_filter_selects_ac08_family() -> None:
    """AC08..AC08 is a partial prefix filter for the AC0800..AC0899 family."""

    assert remaining_helpers._inRequestedRange("AC0800_L.jpg", "AC08", "AC08")
    assert remaining_helpers._inRequestedRange("AC0813_M.jpg", "AC08", "AC08")
    assert remaining_helpers._inRequestedRange("AC0899_S.jpg", "AC08", "AC08")
    assert not remaining_helpers._inRequestedRange("AC0080_L.jpg", "AC08", "AC08")
    assert not remaining_helpers._inRequestedRange("AC0538_1L_sia.jpg", "AC08", "AC08")
    assert not remaining_helpers._inRequestedRange("AC0900_L.jpg", "AC08", "AC08")
