from __future__ import annotations

from src import imageCompositeConverterSemanticValidation as semantic_validation_helpers


def test_expected_semantic_presence_detects_circle_stem_and_text() -> None:
    expected = semantic_validation_helpers.expectedSemanticPresenceImpl(
        [
            "SEMANTIC: Kreis mit senkrechter Strich und Buchstabe",
        ]
    )

    assert expected == {
        "circle": True,
        "stem": True,
        "arm": False,
        "text": True,
    }


def test_semantic_presence_mismatches_reports_missing_and_unexpected_items() -> None:
    mismatches = semantic_validation_helpers.semanticPresenceMismatchesImpl(
        {"circle": True, "stem": False, "arm": True, "text": False},
        {"circle": False, "stem": True, "arm": False, "text": False},
    )

    assert "Beschreibung erwartet Kreis, im Bild aber nicht robust erkennbar" in mismatches
    assert "Beschreibung erwartet waagrechter Strich, im Bild aber nicht robust erkennbar" in mismatches
    assert "Im Bild ist senkrechter Strich erkennbar, aber nicht in der Beschreibung enthalten" in mismatches
